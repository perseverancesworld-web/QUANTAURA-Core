"""Intent API — receive, validate, evaluate, and transition intents.

Core invariant: No execution occurs without a verified, authorized intent.
Now backed by a durable SQLite ledger and multi-party approval support.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from quantaura.crypto.signatures import compute_payload_hash, verify_signature
from quantaura.ledger.state_machine import (
    IntentStatus,
    InvalidStateTransitionError,
    transition_state,
)
from quantaura.ledger.store import store
from quantaura.policy.evaluator import PolicyEngine
from quantaura.policy.approvals import ApprovalManager

router = APIRouter(prefix="/v1/intents", tags=["Intents"])
policy_engine = PolicyEngine()
approval_manager = ApprovalManager()

TENANT_KEYS: dict[str, str] = {}


class IntentPayload(BaseModel):
    action_type: str = Field(..., description="Action identifier, e.g. TRANSFER_FUNDS")
    payload: dict[str, Any] = Field(default_factory=dict)
    required_approvals: int = Field(1, ge=1, le=10, description="Number of distinct approvals needed")


class TransitionRequest(BaseModel):
    target_status: IntentStatus


class ApprovalRequest(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject)$")
    comment: str = ""


@router.post("", status_code=201)
def create_intent(
    body: IntentPayload,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_quantaura_signature: Optional[str] = Header(None, alias="X-QUANTAURA-Signature"),
) -> dict[str, Any]:
    """Submit a new intent for authorization."""
    payload_hash = compute_payload_hash(body.payload)

    if x_tenant_id in TENANT_KEYS:
        if not x_quantaura_signature:
            raise HTTPException(status_code=401, detail="Signature required for this tenant")
        public_key = TENANT_KEYS[x_tenant_id]
        if not verify_signature(public_key, body.payload, x_quantaura_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    decision = policy_engine.evaluate(body.action_type, body.payload)

    if not decision.allowed:
        initial_status = IntentStatus.REJECTED
    elif decision.requires_approval or body.required_approvals > 1:
        initial_status = IntentStatus.PENDING_AUTHORIZATION
    else:
        initial_status = IntentStatus.AUTHORIZED

    intent_id = f"req_{uuid.uuid4().hex[:12]}"
    record = {
        "intent_id": intent_id,
        "tenant_id": x_tenant_id,
        "action_type": body.action_type,
        "payload_hash": payload_hash,
        "status": initial_status.value if hasattr(initial_status, "value") else initial_status,
        "reason": decision.reason,
        "payload": body.payload,
        "approvals": [],
        "required_approvals": body.required_approvals,
    }
    store.save(record)
    store.append_audit(intent_id, "created", actor=x_tenant_id, detail={"status": initial_status.value})
    return record


@router.get("/{intent_id}")
def get_intent(intent_id: str) -> dict[str, Any]:
    record = store.get(intent_id)
    if not record:
        raise HTTPException(status_code=404, detail="Intent not found")
    return record


@router.post("/{intent_id}/transition")
def transition_intent(
    intent_id: str,
    body: TransitionRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
) -> dict[str, Any]:
    record = store.get(intent_id)
    if not record:
        raise HTTPException(status_code=404, detail="Intent not found")
    if record["tenant_id"] != x_tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")

    try:
        new_status = transition_state(
            IntentStatus(record["status"]), body.target_status
        )
    except InvalidStateTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record["status"] = new_status.value if hasattr(new_status, "value") else new_status
    record["reason"] = f"Transitioned to {new_status.value}"
    store.save(record)
    store.append_audit(
        intent_id, "transition", actor=x_tenant_id, detail={"to": new_status.value}
    )
    return record


@router.post("/{intent_id}/approve")
def approve_intent(
    intent_id: str,
    body: ApprovalRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_actor: str = Header(..., alias="X-Actor"),
) -> dict[str, Any]:
    """Submit a human/service approval or rejection for a pending intent."""
    record = store.get(intent_id)
    if not record:
        raise HTTPException(status_code=404, detail="Intent not found")
    if record["status"] != IntentStatus.PENDING_AUTHORIZATION.value:
        raise HTTPException(
            status_code=409,
            detail=f"Intent is not pending authorization (current: {record['status']})",
        )

    result = approval_manager.add_approval(
        current_approvals=record.get("approvals", []),
        required=record.get("required_approvals", 1),
        actor=x_actor,
        decision=body.decision,
        comment=body.comment,
    )

    record["approvals"] = result.approvals
    record["reason"] = result.reason

    if result.complete:
        if result.authorized:
            record["status"] = IntentStatus.AUTHORIZED.value
        else:
            record["status"] = IntentStatus.REJECTED.value

    store.save(record)
    store.append_audit(
        intent_id,
        "approval",
        actor=x_actor,
        detail={"decision": body.decision, "complete": result.complete},
    )
    return record


@router.get("")
def list_intents(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
) -> list[dict[str, Any]]:
    return store.list_for_tenant(x_tenant_id)


@router.post("/register-key")
def register_tenant_key(
    public_key_hex: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
) -> dict[str, str]:
    TENANT_KEYS[x_tenant_id] = public_key_hex
    return {"tenant_id": x_tenant_id, "status": "registered"}
