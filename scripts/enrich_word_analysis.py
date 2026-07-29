#!/usr/bin/env python3
"""
Precomputes word-by-word analysis for every TextBlock (sutra).

For each of the 196 sutras this script:
1. Runs the sanskrit_analyzer ensemble on the full Devanagari line
   (sandhi splitting, lemma, morphology, dhatu) via SanskritAdapter.
2. Verifies each proposed dhatu against the real Dhatupatha using the
   sanskrit_model DhatuKosha ("neural proposes, Panini disposes"), and
   attaches the attested meaning (artha) and gana name when confirmed.
3. Stores the result in TextBlock.word_analysis and dumps a cache file
   data/word_analysis.json so reseeding does not require the models.

Run from project root with the backend venv:
    backend/venv/bin/python scripts/enrich_word_analysis.py [--limit N] [--dry-run]

Options:
    --limit N        Only process the first N blocks (for smoke testing)
    --dry-run        Analyze and print, but write nothing
    --byt5           Enable the local ByT5 engine (best segmentation quality,
                     needs torch + model weights; slower first run)
    --slm-path PATH  sanskrit_model checkout for dhatu verification
                     (default: ../sanskrit_model; skipped if missing)
"""
import argparse
import json
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
sys.path.insert(0, BACKEND_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
CACHE_FILE = os.path.join(DATA_DIR, 'word_analysis.json')
DEFAULT_SLM_PATH = os.path.join(os.path.dirname(PROJECT_ROOT), 'sanskrit_model')


def build_adapter(use_byt5: bool):
    """Adapter with explicit engine config: no network engines by default."""
    from sanskrit_analyzer import Config
    from app.services.sanskrit_adapter import SanskritAdapter

    config = Config()
    config.engines.dharmamitra = False   # remote API — not for batch runs
    config.engines.heritage = False      # needs local Heritage server
    config.engines.local_byt5 = use_byt5
    # ByT5 solo beats any ensemble on root-word F1 (0.848 vs 0.401 vidyut
    # baseline; July 2026 eval) — vidyut re-splitting degrades its output.
    config.engines.vidyut = not use_byt5
    # The shared SQLite cache holds results from older engine configs;
    # a batch precompute must reflect THIS config, not stale entries.
    config.cache.sqlite_enabled = False
    config.cache.redis_enabled = False
    return SanskritAdapter(config)


def load_dhatu_kosha(slm_path: str):
    """Load the sanskrit_model Dhatupatha verifier; None if unavailable."""
    if not os.path.isdir(slm_path):
        print(f"  sanskrit_model not found at {slm_path}; skipping dhatu verification")
        return None
    try:
        sys.path.insert(0, slm_path)
        from slm.rules import DhatuKosha
        kosha = DhatuKosha()
        print(f"  Dhatu verifier loaded: {len(kosha.entries)} dhatupatha entries")
        return kosha
    except Exception as e:
        print(f"  Could not load DhatuKosha ({e}); skipping dhatu verification")
        return None


def verify_dhatus(analysis: dict, kosha) -> None:
    """Cross-check analyzer-proposed dhatus against the real Dhatupatha.

    A confirmed root gains dhatu_verified=True plus the attested meaning
    (artha) and gana name; an unattested root is flagged False so the UI
    can de-emphasize it.
    """
    for word in analysis.get('words', []):
        root = word.get('dhatu_slp1')
        if not root:
            continue
        entries = kosha.lookup(root)
        if entries:
            # Prefer the hand-curated dhatus-core.csv rows
            entry = next((e for e in entries if e.get('curated')), entries[0])
            word['dhatu_verified'] = True
            word['dhatu_devanagari'] = entry.get('dhatu_deva') or None
            word['dhatu_meaning'] = entry.get('artha_iast') or None
            word['gana_name'] = entry.get('gana_name') or None
            if word.get('gana') is None and entry.get('gana'):
                try:
                    word['gana'] = int(entry['gana'])
                except ValueError:
                    pass
        else:
            word['dhatu_verified'] = False
    analysis['dhatu_verifier'] = 'sanskrit_model DhatuKosha'


import re

# POS markers that begin the definition body in an MW entry
_MW_POS = re.compile(r'\b(?:mfn|mf\(.{1,4}\)n|m|f|n|ind|cl\.\s*\d)\.\s+')
# Citation tail: ", RV. x, 32" / ", MBh." / page numbers
_MW_CITE = re.compile(r',?\s*(?:[A-ZĀĪŚṚ][A-Za-zĀīāūṛŚś]{0,8}\.|&c|\d).*$')


def short_gloss(value: str) -> str | None:
    """Extract a short English gloss from a raw MW entry value.

    MW rows look like:
      'anuSAsanaanu-SA/sana... n. instruction, direction, command, RV. x, 32...'
    Take the text after the first part-of-speech marker, cut before the
    first citation/reference, and cap the length.
    """
    m = _MW_POS.search(value)
    if not m:
        return None
    body = value[m.end():]
    while re.search(r'\([^()]*\)', body):      # drop (possibly nested) etymology parens
        body = re.sub(r'\([^()]*\)', '', body)
    body = _MW_CITE.sub('', body)
    body = re.sub(r'\s+', ' ', body).replace(' ,', ',')
    body = body.strip(' ,;').lstrip(' .)],;')
    if not body or len(body) < 3:
        return None
    if len(body) > 90:                          # cap at a clause boundary
        body = re.split(r'[;,]', body[:90])
        body = ','.join(body[:-1]) if len(body) > 1 else body[0]
    return body.strip(' ,;')


def apte_gloss(value: str) -> str | None:
    """Extract the first numbered sense from a raw Apte entry.

    Apte rows look like: 'cittacittacitta p. p. [cit-kta] 1 Observed,
    perceived. 2 Considered...'
    """
    m = re.search(r'\b1\s+(\(?[A-Za-z][^.]{2,90})', value)
    if not m:
        return None
    return m.group(1).strip(' ,;')


def attach_meanings(analysis: dict, db) -> None:
    """Fill empty word meanings from the seeded dictionaries.

    Monier-Williams first; entries that are only cross-references
    ('see a-citta') fall through to Apte's numbered senses.
    """
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate
    from app.models.dictionary import DictionaryEntry

    for word in analysis.get('words', []):
        if word.get('meanings'):
            continue
        lemma = word.get('lemma')
        if not lemma:
            continue
        key = transliterate(lemma, sanscript.IAST, sanscript.SLP1)
        rows = (
            db.session.query(DictionaryEntry.value, DictionaryEntry.dictionary_id)
            .filter(DictionaryEntry.key == key)
            .order_by(DictionaryEntry.dictionary_id)
            .limit(10)
            .all()
        )
        for value, dict_id in rows:
            gloss = short_gloss(value) if dict_id == 1 else apte_gloss(value)
            if gloss and 'see ' not in gloss.lower()[:40]:
                word['meanings'] = [gloss]
                word['meaning_source'] = 'mw' if dict_id == 1 else 'apte'
                break


def enrich(limit: int | None, dry_run: bool, use_byt5: bool, slm_path: str) -> bool:
    from app import create_app, db
    from app.models.text import TextBlock

    print("Initializing sanskrit_analyzer...")
    adapter = build_adapter(use_byt5)
    _ = adapter.analyzer  # trigger init up front so failures are loud
    kosha = load_dhatu_kosha(slm_path)

    app = create_app()
    cache: dict[str, dict] = {}
    ok = failed = 0

    with app.app_context():
        blocks = (
            db.session.query(TextBlock)
            .order_by(TextBlock.section_id, TextBlock.order_in_section)
            .all()
        )
        if limit:
            blocks = blocks[:limit]
        print(f"Analyzing {len(blocks)} blocks...")

        start = time.time()
        for i, block in enumerate(blocks, 1):
            content = (block.content or '').strip()
            if not content:
                print(f"  [{block.slug}] no content, skipped")
                continue
            try:
                analysis = adapter.analyze_block_sync(content)
            except Exception as e:
                print(f"  [{block.slug}] FAILED: {e}")
                failed += 1
                continue
            if not analysis:
                print(f"  [{block.slug}] no parse")
                failed += 1
                continue

            if kosha:
                verify_dhatus(analysis, kosha)
            attach_meanings(analysis, db)

            cache[block.slug] = analysis
            if not dry_run:
                block.word_analysis = analysis
            ok += 1

            if i % 20 == 0 or i == len(blocks):
                rate = i / (time.time() - start)
                print(f"  {i}/{len(blocks)} ({rate:.1f} blocks/s)")

        if not dry_run:
            db.session.commit()
            print(f"Committed word_analysis for {ok} blocks")

    if not dry_run:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=1)
        print(f"Cache written: {CACHE_FILE} ({len(cache)} entries)")
    else:
        sample_slug = next(iter(cache), None)
        if sample_slug:
            print(f"\n--- sample ({sample_slug}) ---")
            print(json.dumps(cache[sample_slug], ensure_ascii=False, indent=2))

    print(f"\nDone: {ok} analyzed, {failed} failed")
    return failed == 0 and ok > 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--byt5', action='store_true')
    parser.add_argument('--slm-path', default=DEFAULT_SLM_PATH)
    args = parser.parse_args()

    success = enrich(args.limit, args.dry_run, args.byt5, args.slm_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
