"""Interoperability demo (paper Sec 8.6 worked scenario + Sec 9.3 interop passage).

The exact scenario from the paper: under a Mastercard Verifiable Intent (VI)
credential, an agent is mandated to buy a 100W USB-C charger. Authorization and
payment are clean -- the VI credential is valid and the charge settles -- but the
agent procures a 65W charger. The defect is a PERFORMANCE failure (the delivered
item does not meet the mandated specification), not an authorization or payment
fraud, which is precisely the failure mode the dispute regime does not catch.

RAILS sits BETWEEN the network and settlement as a neutral layer: it consumes the
network artifacts as evidence (the VI credential as authority, the fulfillment
record as the performance attestation), runs the clearing core, and hands a
Settlement Instruction back to the network's rail. Authorization clears; the
wattage mismatch makes the clearing determination a performance failure, so the
instruction routes the payment to resolution instead of releasing it to the
merchant. RAILS does not replace the rail or the customer relationship; it
produces the clearing determination the rail needs.

No API calls. Run:  python -m experiments.interop_demo
"""
from __future__ import annotations

from rails_ref.admissibility import Class
from rails_ref.objects import (
    ObligationObject, EvidenceEnvelope, EvidenceItem, VerifierOutput, Verdict,
)
from rails_ref.verifiers import PolicyVerifier
from rails_ref.mesh import clear

MANDATED_W = 100
DELIVERED_W = 65


def charger_obligation() -> ObligationObject:
    return ObligationObject(
        id="vi-mandate-65W-vs-100W",
        floor=Class.ATT,                                  # material purchase
        task=f"agentic checkout: buy a {MANDATED_W}W USB-C charger under the user's verifiable intent",
        acceptance=f"delivered item meets the mandated {MANDATED_W}W specification",
        parties=("buyer", "merchant"),
        loss_if_bad=float(200),
    )


def network_artifacts_to_evidence() -> list[EvidenceItem]:
    """Map the network's artifacts onto Lambda.

    - Mastercard VI credential: a network-signed credential binding issuer + user
      authorization + payment mandate. As authority evidence it is a trusted
      attestation -> ATT. It does NOT reveal the defect (authorization is clean).
    - Fulfillment record: the merchant/rail-edge attestation of what was actually
      procured (a 65W charger) -> ATT. This reveals the performance defect: the
      delivered wattage does not meet the mandated 100W.
    - Agent self-report ("purchase complete") -> SELF; asserts success, reveals
      nothing.
    """
    return [
        EvidenceItem("verifiable_intent_credential", Class.ATT, Class.ATT,
                     reveals_defect=False, payload_ref="VI: authorized + paid, clean"),
        EvidenceItem("fulfillment_record", Class.ATT, Class.ATT,
                     reveals_defect=True, payload_ref=f"delivered {DELIVERED_W}W != mandated {MANDATED_W}W"),
        EvidenceItem("agent_self_report", Class.SELF, Class.SELF,
                     reveals_defect=False, payload_ref="self-report: purchase complete"),
    ]


def settlement_instruction(decision) -> dict:
    """Translate a Clearing Decision into a rail-executable instruction. A clean
    clearing settles to the merchant; a verifiable performance failure is held and
    routed to resolution rather than released."""
    clean = decision.performance == Verdict.PASS and decision.policy == Verdict.PASS
    return {
        "instruction_id": "0x7E29...3C4F",
        "decision_ref": decision.obligation_id,
        "action": "settle_to_merchant" if clean else "hold_and_route_to_resolution",
        "performance": decision.performance.value,
        "basis_class": decision.cls_basis.name,
        "finality": decision.finality.value,
        "execution_rail": "network_rail::settle",
    }


def run_scenario():
    """Return (obligation, items, authorization-clean flag, performance output,
    decision, settlement_instruction) for the scenario.

    Authorization is a clean precondition read off the VI credential (it does not
    reveal a defect). The obligation-performance determination is rendered by the
    fulfillment verifier, which reads the (ATT) fulfillment record and FAILs on the
    65W-vs-100W mismatch. RAILS issues ONE clearing determination on the obligation
    -- a performance failure on admissible evidence -- rather than voting an
    authorization PASS against a performance FAIL (different questions)."""
    o = charger_obligation()
    items = network_artifacts_to_evidence()
    env = EvidenceEnvelope(o.id, items)

    vi = next(it for it in items if it.kind == "verifiable_intent_credential")
    authorization_clean = not vi.reveals_defect

    perf = PolicyVerifier(watch_kind="fulfillment_record", verifier_id="pv_performance")
    perf_out = perf.verify(o.id, env)

    decision = clear(o, [perf_out])
    return o, items, authorization_clean, perf_out, decision, settlement_instruction(decision)


def mock_network_rail(instruction: dict) -> str:
    return f"[network rail] executed '{instruction['action']}' under finality {instruction['finality']}"


def main() -> None:
    o, items, authorization_clean, perf_out, decision, si = run_scenario()

    print("RAILS as a neutral layer between a payment network and settlement")
    print(f"Scenario: VI-mandated {MANDATED_W}W charger; agent procured {DELIVERED_W}W "
          f"(authorization + payment clean).\n")

    print("INPUT  network artifacts -> Lambda classes:")
    for it in items:
        print(f"   - {it.kind:32s} class {it.claimed_class.name:5s} {it.payload_ref}")

    print("\nVERIFY per-leg:")
    print(f"   - authorization (VI credential): {'clean' if authorization_clean else 'DISPUTED'}")
    print(f"   - performance   (fulfillment)  : {perf_out.verdict.value}  "
          f"basis {'/'.join(c.name for c in perf_out.declared_basis)}  "
          f"({DELIVERED_W}W != mandated {MANDATED_W}W)")

    print(f"\nCLEAR  obligation floor = {o.floor.name}")
    print(f"   -> emitted={decision.emitted}  performance={decision.performance.value}  "
          f"policy={decision.policy.value}  basis={decision.cls_basis.name}")
    print("   (authorization clears; the wattage mismatch makes the determination a performance failure)")

    print("\nOUTPUT Settlement Instruction handed back to the rail:")
    for k, v in si.items():
        print(f"   {k:16s}: {v}")
    print("\n" + mock_network_rail(si))


if __name__ == "__main__":
    main()
