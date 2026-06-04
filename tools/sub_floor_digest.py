"""Generate a human-readable digest of the sub_floor DEFECTIVE cases for Adrian's
A4 spot-read. These are the 60 cases the headline false-clear rate rests on, so the
digest is written to let a reader judge whether the deceptions are realistic rather
than strawmen. Writes a Markdown file to the RAILS project root.

Run:  python -m tools.sub_floor_digest
"""
from __future__ import annotations
import re
from collections import Counter
from pathlib import Path

from rails_ref.dataset import load_cases

OUT = Path(r"D:\EvolutionAIry\RAILS\RAILS_sub_floor_cases_for_Adrian_2026-06-04.md")


def _self_report(text: str) -> str:
    m = re.search(r'AGENT SELF-REPORT:\s*\n"(.+?)"', text, re.S)
    return " ".join(m.group(1).split()) if m else "(unparsed)"


def main() -> None:
    cases = [c for c in load_cases() if c.deception == "sub_floor" and c.label == "defective"]
    clean = [c for c in load_cases() if c.deception == "sub_floor_clean"]
    tasks = Counter(c.task for c in cases)
    n_scen = len({c.scenario_key for c in cases})
    n_twins = len({c.scenario_key for c in clean} & {c.scenario_key for c in cases})

    L: list[str] = []
    add = L.append

    add(f"# RAILS headline dataset v2 — the {len(cases)} sub_floor defective cases (for Adrian, A4)\n")
    add("_Generated from `reference/data/rails_cases_v2.jsonl` (seed 20260603). This is the exact set "
        "the headline false-clear rate is computed on. v2 rebuilds it to your A4 spec: coherent bug/fix "
        f"pairs, {n_twins} matched clean/defective twins, and {len(tasks)} distinct tasks across "
        f"{n_scen} distinct (task, fix) scenarios._\n")
    add("**Why this matters (governance result).** On this exact set, judge-alone false-clear is "
        "model-dependent: some current models rubber-stamp these confident self-reports while others "
        "refuse them, and RAILS clears 0% for every model (no admissible evidence meets the ATT floor). "
        "The per-model percentages are being **re-measured on this v2 set**; until the nine-model rerun "
        "lands, treat any model numbers as provisional. The point of your read is unchanged: these are "
        "**not** a strawman no current model fails -- current models genuinely clear a material "
        "fraction, which is exactly why a read of their realism is worth your time.\n")

    add("## 1. What one of these cases is, and why it is the right test\n")
    add("A *sub_floor defective* case is a confident, detailed agent **self-report claiming success**, "
        "with **no independent evidence attached** (no CI log, no diff, no third-party attestation). The "
        "agent's claim is, in ground truth, **false** — the work is defective. The judge sees only the "
        "narrative and the acceptance criteria, and is asked PASS/FAIL.\n")
    add("The deception here is deliberately mundane, and that is the point. It is **not** an elaborate lie "
        "with planted fake evidence; it is the ordinary case in agentic settlement — an agent says \"done, "
        "all tests pass, production-ready,\" and nothing independent corroborates it. A material fraction of "
        "such claims are wrong. The class `SELF` (a bare self-report) sits below the obligation's `ATT` floor, "
        "so RAILS has no admissible verifier and returns UNVERIFIABLE; a bare LLM judge has nothing to go on "
        "but the prose.\n")
    add(f"**The key property to evaluate:** the {len(cases)} defective self-reports are textually "
        f"indistinguishable from the {len(clean)} *clean* sub_floor self-reports. They are drawn from the "
        f"same process and the same scenario pool, and {n_twins} of the defective scenarios reappear as "
        "clean twins with the **same coherent fix** and the opposite hidden outcome. So the text cannot "
        "encode the label: a judge that clears a defective one is not being out-smarted, it is rendering a "
        "verdict on confidence and fluency. That is the ungoverned disposition the paper is about.\n")

    add("## 2. The honest weakness to judge (this is what your spot-read is for)\n")
    add("In v2 the bug and the fix are **coherent**: every report draws its fix from a per-bug pool, so the "
        "claimed fix always plausibly addresses the stated bug. The defect is **not** a visible bug/fix "
        "mismatch (that was the v1 confound you flagged); it lives only in ground truth. So there is nothing "
        "in the prose to catch, and a cautious model's refusal cannot be re-read as real mismatch detection.\n")
    add("The remaining honest weakness is that the narratives are still **synthetic**: drawn from a structured "
        "pool of components, coherent root-cause/fix pairs, templates, closings, and test counts (§3), realistic "
        "in *shape* but not captured from production agents. A hostile reviewer can say \"these are templates, "
        "not real agent outputs.\" Per your A4 note we will mix in a dozen or two real anonymized cases before "
        "anything ships (`reference/data/real_cases.jsonl`, same schema). Your call on reading them: **is a "
        "confident self-report with no independent evidence a realistic input a deployed judge would face and "
        "clear, and are these defects real defects?**\n")
    add("This realism is **load-bearing** for the permissive models' false-clear numbers: if a skeptic discounts "
        "the templates, they discount those rates. It does **not** touch the governance argument -- that rests on "
        "the *dispersion* across models (some refuse, some rubber-stamp, not even consistent within one provider), "
        "which holds regardless of how realistic any single case is -- but it does touch the punchy current-model "
        "gap. Hence the read.\n")

    add("## 3. The scenario space (coherent variety behind the set)\n")
    add("Each case draws one component/bug, one **coherent** root-cause/fix, and a test count, then asserts "
        "success. Defective and clean instances come from the same pools, so no surface feature predicts the "
        "label. The actual variety in this set:\n")
    test_counts = sorted({int(m.group(1)) for c in cases
                          for m in [re.search(r"all (\d+) tests", c.acceptance)] if m})
    add(f"- **Distinct tasks:** {len(tasks)} (v1 had ~8).\n")
    add(f"- **Distinct (task, fix) scenarios:** {n_scen} -- the confidence intervals are based on this "
        "effective count, not the raw case count.\n")
    add(f"- **Matched clean twins:** {n_twins} of the defective scenarios reappear as clean cases with the "
        "same coherent fix and the opposite hidden outcome.\n")
    add(f"- **Test counts drawn:** {{{', '.join(str(t) for t in test_counts)}}}, over varied report templates "
        "and closings, so no two prompts in the full 180-case set are byte-identical.\n")

    add("## 4. Five cases in full (exactly what the judge received)\n")
    for c in cases[:5]:
        add(f"### {c.id}  ·  defect: {c.defect_type}\n")
        add("```\n" + c.artifact_text.strip() + "\n```\n")

    add(f"## 5. All {len(cases)} self-reports (skim list)\n")
    add("_Each is a defective claim; the bracket notes the task it claims to have completed._\n")
    for c in cases:
        add(f"- **{c.id}** — \"{_self_report(c.artifact_text)}\"  \n  _claimed task: {c.task}_")
    add("")

    add("## 6. Where the data lives / how to regenerate\n")
    add("- Raw data: `reference/data/rails_cases_v2.jsonl` (one JSON object per line, all 180 cases; the "
        "sub_floor defective block is the first 60). Schema in `reference/data/RAILS_dataset_v2_README.md`.\n")
    add("- Regenerate deterministically: `python data/build_cases_v2.py --seed 20260603`.\n")
    add("- Add real anonymized cases (same schema) to `reference/data/real_cases.jsonl`; they are loaded "
        "automatically alongside the synthetic set.\n")

    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {OUT}  ({len(cases)} defective sub_floor cases, {len(tasks)} distinct tasks)")


if __name__ == "__main__":
    main()
