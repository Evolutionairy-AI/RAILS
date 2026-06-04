"""One-command reproduction. Regenerates every results file and figure from the
committed LLM-response cache — no API keys required.

    python repro.py

The headline step replays cached judge responses; to regenerate the cache with
your own keys, set ANTHROPIC_API_KEY / OPENAI_API_KEY and run
`python -m experiments.exp_headline` first.
"""
from __future__ import annotations

from experiments import exp_population, exp_headline, exp_twins, exp_loss, exp_variable_floor
from figures import fig_population, fig_headline, fig_loss, fig_scatter, fig_variable_floor
from rails_ref.simulate import run_population


def main() -> None:
    print("[1/7] population / soundness-at-scale sweeps ...", flush=True)
    exp_population.main()

    print("[2/7] headline experiment (replaying cached judge responses) ...", flush=True)
    exp_headline.main([])

    print("[3/7] matched-twin label-independence (replaying cache) ...", flush=True)
    exp_twins.main()

    print("[4/7] loss / exposure reframe ...", flush=True)
    exp_loss.main()

    print("[5/7] exposure-variable floor (over-declining rebuttal) ...", flush=True)
    exp_variable_floor.main()

    print("[6/7] figures ...", flush=True)
    fig_population.make()
    fig_headline.make()
    fig_scatter.make()
    fig_loss.make()
    fig_variable_floor.make()

    print("[7/7] determinism check ...", flush=True)
    a = run_population(5000, {"forge_up": 0.3, "launder": 0.3, "downgrade": 0.2}, seed=7)
    b = run_population(5000, {"forge_up": 0.3, "launder": 0.3, "downgrade": 0.2}, seed=7)
    assert a.summary() == b.summary(), "non-deterministic population run"
    assert a.floor_violations == 0, "soundness invariant violated"
    print("done. results/ and figures/out/ regenerated; determinism OK.")


if __name__ == "__main__":
    main()
