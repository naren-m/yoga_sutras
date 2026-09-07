"""EXPERIMENT 3: engine ablation.

Scores root-word identification for each engine in isolation vs both engines
enabled together, plus an ORACLE union (upper bound on engine combination).

Engines are toggled via Config().engines.{vidyut,local_byt5} bool flags; one
fresh Analyzer per config. Availability is probed once per engine by
instantiating it directly and running a single analyze() with a timeout;
unreachable / unusable engines are recorded and skipped for the full run.

Extraction convention matches exp1: parse_forest[0], collect lemma (or
surface_form) for every base_word across all sandhi_groups; dhatu = first
base_word that has one. mode=EDUCATIONAL, bypass_cache=True (so a shared on-disk
cache can never leak one engine's answer into another config).
"""
import asyncio
import json
import os
import traceback

from sanskrit_analyzer import Analyzer, Config, AnalysisMode
from score import load_gold, score_run

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
TIMEOUT_S = 30.0
PROBE_WORD = "योगः"

# config name -> dict of engine bool flags to set on Config().engines
#
# sanskrit_analyzer used to weight-vote across vidyut, dharmamitra and heritage.
# Dharmamitra and Heritage are both gone and the vote collapsed into
# EngineRunner, which is priority-ordered: the first engine returning segments
# wins. So "runner" is not an ensemble — it measures fallback order, not voting.
CONFIGS = {
    "vidyut":     {"vidyut": True,  "local_byt5": False},
    "local_byt5": {"vidyut": False, "local_byt5": True},
    "runner":     {"vidyut": True,  "local_byt5": True},
}
SINGLE_ENGINE_CONFIGS = ["vidyut", "local_byt5"]


def extract_prediction(result):
    """Replicate exp1 / production adapter lemma extraction."""
    lemmas = []
    dhatu = None
    if not result or not getattr(result, "parse_forest", None):
        return {"lemmas": lemmas, "dhatu": dhatu}
    parse = result.parse_forest[0]
    for sg in getattr(parse, "sandhi_groups", []) or []:
        for bw in getattr(sg, "base_words", []) or []:
            lemma = getattr(bw, "lemma", None) or getattr(bw, "surface_form", None)
            if lemma:
                lemmas.append(lemma)
            if dhatu is None:
                d = getattr(bw, "dhatu", None)
                if d is not None:
                    dval = getattr(d, "dhatu", None) if not isinstance(d, str) else d
                    if dval:
                        dhatu = dval
    return {"lemmas": lemmas, "dhatu": dhatu}


def make_config(flags):
    """Build a Config with exactly the requested engines enabled.

    ``Config.engines`` is a plain dataclass, so assigning an engine name it does
    not define silently creates a dead attribute instead of raising — which is
    how the dharmamitra and heritage configs went on "running" long after both
    engines were deleted upstream, scoring an unchanged default Analyzer. Fail
    loudly so the next engine removal shows up as an error, not a silent no-op.
    """
    cfg = Config()
    for engine, enabled in flags.items():
        if not hasattr(cfg.engines, engine):
            raise AttributeError(
                f"Config.engines has no {engine!r} — the engine was probably "
                f"removed from sanskrit_analyzer. Update CONFIGS."
            )
        setattr(cfg.engines, engine, enabled)
    return cfg


async def probe_engine(name):
    """Instantiate one engine directly and run a single analyze() probe.

    Returns (available: bool, detail: str).
    """
    try:
        if name == "vidyut":
            from sanskrit_analyzer.engines.vidyut_engine import VidyutEngine
            eng = VidyutEngine()
        elif name == "local_byt5":
            from sanskrit_analyzer.engines.local_byt5_engine import LocalByT5Engine
            eng = LocalByT5Engine()
        else:
            return False, "unknown engine"
    except Exception as e:  # noqa: BLE001
        return False, f"init failed: {type(e).__name__}: {e}"

    if not getattr(eng, "is_available", False):
        detail = getattr(eng, "_init_error", None) or "is_available=False"
        return False, str(detail)

    try:
        res = await asyncio.wait_for(eng.analyze(PROBE_WORD), timeout=TIMEOUT_S)
    except asyncio.TimeoutError:
        return False, "probe timeout"
    except Exception as e:  # noqa: BLE001
        return False, f"probe error: {type(e).__name__}: {e}"

    if getattr(res, "error", None):
        return False, f"probe returned error: {res.error}"
    if not getattr(res, "segments", None):
        return False, "probe returned no segments"
    return True, f"probe ok: {len(res.segments)} segment(s)"


async def run_one(analyzer, text):
    try:
        result = await asyncio.wait_for(
            analyzer.analyze(text, mode=AnalysisMode.EDUCATIONAL, bypass_cache=True),
            timeout=TIMEOUT_S,
        )
        return extract_prediction(result), None
    except asyncio.TimeoutError:
        return {"lemmas": [], "dhatu": None}, "timeout"
    except Exception as e:  # noqa: BLE001
        return {"lemmas": [], "dhatu": None}, f"{type(e).__name__}: {e}"


