"""EXPERIMENT 2: DeepRead facility (sanskrit_analyzer.deep_read).

Evaluates the new DeepRead facade on the 40 Yoga Sutras gold cases.

DeepRead.analyze(text, prefer_analyzer=False, use_dharmamitra=True) -> DeepReadResult
  DeepReadResult: input, slp1, engine, tokens[Token], notes
  Token: surface, slp1, resolved, analyses[Analysis], reason, error
  Analysis: kind (verb|derived|nominal|indeclinable|unknown), lemma, dhatu(DhatuBlock), morphology
  DhatuBlock: root, root_dev, gana, gana_num, artha_sa, artha_iast, english

Three engine configs are swept (both dev + iast scripts):
  - local     : use_dharmamitra=False  -> offline vidyut.kosha only (whitespace
                tokenization, NO compound splitting)
  - hybrid    : use_dharmamitra=True   -> Dharmamitra ByT5 network segmenter +
                per-pada kosha enrichment
  - analyzer  : prefer_analyzer=True   -> high-level Analyzer split path

For each DeepReadResult we extract lemmas under three strategies, because
DeepRead over-generates candidate analyses per pada and sorts verb/derived
BEFORE nominal, so the headline reading is often the root-derived lemma, not the
pratipadika the gold expects:
  - headline : analyses[0].lemma per token (realistic "top reading" UI behavior)
  - nominal  : prefer a nominal-kind analysis's lemma per token (pratipadika)
  - union    : all candidate lemmas per token (recall ceiling, low precision)

Dhatu is extracted two ways for diagnostics:
  - dhatu_headline : root of the first analysis (any token) that carries a dhatu
  - dhatu_any      : does the gold dhatu appear in ANY candidate across tokens
                     (oracle upper bound; not fed to the shared scorer)

Per-call latency recorded. Each call runs in a worker thread with a 45s wall
timeout so a network hang cannot kill the run.
"""
import concurrent.futures
import json
import os
import time
import traceback

from sanskrit_analyzer.deep_read import DeepRead
from score import load_gold, score_run, to_slp1

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
TIMEOUT_S = 45.0

CONFIGS = {
    "local":    dict(prefer_analyzer=False, use_dharmamitra=False),
    "hybrid":   dict(prefer_analyzer=False, use_dharmamitra=True),
    "analyzer": dict(prefer_analyzer=True,  use_dharmamitra=True),
}
STRATEGIES = ("headline", "nominal", "union")


def _lemmas_for_token(analyses, strategy):
    if not analyses:
        return []
    if strategy == "headline":
        lem = analyses[0].lemma
        return [lem] if lem else []
    if strategy == "union":
        return [a.lemma for a in analyses if a.lemma]
    if strategy == "nominal":
        pick = next((a for a in analyses if a.kind == "nominal"), None)
        if pick is None:
            pick = next((a for a in analyses if a.kind == "derived"), None)
        if pick is None:
            pick = analyses[0]
        return [pick.lemma] if pick.lemma else []
    raise ValueError(strategy)


def _dhatu_headline(tokens):
    """Root of the first analysis (scanning tokens in order) that has a dhatu."""
    for tok in tokens:
        for a in tok.analyses or []:
            if a.dhatu and a.dhatu.root:
                return a.dhatu.root
    return None


def _dhatu_candidates_slp1(tokens):
    out = set()
    for tok in tokens:
        for a in tok.analyses or []:
            if a.dhatu and a.dhatu.root:
                out.add(to_slp1(a.dhatu.root))
    return out


def extract(res, strategy):
    lemmas = []
    for tok in res.tokens:
        lemmas.extend(_lemmas_for_token(tok.analyses or [], strategy))
    return {"lemmas": lemmas, "dhatu": _dhatu_headline(res.tokens)}


