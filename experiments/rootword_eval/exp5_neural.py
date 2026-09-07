"""EXPERIMENT 5: neural engines (dharmamitra API + local ByT5-Sanskrit).

Findings baked into the run design (discovered during probing):

* dharmamitra_sanskrit_grammar v0.1.7 (installed) is BROKEN against the current
  live API: it POSTs {"input_sentence": ...} but the server now requires
  {"texts": [...]} and returns {"results": [...]}. The old client 422s, so the
  library's DharmamitraEngine returns an empty/error result. We therefore test
  dharmamitra two ways: (C) through the library as-is (documents the breakage),
  and (D) via a corrected direct call to the live endpoint. NB the current public
  /api/tagging/ endpoint does SANDHI SEGMENTATION ONLY and ignores `mode` -- it
  returns underscore-joined split forms, no lemma/morphosyntax.

* local ByT5 (chronbmm/sanskrit5-multitask) works, but LocalByT5Engine._parse_combined
  mishandles the model's compound-member token format `__lemma_U`: it assigns the
  lemma to the `morphology` field and leaves `lemma` empty, so every compound
  member is lost through the Analyzer. We test local_byt5 two ways: (A) through the
  library as-is (production reality) and (B) with a corrected SLM parser (true
  model ceiling).

Extraction convention (library paths A, C, E) matches exp3: Analyzer with only the
target engine, analyze(text, EDUCATIONAL, bypass_cache=True), parse_forest[0],
lemma-or-surface_form for every base_word; dhatu = first base_word with one.
"""
import asyncio
import json
import os
import time
import traceback

from sanskrit_analyzer import Analyzer, Config, AnalysisMode
from score import load_gold, score_run

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
FIRST_TIMEOUT = 120.0
STEADY_TIMEOUT = 30.0
VIDYUT_BASELINE_F1 = 0.401

DM_API = "https://dharmamitra.org/api/tagging/"
DM_HEADERS = {
    "Authorization": "Basic b2xkc3R1ZGVudDpiZWhhcHB5",
    "Content-Type": "application/json",
    "Origin": "https://dharmamitra.org",
    "User-Agent": "Mozilla/5.0",
}
_VERB_MARKERS = ("Pr", "Aor", "Fut", "Impf", "Perf", "Imp", "Opt", "Cond")


# ---------------------------------------------------------------------------
# library-path helpers (shared with exp3)
# ---------------------------------------------------------------------------
# Engines sanskrit_analyzer still defines. Dharmamitra and Heritage were both
# deleted upstream; Config.engines is a plain dataclass, so assigning their old
# names silently created dead attributes and every "dharmamitra" run below was
# really scoring an unmodified default Analyzer.
LIBRARY_ENGINES = ("vidyut", "local_byt5")


def make_config(target):
    """Enable exactly ``target``. Raises if the engine no longer exists."""
    if target not in LIBRARY_ENGINES:
        raise ValueError(
            f"{target!r} is not a library engine; have {list(LIBRARY_ENGINES)}. "
            "Dharmamitra is reachable only via the direct API path below."
        )
    cfg = Config()
    for engine in LIBRARY_ENGINES:
        if not hasattr(cfg.engines, engine):
            raise AttributeError(
                f"Config.engines has no {engine!r}; update LIBRARY_ENGINES."
            )
        setattr(cfg.engines, engine, engine == target)
    return cfg


def iter_base_words(parse):
    for sg in getattr(parse, "sandhi_groups", []) or []:
        for bw in getattr(sg, "base_words", []) or []:
            yield bw


def bw_dhatu(bw):
    d = getattr(bw, "dhatu", None)
    if d is None:
        return None
    return d if isinstance(d, str) else getattr(d, "dhatu", None)


def extract_prediction(result):
    lemmas, dhatu = [], None
    if not result or not getattr(result, "parse_forest", None):
        return {"lemmas": lemmas, "dhatu": dhatu}
    for bw in iter_base_words(result.parse_forest[0]):
        lem = getattr(bw, "lemma", None) or getattr(bw, "surface_form", None)
        if lem:
            lemmas.append(lem)
        if dhatu is None:
            d = bw_dhatu(bw)
            if d:
                dhatu = d
    return {"lemmas": lemmas, "dhatu": dhatu}


async def timed_analyze(analyzer, text, timeout):
    t0 = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            analyzer.analyze(text, mode=AnalysisMode.EDUCATIONAL, bypass_cache=True),
            timeout=timeout,
        )
        return extract_prediction(result), time.perf_counter() - t0, None
    except asyncio.TimeoutError:
        return {"lemmas": [], "dhatu": None}, time.perf_counter() - t0, "timeout"
    except Exception as e:  # noqa: BLE001
        return {"lemmas": [], "dhatu": None}, time.perf_counter() - t0, f"{type(e).__name__}: {e}"


