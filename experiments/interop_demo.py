"""Interoperability demo (Adrian wishlist item 6).

Shows RAILS sitting BETWEEN a payment network and settlement as a neutral layer:
it consumes a network artifact (a mock Verifiable Intent credential and a mock
Trusted Agent attestation) as evidence, runs the clearing core, and hands a
Settlement Instruction back to the network's rail to execute. RAILS does not
replace the rail or the customer relationship; it produces the clearing
determination the rail needs.

No API calls. Run:  python -m experiments.interop_demo
"""
from __future__ import annotations

from rails_ref.admissibility import Class
from rails_ref.objects import (
    ObligationObject, EvidenceEnvelope, EvidenceItem, VerifierOutput, Verdict,
)
from rails_ref.verifiers import PolicyVerifier
from rails_ref.mesh import clear


def network_artifacts_to_evidence() -> list[EvidenceItem]:
    """Map network artifacts onto Lambda. A Verifiable Intent credential binds
    issuer + user authorization + agent fulfillment (a third-party witness -> WIT);
    a Trusted Agent attestation rides a TEE/HTTP-edge attestation (-> ATT)."""
    return [
        EvidenceItem("verifiable_intent_credential", Class.WIT, Class.WIT, reveals_defect=False),
        EvidenceItem("trusted_agent_attestation", Class.ATT, Class.ATT, reveals_defect=False),
        EvidenceItem("agent_self_report", Class.SELF, Class.SELF, reveals_defect=False),
    ]


def settlement_instruction(decision) -> dict:
    """Translate a Clearing Decision into a rail-executable instruction."""
    return {
        "instruction_id": "0x7E29...3C4F",
        "decision_ref": decision.obligation_id,
        "action": "release" if decision.performance == Verdict.PASS and decision.policy == Verdict.PASS else "hold",
        "basis_class": decision.cls_basis.name,
        "finality": decision.finality.value,
        "execution_rail": "network_rail::settle",
    }


def mock_network_rail(instruction: dict) -> str:
    return f"[network rail] executed '{instruction['action']}' under finality {instruction['finality']}"


def main() -> None:
    o = ObligationObject("intent-9F2", Class.ATT, "agentic checkout: deliver and settle order #5567",
                         "authorized agent fulfilled the mandated purchase", ("buyer", "merchant"))
    items = network_artifacts_to_evidence()
    env = EvidenceEnvelope(o.id, items)

    # the network attestation is ATT-class evidence a verifier can stand on
    judge = VerifierOutput("network_attest_verifier", Verdict.PASS, 0.9, (Class.ATT,))
    panel = [PolicyVerifier(watch_kind="trusted_agent_attestation", verifier_id="pv_attest")]
    outs = [judge] + [v.verify(o.id, env) for v in panel]

    decision = clear(o, outs)
    si = settlement_instruction(decision)

    print("RAILS as a neutral layer between a payment network and settlement\n")
    print("INPUT  evidence (network artifacts -> Lambda classes):")
    for it in items:
        print(f"   - {it.kind:32s} class {it.claimed_class.name}")
    print(f"\nCLEAR  obligation floor = {o.floor.name}")
    print(f"   -> emitted={decision.emitted}  performance={decision.performance.value} "
          f"policy={decision.policy.value}  basis={decision.cls_basis.name}")
    print(f"\nOUTPUT Settlement Instruction handed back to the rail:")
    for k, v in si.items():
        print(f"   {k:16s}: {v}")
    print("\n" + mock_network_rail(si))


if __name__ == "__main__":
    main()
