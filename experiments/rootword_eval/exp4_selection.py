"""EXPERIMENT 4: parse-selection strategy + new script-routing / entity-key utils.

Compares lemma-extraction strategies against gold on 40 Yoga Sutras cases, for
both Devanagari and IAST inputs. All scoring goes through the shared score.py.

Strategies
----------
A  first-parse (current adapter): parse_forest[0], all base_words, lemma or
   surface_form; dhatu from first base_word that has one.
B  all-parses union: lemmas from every parse in the forest (ACADEMIC mode).
C  best-parse by confidence: pick the highest-confidence parse (AnalysisTree
   .best_parse, else argmax over forest); record whether parse_forest[0] was
   actually the best and whether a non-first parse recovered a gold lemma the
   first parse missed.
D  first-parse + input routed to Devanagari before analyze. Two variants:
     D_route   -- correct routing: detect_script() then transliterate to Devanagari
                  (the script the analyzer segments most reliably).
     D_naive   -- the new script_routing.to_devanagari() auto-router applied
                  verbatim, to expose its IAST-handling behaviour.
   Also probes entity-key folding (canonical_key) on output lemmas.
E  first-parse + confidence/junk-token filtering (candidate recommendation):
   drop pure sandhi artifacts (bare visarga/anusvara, single-char tokens) and
   base_words below a confidence floor.

Everything is scored with score_run() so numbers are comparable across experiments.
"""
import asyncio
import json
import os
import traceback

from sanskrit_analyzer import Analyzer, Config, AnalysisMode
from sanskrit_analyzer.models.scripts import Script
from sanskrit_analyzer.utils.normalize import detect_script
from sanskrit_analyzer.utils.transliterate import transliterate
from sanskrit_analyzer.utils.script_routing import to_devanagari as auto_to_devanagari
from sanskrit_analyzer.utils.entity_keys import canonical_key

from score import load_gold, score_run

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
TIMEOUT_S = 30.0

# Pure sandhi-junk tokens (SLP1): bare visarga / anusvara left as their own word.
_JUNK_SLP1 = {"H", "M", "MH", "HM"}
_CONF_FLOOR = 0.5


# ---------------------------------------------------------------------------
# base_word -> lemma / dhatu helpers
# ---------------------------------------------------------------------------
def bw_lemma(bw):
    return getattr(bw, "lemma", None) or getattr(bw, "surface_form", None)


def bw_dhatu(bw):
    d = getattr(bw, "dhatu", None)
    if d is None:
        return None
    return d if isinstance(d, str) else getattr(d, "dhatu", None)


def is_junk_lemma(lemma):
    if not lemma:
        return True
    s = lemma.strip("-").strip()
    if len(s) <= 1:
        return True
    if s in _JUNK_SLP1:
        return True
    return False


def iter_base_words(parse):
    for sg in getattr(parse, "sandhi_groups", []) or []:
        for bw in getattr(sg, "base_words", []) or []:
            yield bw


def dhatu_from_parse(parse):
    for bw in iter_base_words(parse):
        d = bw_dhatu(bw)
        if d:
            return d
    return None


# ---------------------------------------------------------------------------
# strategies: each takes an AnalysisTree result, returns {"lemmas","dhatu"}
# ---------------------------------------------------------------------------
def strat_A(result):
    lemmas = []
    if result and getattr(result, "parse_forest", None):
        for bw in iter_base_words(result.parse_forest[0]):
            lem = bw_lemma(bw)
            if lem:
                lemmas.append(lem)
        dhatu = dhatu_from_parse(result.parse_forest[0])
    else:
        dhatu = None
    return {"lemmas": lemmas, "dhatu": dhatu}


def strat_B(result):
    lemmas, dhatu = [], None
    if result and getattr(result, "parse_forest", None):
        for parse in result.parse_forest:
            for bw in iter_base_words(parse):
                lem = bw_lemma(bw)
                if lem and lem not in lemmas:
                    lemmas.append(lem)
            if dhatu is None:
                dhatu = dhatu_from_parse(parse)
    return {"lemmas": lemmas, "dhatu": dhatu}


