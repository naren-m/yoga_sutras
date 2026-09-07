"""EXPERIMENT 1: baseline + analysis modes.

Mimics the production adapter's lemma extraction (first parse, all base_words,
lemma or surface_form; dhatu from first base_word that has one) and sweeps the
three AnalysisMode values across both input scripts (dev + iast).
"""
import asyncio
import json
import os
import traceback

from sanskrit_analyzer import Analyzer, Config, AnalysisMode
from score import load_gold, score_run

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
TIMEOUT_S = 30.0

MODES = {
    "PRODUCTION": AnalysisMode.PRODUCTION,
    "EDUCATIONAL": AnalysisMode.EDUCATIONAL,
    "ACADEMIC": AnalysisMode.ACADEMIC,
}


def extract_prediction(result):
    """Replicate sanskrit_adapter.py behaviour.

    - take parse_forest[0]
    - collect all base_words across sandhi_groups
    - lemma = word.lemma or surface_form
    - dhatu from the first base_word that has one
    """
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


async def run_one(analyzer, text, mode):
    try:
        result = await asyncio.wait_for(analyzer.analyze(text, mode=mode), timeout=TIMEOUT_S)
        return extract_prediction(result), None
    except asyncio.TimeoutError:
        return {"lemmas": [], "dhatu": None}, "timeout"
    except Exception as e:  # noqa: BLE001
        return {"lemmas": [], "dhatu": None}, f"{type(e).__name__}: {e}"


async def main():
    gold = load_gold()
    cases = gold["cases"]
    analyzer = Analyzer(Config())

    all_results = {}
    errors = []

    for mode_name, mode in MODES.items():
        for script in ("dev", "iast"):
            run_key = f"{mode_name}__{script}"
            preds = {}
            for case in cases:
                text = case[script]
                pred, err = await run_one(analyzer, text, mode)
                preds[case["id"]] = pred
                if err:
                    errors.append({"run": run_key, "id": case["id"], "input": text, "error": err})
            report = score_run(preds, gold)
            all_results[run_key] = {
                "mode": mode_name,
                "script": script,
                "summary": report["summary"],
                "rows": report["rows"],
                "predictions": {str(k): v for k, v in preds.items()},
            }
            s = report["summary"]
            print(f"{run_key:28s} f1={s['mean_f1']:.3f} exact={s['exact_match_rate']:.3f} "
                  f"dhatu_acc={s['dhatu_accuracy']} (n={s['dhatu_n']})")

    out = {"results": all_results, "errors": errors}
    with open(os.path.join(EVAL_DIR, "exp1_results.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nErrors/timeouts: {len(errors)}")
    return out


if __name__ == "__main__":
    asyncio.run(main())
