# rails-ref

Reference implementation and adversarial harness for the **RAILS** verification-native clearing protocol — the admissibility-graded Verification Mesh whose soundness property is

> **Emit(S) ⟹ cls(B) ⪰ φ_O** — no financially material settlement is supported by evidence below the obligation's admissibility floor.

This repository lets a third party (a) run the clearing core, (b) reproduce the paper's empirical figures with one command and no API keys, and (c) check conformance to the specification.

## What's here

| Module | Responsibility |
|--------|----------------|
| `rails_ref/admissibility.py` | The Λ admissibility poset (WIT ∥ REC incomparable), `cls(B)` join, floor predicate |
| `rails_ref/objects.py` | The seven RAILS primitives |
| `rails_ref/intake.py` | Intake verifier — the FORGE-UP defense |
| `rails_ref/mesh.py` | The Γ aggregator + floor-enforcement gate (the soundness assertion lives here) |
| `rails_ref/verifiers.py` | Deterministic and naive-fooled verifiers |
| `rails_ref/attacks.py` | FORGE-UP, LAUNDER-BASIS, DOWNGRADE-FLOOR generators |
| `rails_ref/simulate.py` | Synthetic adversarial population + launder-detection study |
| `rails_ref/llm.py`, `config.py` | Cached LLM-judge wrapper; secure key loading + TLS |
| `data/`, `experiments/`, `figures/` | Curated cases, the three experiments, figure generators |

## Reproduce the results (no keys needed)

```bash
pip install -e .
python repro.py
```

This replays the committed LLM-response cache and regenerates `results/*.json` and `figures/out/*.{pdf,png}`. To regenerate the cache against the live APIs, set `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` (or place key files per `rails_ref/config.py`) and run `python -m experiments.exp_headline`.

## Check conformance

```bash
python -m pytest          # full suite, including the spec-conformance tests
```

`tests/test_conformance.py` has one test per empirical claim: the floor invariant at scale, FORGE-UP catch behavior, LAUNDER-BASIS detectability, DOWNGRADE rejection, and the headline divergence.

## Headline finding (governance, not accuracy)

On defective settlements whose only evidence is an agent self-report (below the ATT floor), the bare LLM judge's verdict is an **ungoverned, model-dependent disposition**. Across a roster of current frontier judges spanning four providers, the false-clear rate on the *same* inadmissible-evidence cases ranges from near-zero (cautious current models that have internalised the caution) up to ~95% (a permissive, prior-generation model); throughput on legitimate work ranges just as widely, from 0% (a model that rejects everything) to ~98%. No judge occupies the safe-and-high-throughput corner; each sits on a model-dependent tradeoff frontier.

**Under RAILS floor enforcement, soundness on this slice is identical for every judge** — zero defective settlements clear on inadmissible evidence — because it is a proven invariant, not an incidental property of the model. Throughput is then set by policy, not temperament: the exposure-variable floor (`exp_variable_floor.py`) clears low-stakes self-report work while escalating only where the dollars are. The argument is governance: a settlement system cannot rest on "the model happened to be cautious," and RAILS does not.

The honest boundary (kept visible): RAILS cannot catch a defect whose only revealing evidence sits *below* the floor (the at_floor cases), and on that slice a careful judge can catch what RAILS does not. This is the soundness/coverage tradeoff; lowering the floor trades soundness for coverage — an explicit knob.

## Notes on the specification

Three points were underspecified in the paper and resolved here with documented defaults (see the design spec, §12): the exact Γ survivor-weighting function (`rank(cls) × confidence`), the Λ covering relations, and whether the floor guards all emissions or only those above a loss threshold.

## License

Apache-2.0.
