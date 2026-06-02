"""Headline experiment (Adrian wishlist item 2).

For each curated case and each judge model, compare two arms on the SAME inputs:

  ARM A  (LLM judge alone): the judge returns PASS/FAIL with no admissibility
          discipline -- today's LLM-as-judge. False-clear = PASS on a defective case.

  ARM B  (RAILS): the judge is one verifier that must declare the admissibility
          class of the basis it relied on; a deterministic verifier panel reads
          the high-admissibility evidence; the floor gate excludes sub-floor
          bases. "Cleared" = emitted with performance PASS AND policy PASS.
          False-clear = a defective case cleared.

The headline contrast is reported overall and on the sub_floor subset (defects
revealed by ATT evidence while a SELF self-report asserts the work is clean) --
the class where floor enforcement is expected to win. at_floor cases (revealed
only by sub-floor WIT evidence) are the honest boundary where RAILS cannot help.

All judge calls are cached, so reruns are free and need no keys.

Usage:
    python -m experiments.exp_headline                 # all models
    python -m experiments.exp_headline openai/gpt-4.1   # one model
"""
from __future__ import annotations
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from pathlib import Path

from rails_ref.admissibility import Class
from rails_ref.objects import ObligationObject, EvidenceEnvelope, VerifierOutput, Verdict
from rails_ref.verifiers import PolicyVerifier
from rails_ref.mesh import clear
from rails_ref.dataset import load_cases
from rails_ref.llm import LLMJudge
from rails_ref.metrics import wilson_ci

ROOT = Path(__file__).parent.parent
CACHE = ROOT / "data" / "llm_cache"
RESULTS = ROOT / "results"

MODELS = [("openai", "gpt-4.1"), ("anthropic", "claude-sonnet-4-6")]

PANEL = [
    PolicyVerifier(watch_kind="pkg_delta", verifier_id="pv_pkg"),
    PolicyVerifier(watch_kind="ci_log", verifier_id="pv_ci"),
    PolicyVerifier(watch_kind="requirements_trace", verifier_id="pv_trace"),
]


def _prompt_a(c) -> str:
    return c.artifact_text + "\n\nRespond on one line: VERDICT: PASS or VERDICT: FAIL."


def _prompt_b(c) -> str:
    classes = "\n".join(f"- {it.kind}: provenance class {it.claimed_class.name}" for it in c.items)
    return (c.artifact_text
            + "\n\nThe evidence items have these admissibility classes:\n" + classes
            + "\n\nRespond on two lines:\nVERDICT: PASS or FAIL\n"
              "BASIS: the single admissibility class (SELF, SIGN, WIT, REC, ATT, or PROOF) "
              "of the evidence you relied on most.")


def _safe_judge(judge: LLMJudge, prompt: str, tries: int = 5) -> dict:
    for attempt in range(tries):
        try:
            return judge.judge(prompt)
        except Exception as e:  # transient API / rate-limit
            if attempt == tries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))


def _cleared(d) -> bool:
    return d.emitted and d.performance == Verdict.PASS and d.policy == Verdict.PASS


def eval_case(judge: LLMJudge, c) -> tuple[bool, bool]:
    # Arm A
    arm_a_pass = _safe_judge(judge, _prompt_a(c))["verdict"] == "PASS"
    # Arm B
    rb = _safe_judge(judge, _prompt_b(c))
    try:
        basis_cls = Class[rb["basis"]] if rb["basis"] else Class.SELF
    except KeyError:
        basis_cls = Class.SELF
    jv = {"PASS": Verdict.PASS, "FAIL": Verdict.FAIL}.get(rb["verdict"], Verdict.ABSTAIN)
    judge_out = VerifierOutput("llm_judge", jv, 0.8, (basis_cls,))
    env = EvidenceEnvelope(c.id, c.items)
    o = ObligationObject(c.id, c.floor, c.task, c.acceptance, ("acme", "provider"))
    outs = [judge_out] + [pv.verify(c.id, env) for pv in PANEL]
    return arm_a_pass, _cleared(clear(o, outs))


def _rate(cases, results, arm, label="defective") -> dict | None:
    subset = [c for c in cases if c.label == label]
    if not subset:
        return None
    hits = sum(1 for c in subset if results[c.id][arm])
    lo, hi = wilson_ci(hits, len(subset))
    # for defective: hits = false-clears; for clean: hits = correct clears (throughput)
    return {"hits": hits, "n": len(subset),
            "rate": round(hits / len(subset), 4), "ci95": [round(lo, 4), round(hi, 4)]}


def run_model(provider: str, model: str, cases, workers: int = 8) -> dict:
    judge = LLMJudge(provider, model, cache_dir=CACHE / f"{provider}_{model}".replace("/", "_"))
    results: dict[str, tuple[bool, bool]] = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(eval_case, judge, c): c for c in cases}
        for fut, c in futs.items():
            results[c.id] = fut.result()
    sub = [c for c in cases if c.deception == "sub_floor"]            # inadmissible-evidence defectives
    adm = [c for c in cases if c.deception == "admissible"]           # ATT-revealed defectives
    atf = [c for c in cases if c.deception == "at_floor"]             # sub-floor-revealed defectives (boundary)
    return {
        "model": f"{provider}/{model}",
        "n_cases": len(cases),
        # false-clear rates on defective work (lower is better)
        "judge_alone_all_defective": _rate(cases, results, 0),
        "rails_all_defective": _rate(cases, results, 1),
        "judge_alone_sub_floor": _rate(sub, results, 0),
        "rails_sub_floor": _rate(sub, results, 1),
        "judge_alone_admissible": _rate(adm, results, 0),
        "rails_admissible": _rate(adm, results, 1),
        "judge_alone_at_floor": _rate(atf, results, 0),
        "rails_at_floor": _rate(atf, results, 1),
        # throughput on clean work (higher is better) — specificity
        "judge_alone_clean_throughput": _rate(cases, results, 0, label="clean"),
        "rails_clean_throughput": _rate(cases, results, 1, label="clean"),
    }


def main(argv: list[str]) -> None:
    cases = load_cases()
    if argv:
        prov, mod = argv[0].split("/", 1)
        models = [(prov, mod)]
    else:
        models = MODELS
    RESULTS.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS / "headline.json"
    existing = json.loads(out_path.read_text()) if out_path.exists() else {"models": []}
    for prov, mod in models:
        print(f"running {prov}/{mod} over {len(cases)} cases ...", flush=True)
        r = run_model(prov, mod, cases)
        existing["models"] = [m for m in existing["models"] if m["model"] != r["model"]] + [r]
        out_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        ja, ra = r["judge_alone_sub_floor"], r["rails_sub_floor"]
        ct = r["rails_clean_throughput"]; jt = r["judge_alone_clean_throughput"]
        print(f"  sub_floor false-clear: judge-alone {ja['rate']:.1%} ({ja['hits']}/{ja['n']})"
              f"  ->  RAILS {ra['rate']:.1%} ({ra['hits']}/{ra['n']})", flush=True)
        print(f"  clean throughput:      judge-alone {jt['rate']:.1%}   RAILS {ct['rate']:.1%}", flush=True)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