def best_parse_of(result):
    """Return (best_parse, index_in_forest, is_first)."""
    forest = getattr(result, "parse_forest", None) or []
    if not forest:
        return None, -1, True
    bp = getattr(result, "best_parse", None)
    if bp is not None:
        for i, p in enumerate(forest):
            if p is bp:
                return bp, i, (i == 0)
        return bp, -1, False  # best_parse not object-identical to any forest entry
    # fall back to argmax on confidence
    idx = max(range(len(forest)), key=lambda i: getattr(forest[i], "confidence", 0) or 0)
    return forest[idx], idx, (idx == 0)


def strat_C(result):
    bp, _, _ = best_parse_of(result)
    if bp is None:
        return {"lemmas": [], "dhatu": None}
    lemmas = [bw_lemma(bw) for bw in iter_base_words(bp) if bw_lemma(bw)]
    return {"lemmas": lemmas, "dhatu": dhatu_from_parse(bp)}


def strat_E(result):
    """A + confidence floor + junk-token filtering."""
    lemmas, dhatu = [], None
    if result and getattr(result, "parse_forest", None):
        parse = result.parse_forest[0]
        for bw in iter_base_words(parse):
            conf = getattr(bw, "confidence", 1.0)
            if conf is not None and conf < _CONF_FLOOR:
                continue
            lem = bw_lemma(bw)
            if is_junk_lemma(lem):
                continue
            lemmas.append(lem)
        dhatu = dhatu_from_parse(parse)
    return {"lemmas": lemmas, "dhatu": dhatu}


# ---------------------------------------------------------------------------
# input routing (strategy D)
# ---------------------------------------------------------------------------
def route_to_dev_correct(text):
    src = detect_script(text)
    if src == Script.DEVANAGARI:
        return text
    return transliterate(text, src, Script.DEVANAGARI)


# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------
async def analyze(analyzer, text, mode=AnalysisMode.ACADEMIC):
    try:
        result = await asyncio.wait_for(analyzer.analyze(text, mode=mode), timeout=TIMEOUT_S)
        return result, None
    except asyncio.TimeoutError:
        return None, "timeout"
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"


