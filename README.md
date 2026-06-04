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
| `data/`, `experiments/`, `figures/` | The v2 dataset, the experiments, figure generators |

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

On defective settlements whose only evidence is an agent self-report (below the ATT floor), the bare LLM judge's verdict is an **ungoverned, model-dependent disposition**. Across a roster of nine judges spanning four providers, the false-clear rate on the *same* inadmissible-evidence cases ranges from 0% (four current models that refuse almost everything) up to ~97% for a current, shipping small model, with a current flagship at ~87% and a prior-generation reference at ~93%; current models populate the whole range, including the middle (~43% and ~30%), not just the safe end. Throughput on legitimate work ranges just as widely: the cautious judges clear only about half of good work (~42–50%), while the permissive ones clear up to ~98%. Caution is not a property of "current models," nor even of a provider: within a single provider's lineup, the small model rubber-stamps ~97% of inadmissible-evidence defectives while the frontier model clears ~43%. Disposition is a per-model accident. No judge occupies the safe-and-high-throughput corner; each sits on a model-dependent tradeoff frontier.

A matched-twin control makes the point sharp. Thirty scenarios appear as both a clean case and a defective one sharing the same task, the same coherent fix, and the same report style, differing only in hidden ground truth. No judge clears the honest twin more often than the deceptive one, and several clear the defective one slightly more. The text below the floor carries no label a judge can act on; a judge that clears it is ruling on fluency, not evidence.

**Under RAILS floor enforcement, soundness on this slice is identical for every judge** — zero defective settlements clear on inadmissible evidence — because it is a proven invariant, not an incidental property of the model. Throughput is then set by policy, not temperament: the exposure-variable floor (`exp_variable_floor.py`) clears low-stakes self-report work while escalating only where the dollars are. The argument is governance: a settlement system cannot rest on "the model happened to be cautious," and RAILS does not.

The honest boundary (kept visible): RAILS cannot catch a defect whose only revealing evidence sits *below* the floor (the at_floor cases), and on that slice a careful judge can catch what RAILS does not. This is the soundness/coverage tradeoff; lowering the floor trades soundness for coverage — an explicit knob.

## Notes on the specification

Three points were underspecified in the paper and resolved here with documented defaults (see the design spec, §12): the exact Γ survivor-weighting function (`rank(cls) × confidence`), the Λ covering relations, and whether the floor guards all emissions or only those above a loss threshold.

## Citing this work

This repository accompanies the RAILS paper:

> *RAILS: A Verification-Native Clearinghouse Protocol for Autonomous Agent Obligations.* Evolutionairy AI / RAILS Initiative. arXiv preprint (identifier to be added on posting).

The arXiv identifier will be added here and to the repository description once the preprint is posted. If you use the harness or the dataset, please cite the paper.

## License

Apache-2.0. The full license text is in [`LICENSE`](LICENSE).