def _call_with_timeout(dr, text, kw, executor):
    """Run DeepRead.analyze in a worker thread with a wall-clock timeout.

    Returns (result_or_None, latency_seconds, error_or_None).
    """
    t0 = time.time()
    fut = executor.submit(dr.analyze, text, **kw)
    try:
        res = fut.result(timeout=TIMEOUT_S)
        return res, time.time() - t0, None
    except concurrent.futures.TimeoutError:
        return None, time.time() - t0, "timeout"
    except Exception as e:  # noqa: BLE001
        return None, time.time() - t0, f"{type(e).__name__}: {e}"


def _median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return None
    m = n // 2
    return s[m] if n % 2 else (s[m - 1] + s[m]) / 2


def main():
    gold = load_gold()
    cases = gold["cases"]
    # gold dhatu (slp1) per case for the dhatu_any diagnostic
    gold_dhatu_slp1 = {c["id"]: to_slp1(c["dhatu"]) for c in cases if c.get("dhatu")}

    dr = DeepRead()
    all_results = {}
    errors = []

    # single-worker executor so calls are serialized but individually timeout-guarded
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        for cfg_name, kw in CONFIGS.items():
            for script in ("dev", "iast"):
                run_key = f"{cfg_name}__{script}"
                latencies = []
                engines = {}
                # cache one DeepReadResult per case, then score each strategy
                per_case = {}   # id -> {"res": DeepReadResult|None, "err":..., "lat":...}
                for case in cases:
                    text = case[script]
                    res, lat, err = _call_with_timeout(dr, text, kw, executor)
                    latencies.append(lat)
                    per_case[case["id"]] = {"res": res, "err": err, "lat": lat}
                    if res is not None:
                        engines[res.engine] = engines.get(res.engine, 0) + 1
                    if err:
                        errors.append({"run": run_key, "id": case["id"],
                                       "input": text, "error": err})

                # dhatu_any diagnostic (oracle upper bound over candidate roots)
                dhatu_any_hit = 0
                dhatu_any_total = 0
                for cid, gd in gold_dhatu_slp1.items():
                    dhatu_any_total += 1
                    res = per_case[cid]["res"]
                    cands = _dhatu_candidates_slp1(res.tokens) if res is not None else set()
                    dhatu_any_hit += int(gd in cands)

                strat_reports = {}
                for strat in STRATEGIES:
                    preds = {}
                    for case in cases:
                        res = per_case[case["id"]]["res"]
                        preds[case["id"]] = (extract(res, strat) if res is not None
                                             else {"lemmas": [], "dhatu": None})
                    rep = score_run(preds, gold)
                    strat_reports[strat] = {
                        "summary": rep["summary"],
                        "rows": rep["rows"],
                        "predictions": {str(k): v for k, v in preds.items()},
                    }
                    s = rep["summary"]
                    print(f"{run_key:16s} {strat:9s} f1={s['mean_f1']:.3f} "
                          f"exact={s['exact_match_rate']:.3f} "
                          f"dhatu_acc={s['dhatu_accuracy']} (n={s['dhatu_n']})")

                mlat = _median(latencies)
                dhatu_any_acc = (round(dhatu_any_hit / dhatu_any_total, 4)
                                 if dhatu_any_total else None)
                print(f"{run_key:16s} {'--':9s} median_lat={mlat:.3f}s "
                      f"max_lat={max(latencies):.3f}s engines={engines} "
                      f"dhatu_any_acc={dhatu_any_acc}")
                all_results[run_key] = {
                    "config": cfg_name,
                    "script": script,
                    "kwargs": kw,
                    "engines": engines,
                    "median_latency_s": round(mlat, 4) if mlat is not None else None,
                    "max_latency_s": round(max(latencies), 4),
                    "mean_latency_s": round(sum(latencies) / len(latencies), 4),
                    "dhatu_any_acc": dhatu_any_acc,
                    "dhatu_any_hit": dhatu_any_hit,
                    "dhatu_any_total": dhatu_any_total,
                    "strategies": strat_reports,
                }

    out = {"experiment": "exp2_deepread", "results": all_results, "errors": errors}
    with open(os.path.join(EVAL_DIR, "exp2_results.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nErrors/timeouts: {len(errors)}")
    return out


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