async def main():
    gold = load_gold()
    cases = gold["cases"]
    analyzer = Analyzer(Config())

    errors = []
    all_results = {}

    # diagnostics for the forest / best-parse questions
    forest_lengths = {}         # case_id -> forest length (dev input)
    best_not_first = []         # case_ids where best_parse index != 0
    later_parse_recovers = []   # case_ids where a non-first parse held a gold lemma A missed

    # cache raw analysis results so we analyze each (script,text) once, reuse across strategies
    async def get_result(text):
        r, err = await analyze(analyzer, text)
        return r, err

    # ---- strategies that share the raw (unrouted) analysis ----
    lemma_strats = {"A_first": strat_A, "B_union": strat_B, "C_best": strat_C, "E_filtered": strat_E}

    for script in ("dev", "iast"):
        # analyze every case once
        raw = {}
        for case in cases:
            text = case[script]
            r, err = await get_result(text)
            raw[case["id"]] = r
            if err:
                errors.append({"run": f"raw__{script}", "id": case["id"], "input": text, "error": err})

        # diagnostics only on dev pass
        if script == "dev":
            gold_by_id = {}
            for case in cases:
                accepts = set()
                for slot in case["expected"]:
                    for alt in slot:
                        accepts.add(canonical_slp1(alt))
                gold_by_id[case["id"]] = accepts
            for case in cases:
                r = raw[case["id"]]
                forest = getattr(r, "parse_forest", None) or []
                forest_lengths[case["id"]] = len(forest)
                if not forest:
                    continue
                _, idx, is_first = best_parse_of(r)
                if not is_first:
                    best_not_first.append({"id": case["id"], "best_index": idx})
                # does any non-first parse contribute a gold lemma the first parse missed?
                first_lemmas = {canonical_slp1(bw_lemma(bw)) for bw in iter_base_words(forest[0]) if bw_lemma(bw)}
                gold_set = gold_by_id[case["id"]]
                missed = gold_set - first_lemmas
                if missed and len(forest) > 1:
                    for p in forest[1:]:
                        other = {canonical_slp1(bw_lemma(bw)) for bw in iter_base_words(p) if bw_lemma(bw)}
                        recovered = missed & other
                        if recovered:
                            later_parse_recovers.append({"id": case["id"], "recovered": sorted(recovered)})
                            break

        # score each lemma strategy
        for sname, fn in lemma_strats.items():
            preds = {c["id"]: fn(raw[c["id"]]) for c in cases}
            report = score_run(preds, gold)
            all_results[f"{sname}__{script}"] = {
                "strategy": sname, "script": script,
                "summary": report["summary"],
                "predictions": {str(k): v for k, v in preds.items()},
            }

    # ---- strategy D: routed input (analyze routed text), score with strat_A ----
    for router_name, router in (("D_route", route_to_dev_correct), ("D_naive", auto_to_devanagari)):
        for script in ("dev", "iast"):
            preds = {}
            for case in cases:
                routed = router(case[script])
                r, err = await get_result(routed)
                preds[case["id"]] = strat_A(r)
                if err:
                    errors.append({"run": f"{router_name}__{script}", "id": case["id"],
                                   "input": routed, "error": err})
            report = score_run(preds, gold)
            all_results[f"{router_name}__{script}"] = {
                "strategy": router_name, "script": script,
                "summary": report["summary"],
                "predictions": {str(k): v for k, v in preds.items()},
            }

    # ---- entity-key folding probe: does canonical_key on lemmas help/hurt vs A? ----
    # Apply canonical_key to strat_A lemmas (dev input) and score.
    entity_probe = {}
    for case in cases:
        r = raw_dev = None
    # re-run dev raw quickly reused: recompute from A predictions we stored
    a_dev = all_results["A_first__dev"]["predictions"]
    folded_preds = {}
    for cid, pred in a_dev.items():
        folded_preds[int(cid)] = {
            "lemmas": [canonical_key(l) for l in pred["lemmas"]],
            "dhatu": pred["dhatu"],
        }
    folded_report = score_run(folded_preds, gold)
    all_results["FOLDED_canonical_key__dev"] = {
        "strategy": "canonical_key(lemmas)", "script": "dev",
        "summary": folded_report["summary"],
        "note": "canonical_key applied to SLP1 lemmas (expected to hurt: it assumes IAST/Devanagari input)",
    }

    # dhatu availability diagnostic
    dhatu_defined = [c["id"] for c in cases if c.get("dhatu")]
    dhatu_populated = []
    for c in cases:
        r = None
    # count from A_first dev predictions
    for cid, pred in a_dev.items():
        if pred.get("dhatu"):
            dhatu_populated.append(int(cid))

    out = {
        "results": all_results,
        "diagnostics": {
            "forest_lengths": forest_lengths,
            "max_forest_len": max(forest_lengths.values()) if forest_lengths else 0,
            "n_cases_forest_gt1": sum(1 for v in forest_lengths.values() if v > 1),
            "best_not_first": best_not_first,
            "later_parse_recovers_gold": later_parse_recovers,
            "dhatu_defined_in_gold": dhatu_defined,
            "dhatu_populated_by_analyzer": dhatu_populated,
        },
        "errors": errors,
    }
    with open(os.path.join(EVAL_DIR, "exp4_results.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # console summary table
    print(f"{'run':32s} {'mean_f1':>8s} {'exact':>7s} {'dhatu_acc':>10s} {'dhatu_n':>8s}")
    order = ["A_first", "B_union", "C_best", "E_filtered", "D_route", "D_naive"]
    for sname in order:
        for script in ("dev", "iast"):
            key = f"{sname}__{script}"
            if key in all_results:
                s = all_results[key]["summary"]
                print(f"{key:32s} {s['mean_f1']:8.3f} {s['exact_match_rate']:7.3f} "
                      f"{str(s['dhatu_accuracy']):>10s} {s['dhatu_n']:8d}")
    fk = all_results["FOLDED_canonical_key__dev"]["summary"]
    print(f"{'FOLDED_canonical_key__dev':32s} {fk['mean_f1']:8.3f} {fk['exact_match_rate']:7.3f}")
    print(f"\nmax forest len: {out['diagnostics']['max_forest_len']}, "
          f"cases with forest>1: {out['diagnostics']['n_cases_forest_gt1']}")
    print(f"best_parse != first: {len(best_not_first)} cases -> {best_not_first}")
    print(f"later parse recovers gold: {later_parse_recovers}")
    print(f"dhatu defined in gold: {len(dhatu_defined)}, populated by analyzer: {len(dhatu_populated)} -> {dhatu_populated}")
    print(f"errors/timeouts: {len(errors)}")
    return out


# canonical SLP1 for diagnostics (reuse scorer's normalization)
from score import to_slp1 as canonical_slp1  # noqa: E402


if __name__ == "__main__":
    asyncio.run(main())
