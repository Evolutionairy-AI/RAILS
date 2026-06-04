"""Matched-twin label-independence (Adrian's strongest demonstration).

30 of the sub_floor scenarios appear as BOTH a clean and a defective case: same
task, same coherent fix, same report style, opposite hidden ground truth. If the
prose carried any signal about the label, a judge would pass the clean twin more
often than the defective twin. This experiment measures, per model and replaying
ONLY from the committed cache (no API, no keys), the judge-alone PASS rate on the
clean vs the defective members of those matched scenarios. A gap near zero is the
proof: the judge cannot tell them apart, so a clear is a verdict on confidence and
fluency, not on evidence.

Reads the cache populated by exp_headline; writes results/twins.json.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

from rails_ref.dataset import load_cases
from rails_ref.llm import LLMJudge
from experiments.exp_headline import _prompt_a, MODELS, CACHE

RESULTS = Path(__file__).parent.parent / "results"


def _no_api(prompt: str) -> str:  # any cache miss must fail loudly, never call out
    raise RuntimeError("cache miss in twin analysis (run exp_headline first)")


def _pass_rate(judge: LLMJudge, cases) -> tuple[int, int]:
    hits = sum(1 for c in cases if judge.judge(_prompt_a(c))["verdict"] == "PASS")
    return hits, len(cases)


def run_model(provider: str, model: str, by_key: dict) -> dict | None:
    cache_dir = CACHE / f"{provider}_{model}".replace("/", "_")
    judge = LLMJudge(provider, model, cache_dir=cache_dir, _backend=_no_api)
    clean_all, def_all = [], []
    try:
        for cleans, defs in by_key.values():
            clean_all += cleans
            def_all += defs
        ch, cn = _pass_rate(judge, clean_all)
        dh, dn = _pass_rate(judge, def_all)
    except RuntimeError:
        return None  # this model was not run on v2 (no cache)
    return {
        "model": f"{provider}/{model}",
        "twin_scenarios": len(by_key),
        "clean_twin_pass_rate": round(ch / cn, 4),
        "defective_twin_pass_rate": round(dh / dn, 4),
        # gap > 0 would mean the prose leaks the label; ~0 is the no-signal proof
        "discrimination_gap": round(ch / cn - dh / dn, 4),
        "n_clean": cn, "n_defective": dn,
    }


def main() -> None:
    cases = load_cases()
    sub = [c for c in cases if c.deception in ("sub_floor", "sub_floor_clean") and c.scenario_key]
    by_key: dict[str, tuple[list, list]] = defaultdict(lambda: ([], []))
    for c in sub:
        (by_key[c.scenario_key][0] if c.label == "clean" else by_key[c.scenario_key][1]).append(c)
    # keep only scenarios present as BOTH a clean and a defective case (true twins)
    twins = {k: v for k, v in by_key.items() if v[0] and v[1]}

    rows = [r for prov, mod in MODELS if (r := run_model(prov, mod, twins))]
    out = {
        "twin_scenarios": len(twins),
        "note": "clean and defective members share task, coherent fix and report style; "
                "only the hidden ground truth differs. A near-zero discrimination_gap means "
                "the judge passes the two at the same rate -- the text cannot encode the label.",
        "models": rows,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "twins.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"matched twin scenarios: {len(twins)}")
    print(f'{"model":28s} {"clean PASS":>10s} {"defect PASS":>11s} {"gap":>7s}')
    for r in sorted(rows, key=lambda r: r["defective_twin_pass_rate"]):
        print(f'{r["model"]:28s} {r["clean_twin_pass_rate"]:>10.1%} '
              f'{r["defective_twin_pass_rate"]:>11.1%} {r["discrimination_gap"]:>+7.1%}')
    print(f"wrote {RESULTS / 'twins.json'}")


if __name__ == "__main__":
    main()
