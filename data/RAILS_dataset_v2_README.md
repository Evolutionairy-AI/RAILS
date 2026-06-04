# RAILS headline dataset v2 — rebuild for the A4 spot-read

This replaces the v1 `curated_cases` set used for the judge-vs-RAILS headline. It is a
drop-in: same families, same counts (180 cases), same `sub_floor` defective set as the
metric surface. What changed is the three things that made v1 indefensible.

## What was wrong with v1, and what v2 does about it

**1. Incoherent bug/fix pairs (the load-bearing problem).** v1 drew the bug and the fix
independently, so most defective reports were nonsense: a double-charge "fixed" with a
cache TTL sweep, an off-by-one "root-caused to an off-by-one." That is not just unrealistic.
It is a *confound*: if defective reports carry a visible bug/fix mismatch and clean ones do
not, a cautious judge can catch defects by spotting the mismatch, which means the cautious
models' 0% false-clear is no longer evidence of "ungoverned guess" — it could be real
detection. That hands the cautious-model camp (Anthropic's own models among them) a clean
rebuttal and quietly breaks the paper's central claim that a bare self-report carries no signal.

In v2 every report draws its fix from a per-bug pool, so the claimed fix always plausibly
addresses the stated bug. The defect is never a textual mismatch. It lives only in ground
truth: the agent confidently claims success, and in the defective cases that claim is simply
false. There is nothing in the prose to catch.

**2. No guarantee the text carried no label signal.** v2 generates clean and defective
reports from the *same* process and the *same* scenario pool. Template, closing, test count,
task and fix are all drawn independently of the label. The strongest version of this: 30 of
the 60 defective scenarios reappear as clean twins (same task, same coherent fix, opposite
ground truth), so for those pairs the report text is the same kind of thing and only the
hidden outcome differs. A judge clearing a defective report is therefore ruling on confidence
and fluency, not on evidence. The generator prints a check confirming length and scenario
balance across labels.

**3. Thin and duplicated.** v1 had eight distinct task strings across sixty cases, with
byte-identical duplicates (case_0000 == case_0003). v2 has 20 distinct components/tasks and
48 distinct (task, fix) scenarios, and **zero** byte-identical prompts anywhere in the 180.
A skeptic can no longer call it eight items resampled.

## Generator output (seed 20260603)

```
total cases: 180   distinct prompts across ALL families: 180/180
  sub_floor   defective= 60  clean= 30
  admissible  defective= 40  clean= 30
  at_floor    defective= 20  clean=  0

headline sub_floor defective: 60 cases
  distinct components/tasks   : 20      (v1 had ~8)
  distinct (task,fix) scenarios: 48
  distinct full prompts        : 60/60
  byte-identical duplicates    : 0      (v1 had identical cases, e.g. 0000==0003)
  prompt length mean: defective 618 vs clean 619  (no length tell)
  clean scenarios that also appear as defective: 30/30  (matched twins)
```

## Family structure (unchanged from v1, so the harness maps directly)

| Family | Cases | Evidence the judge/RAILS sees | What it tests |
|---|---|---|---|
| `sub_floor` | 60 def + 30 clean | SELF only (bare self-report). RAILS returns UNVERIFIABLE. | **The headline.** Judge has only prose; false-clear here is the metric. |
| `admissible` | 40 def + 30 clean | ATT (a CI log). For defects it lists the 2 failing tests; for clean it is green. | Both judge and RAILS panel should catch defects on real evidence. |
| `at_floor` | 20 def | WIT (an informal, unsigned note) that reveals the defect but is below the ATT floor. | RAILS excludes it by construction and misses; a judge reading everything catches it. This is the honest soundness/coverage edge. |

The three families share one ground-truth model. Every scenario carries a concrete
`residual` describing how a defective instance still fails. The CI log (admissible) lists the
two failing tests named for that residual, and the informal note (at_floor) paraphrases it.
So the revealing evidence is coherent with the defect rather than bolted on.

## JSON schema (one object per line in `rails_cases_v2.jsonl`)

```
id                     case_0000
family                 sub_floor | admissible | at_floor
label                  clean | defective
evidence_class         SELF | ATT | WIT          (maps to the Λ class available to RAILS)
component              "payments webhook handler"
task                   the bug to fix
acceptance_criteria    "... and all N tests pass."
test_count             N
scenario_key           tNN_fM   (use to find matched clean/defective twins and to dedupe)
ground_truth           PASS | FAIL               (FAIL == defective)
ground_truth_residual  for defects: how it still fails (not shown in sub_floor prompts)
judge_prompt           the exact string the judge receives
```

`judge_prompt` is what you feed the model. `ground_truth` is the label you score against.
For RAILS, route by `evidence_class`: SELF is below the ATT floor (UNVERIFIABLE), ATT clears
the panel, WIT is excluded by the floor.

## How to regenerate and extend

```
python build_cases_v2.py --seed 20260603 --out rails_cases_v2.jsonl
```

To add scenarios, append to `TASKS`: a component, the bug (`task_text`), a `criteria` noun,
and a list of `fixes`, each with a coherent `rc` (root cause), `fix` (remediation), `residual`
(how a defective instance still fails), and `failing` (two test-name stems for the CI log).
Adding fixes raises the distinct-scenario count directly; 20 more fixes would make all 60
headline defectives unique scenarios.

## Two things to keep honest

- **Still add real anonymized cases.** This is synthetic. It is coherent, diverse, and
  label-balanced, but a reviewer is right that synthetic alone should not carry the headline
  percentages unaided. Mix in a dozen or two real anonymized agent completion reports and
  label them by hand; the generator's schema accepts hand-written rows.
- **Report the distinct-scenario count, not just N.** Base the confidence intervals on
  distinct scenarios (48 here), not the raw 60, so the intervals are honest about the
  effective sample.