async def run_config(name, flags, cases, script, errors):
    analyzer = Analyzer(make_config(flags))
    preds = {}
    for case in cases:
        text = case[script]
        pred, err = await run_one(analyzer, text)
        preds[case["id"]] = pred
        if err:
            errors.append({"config": name, "script": script, "id": case["id"],
                           "input": text, "error": err})
    return preds


async def main():
    gold = load_gold()
    cases = gold["cases"]
    errors = []

    # 1. Probe availability of every engine (one call each).
    availability = {}
    print("== Engine availability probes ==")
    for name in SINGLE_ENGINE_CONFIGS:
        ok, detail = await probe_engine(name)
        availability[name] = {"available": ok, "detail": detail}
        print(f"  {name:12s} available={ok!s:5s} {detail}")
    # The runner is usable if any member engine is available.
    availability["runner"] = {
        "available": any(availability[m]["available"] for m in SINGLE_ENGINE_CONFIGS),
        "detail": "members available: " + ", ".join(
            m for m in SINGLE_ENGINE_CONFIGS if availability[m]["available"]) or "none",
    }

    # 2. Run each config (Devanagari) whose engine(s) are available.
    all_results = {}
    single_preds = {}  # config -> {case_id: pred}  (for oracle union)
    print("\n== Config runs (devanagari) ==")
    for name, flags in CONFIGS.items():
        if not availability[name]["available"]:
            print(f"  {name:12s} SKIPPED (unavailable)")
            all_results[name] = {"skipped": True, "availability": availability[name]}
            continue
        preds = await run_config(name, flags, cases, "dev", errors)
        report = score_run(preds, gold)
        s = report["summary"]
        all_results[name] = {
            "script": "dev",
            "availability": availability[name],
            "summary": s,
            "rows": report["rows"],
            "predictions": {str(k): v for k, v in preds.items()},
        }
        if name in SINGLE_ENGINE_CONFIGS:
            single_preds[name] = preds
        print(f"  {name:12s} f1={s['mean_f1']:.3f} exact={s['exact_match_rate']:.3f} "
              f"dhatu_acc={s['dhatu_accuracy']} (n={s['dhatu_n']})")

    # 3. ORACLE union: per case, union of lemmas from all available single engines.
    oracle_report = None
    if single_preds:
        oracle_preds = {}
        for case in cases:
            cid = case["id"]
            union = []
            seen = set()
            dhatu = None
            for cfg_name in SINGLE_ENGINE_CONFIGS:
                p = single_preds.get(cfg_name, {}).get(cid)
                if not p:
                    continue
                for lem in p.get("lemmas", []):
                    if lem not in seen:
                        seen.add(lem)
                        union.append(lem)
                if dhatu is None and p.get("dhatu"):
                    dhatu = p["dhatu"]
            oracle_preds[cid] = {"lemmas": union, "dhatu": dhatu}
        oracle_report = score_run(oracle_preds, gold)
        os_ = oracle_report["summary"]
        all_results["ORACLE_union"] = {
            "note": "per-case union of lemmas from all available single-engine runs (dev)",
            "engines_unioned": list(single_preds.keys()),
            "summary": os_,
            "rows": oracle_report["rows"],
            "predictions": {str(k): v for k, v in oracle_preds.items()},
        }
        print(f"\n  {'ORACLE_union':12s} f1={os_['mean_f1']:.3f} "
              f"exact={os_['exact_match_rate']:.3f} "
              f"dhatu_acc={os_['dhatu_accuracy']} (n={os_['dhatu_n']}) "
              f"[union of {list(single_preds.keys())}]")

    # 4. Best available config -> also run IAST input.
    scored = {n: r for n, r in all_results.items()
              if isinstance(r, dict) and "summary" in r and n != "ORACLE_union"}
    best_name = None
    if scored:
        best_name = max(scored, key=lambda n: scored[n]["summary"]["mean_f1"])
        preds_iast = await run_config(best_name, CONFIGS[best_name], cases, "iast", errors)
        report_iast = score_run(preds_iast, gold)
        s = report_iast["summary"]
        all_results[f"{best_name}__iast"] = {
            "script": "iast",
            "note": f"best config ({best_name}) re-run on IAST input",
            "summary": s,
            "rows": report_iast["rows"],
            "predictions": {str(k): v for k, v in preds_iast.items()},
        }
        print(f"\n  {best_name}__iast  f1={s['mean_f1']:.3f} exact={s['exact_match_rate']:.3f} "
              f"dhatu_acc={s['dhatu_accuracy']} (n={s['dhatu_n']})")

    out = {
        "availability": availability,
        "best_config_dev": best_name,
        "results": all_results,
        "errors": errors,
    }
    with open(os.path.join(EVAL_DIR, "exp3_results.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nErrors/timeouts: {len(errors)}")
    return out


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
        raise
