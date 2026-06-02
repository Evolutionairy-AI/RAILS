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

## Headline finding

On defective settlements whose only evidence is an agent self-report (below the ATT floor), two frontier LLM judges diverge sharply when used *alone*: one cleared 95% of them, the other cleared 0% but rejected most legitimate work as well. **Under RAILS floor enforcement the clearing decision is identical across both judges** — zero defective settlements clear on inadmissible evidence — while admissibly-evidenced work clears unchanged. The LLM judge's verdict is an ungoverned, model-dependent disposition; the RAILS property is not.

The honest boundary: RAILS cannot catch a defect whose only revealing evidence sits *below* the floor (the at-floor cases), which is the soundness/coverage tradeoff. Lowering the floor trades soundness for coverage — an explicit knob.

## Notes on the specification

Three points were underspecified in the paper and resolved here with documented defaults (see the design spec, §12): the exact Γ survivor-weighting function (`rank(cls) × confidence`), the Λ covering relations, and whether the floor guards all emissions or only those above a loss threshold.

## License

Apache-2.0.