async def run_library(target, cases, errors, script="dev"):
    t0 = time.perf_counter()
    analyzer = Analyzer(make_config(target))
    ctor_s = time.perf_counter() - t0
    preds, lat = {}, {}
    for i, case in enumerate(cases):
        pred, dt, err = await timed_analyze(
            analyzer, case[script], FIRST_TIMEOUT if i == 0 else STEADY_TIMEOUT
        )
        preds[case["id"]] = pred
        lat[case["id"]] = dt
        if err:
            errors.append({"config": f"lib:{target}", "script": script,
                           "id": case["id"], "input": case[script], "error": err})
    return preds, lat, ctor_s


# ---------------------------------------------------------------------------
# corrected local ByT5 SLM parser (path B)
# ---------------------------------------------------------------------------
def parse_slm(output):
    """Correctly extract (lemmas, tags) from a ByT5 SLM output string.

    Standard token:        surface_lemma_TAG   -> lemma = field[1]
    Compound-member token: __lemma_U           -> lemma = field[2]
    """
    lemmas, tags = [], []
    for tok in output.strip().split():
        parts = tok.split("_")
        if len(parts) >= 3 and parts[0] == "" and parts[1] == "":
            lemma, tag = parts[2], (parts[3] if len(parts) > 3 else "")
        elif len(parts) >= 2:
            lemma, tag = (parts[1] or parts[0]), (parts[2] if len(parts) > 2 else "")
        elif parts:
            lemma, tag = parts[0], ""
        else:
            continue
        if lemma:
            lemmas.append(lemma)
            tags.append(tag)
    return lemmas, tags


def slm_dhatu(lemmas, tags):
    """Best-effort dhatu: lemma of the first finite-verb-tagged token."""
    for lem, tag in zip(lemmas, tags):
        if tag and (tag[0] == "V" or any(m in tag for m in _VERB_MARKERS)):
            return lem
    return None


# ---------------------------------------------------------------------------
# dharmamitra direct live call (path D) -- segmentation only
# ---------------------------------------------------------------------------
def dm_segment(iast_text, session):
    """Return (lemmas, latency, error). Split forms from the live tagging API."""
    import requests  # noqa
    t0 = time.perf_counter()
    try:
        r = session.post(DM_API, headers=DM_HEADERS, timeout=60, json={
            "texts": [iast_text],
            "mode": "unsandhied-lemma-morphosyntax",
            "input_encoding": "auto",
            "human_readable_tags": True,
        })
        r.raise_for_status()
        results = r.json().get("results", [])
        dt = time.perf_counter() - t0
        if not results:
            return [], dt, "empty results"
        forms = [w for w in results[0].split("_") if w.strip()]
        return forms, dt, None
    except Exception as e:  # noqa: BLE001
        return [], time.perf_counter() - t0, f"{type(e).__name__}: {e}"


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def summarize_latency(ctor_s, lat_by_id):
    vals = list(lat_by_id.values())
    return {
        "ctor_or_first_load_seconds": round(ctor_s, 3),
        "first_call_seconds": round(vals[0], 3) if vals else None,
        "steady_median_seconds": round(median(vals[1:]) or 0, 3),
        "steady_max_seconds": round(max(vals[1:]) if len(vals) > 1 else 0, 3),
    }


async def main():
    import requests
    gold = load_gold()
    cases = gold["cases"]
    errors = []
    out = {"vidyut_baseline_f1": VIDYUT_BASELINE_F1, "results": {}, "notes": {}, "errors": errors}

    def record(key, preds, script, extra=None):
        rep = score_run(preds, gold)
        s = rep["summary"]
        entry = {"script": script, "summary": s, "rows": rep["rows"],
                 "predictions": {str(k): v for k, v in preds.items()}}
        if extra:
            entry.update(extra)
        out["results"][key] = entry
        print(f"  {key:26s} f1={s['mean_f1']:.3f} exact={s['exact_match_rate']:.3f} "
              f"dhatu_acc={s['dhatu_accuracy']} (n={s['dhatu_n']})")
        return s

    # ---- E. vidyut baseline reproduction (also supplies lemmas for ensembles) ----
    print("== vidyut baseline (library) ==")
    vidyut_preds, vlat, vctor = await run_library("vidyut", cases, errors, "dev")
    record("vidyut__dev", vidyut_preds, "dev", {"latency": summarize_latency(vctor, vlat)})

    # ---- A. local_byt5 through the library, as-is (buggy parser) ----
    print("\n== local_byt5 (library, as-is) ==")
    try:
        b_lib_preds, blat, bctor = await run_library("local_byt5", cases, errors, "dev")
        record("local_byt5_lib__dev", b_lib_preds, "dev",
               {"latency": summarize_latency(bctor, blat),
                "note": "library path; _parse_combined drops compound-member lemmas"})
    except Exception as e:  # noqa: BLE001
        out["results"]["local_byt5_lib__dev"] = {"error": f"{type(e).__name__}: {e}"}
        print(f"  local_byt5 library run failed: {e}")

    # ---- B. local_byt5 corrected SLM parse (true model ceiling), dev + iast ----
    print("\n== local_byt5 (corrected SLM parse) ==")
    byt5_corr_dev = {}
    seg_dump = {}
    try:
        import warnings
        warnings.filterwarnings("ignore")
        from sanskrit_analyzer.engines.local_byt5_engine import LocalByT5Engine
        t0 = time.perf_counter()
        eng = LocalByT5Engine()
        load_s = time.perf_counter() - t0
        out["notes"]["local_byt5_load_seconds"] = round(load_s, 3)
        out["notes"]["local_byt5_device"] = getattr(eng, "_device", None)
        for script in ("dev", "iast"):
            preds, lat = {}, {}
            for i, case in enumerate(cases):
                t = time.perf_counter()
                try:
                    raw = eng._generate(case[script], eng.TASK_COMBINED)
                    lemmas, tags = parse_slm(raw)
                    dhatu = slm_dhatu(lemmas, tags)
                    if script == "dev":
                        seg_dump[case["id"]] = {"raw": raw, "lemmas": lemmas, "tags": tags}
                except Exception as e:  # noqa: BLE001
                    lemmas, dhatu = [], None
                    errors.append({"config": "byt5_corrected", "script": script,
                                   "id": case["id"], "error": f"{type(e).__name__}: {e}"})
                lat[case["id"]] = time.perf_counter() - t
                preds[case["id"]] = {"lemmas": lemmas, "dhatu": dhatu}
            extra = {"latency": summarize_latency(load_s, lat)} if script == "dev" else {}
            s = record(f"byt5_corrected__{script}", preds, script, extra)
            if script == "dev":
                byt5_corr_dev = preds
        out["notes"]["byt5_any_morph_tag"] = any(
            any(v["tags"]) for v in seg_dump.values()
        )
        out["notes"]["byt5_segment_dump"] = seg_dump
    except Exception as e:  # noqa: BLE001
        out["results"]["byt5_corrected__dev"] = {"error": f"{type(e).__name__}: {e}"}
        print(f"  local_byt5 corrected run failed: {e}")
        traceback.print_exc()

    # ---- C. dharmamitra through the library: no longer possible ----
    # The engine was deleted from sanskrit_analyzer, so there is no library path
    # left to measure. Recorded explicitly rather than silently scoring a default
    # Analyzer under a "dharmamitra" label, which is what this block used to do.
    print("\n== dharmamitra (library) == skipped: engine removed upstream")
    out["results"]["dharmamitra_lib__dev"] = {
        "skipped": "sanskrit_analyzer.engines.dharmamitra_engine was removed; "
                   "use the direct API path (D) below"
    }

    # ---- D. dharmamitra via corrected live API (segmentation-only) ----
    print("\n== dharmamitra (corrected live API, segmentation) ==")
    dm_seg_dev = {}
    try:
        session = requests.Session()
        preds, lat, seg_raw = {}, {}, {}
        for i, case in enumerate(cases):
            forms, dt, err = dm_segment(case["iast"], session)  # API wants romanized
            preds[case["id"]] = {"lemmas": forms, "dhatu": None}
            lat[case["id"]] = dt
            seg_raw[case["id"]] = forms
            if err:
                errors.append({"config": "dm_seg", "id": case["id"], "error": err})
        record("dharmamitra_seg__iast", preds, "iast",
               {"latency": summarize_latency(0.0, lat),
                "note": "live /api/tagging/ split forms as lemmas (segmentation only)",
                "seg_dump": seg_raw})
        dm_seg_dev = preds
    except Exception as e:  # noqa: BLE001
        out["results"]["dharmamitra_seg__iast"] = {"error": f"{type(e).__name__}: {e}"}
        print(f"  dharmamitra direct API run failed: {e}")

    # ---- F/G. union ensembles: vidyut ∪ neural (ceiling of combining) ----
    print("\n== union ensembles ==")
    def union(a, b):
        preds = {}
        for cid in a:
            seen, lemmas = set(), []
            for src in (a.get(cid, {}), b.get(cid, {})):
                for lem in src.get("lemmas", []) or []:
                    if lem not in seen:
                        seen.add(lem)
                        lemmas.append(lem)
            dhatu = a.get(cid, {}).get("dhatu") or b.get(cid, {}).get("dhatu")
            preds[cid] = {"lemmas": lemmas, "dhatu": dhatu}
        return preds

    if byt5_corr_dev:
        record("union_vidyut+byt5corr__dev", union(vidyut_preds, byt5_corr_dev), "dev",
               {"note": "per-case lemma union; ceiling if byt5 parser were fixed"})
    if dm_seg_dev:
        # dm_seg used iast input but lemmas are script-normalized by scorer; union with vidyut dev
        record("union_vidyut+dmseg__dev", union(vidyut_preds, dm_seg_dev), "dev",
               {"note": "vidyut lemmas ∪ dharmamitra split forms"})

    with open(os.path.join(EVAL_DIR, "exp5_results.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nErrors/timeouts: {len(errors)}")
    return out


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
        raise
