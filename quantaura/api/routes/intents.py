"""Intent API — receive, validate, evaluate, and transition intents.

Core invariant: No execution occurs without a verified, authorized intent.
Backed by durable ledger, multi-party approvals, and tenant isolation.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from quantaura.config import settings
from quantaura.crypto.signatures import compute_payload_hash, verify_signature
from quantaura.ledger.audit_export import audit_to_csv, list_audit_rows
from quantaura.ledger.state_machine import (
    IntentStatus,
    InvalidStateTransitionError,
    transition_state,
)
from quantaura.ledger.store import store
from quantaura.policy.approvals import ApprovalManager
from quantaura.policy.evaluator import PolicyEngine

router = APIRouter(prefix="/v1/intents", tags=["Intents"])
policy_engine = PolicyEngine()
approval_manager = ApprovalManager()

TENANT_KEYS: dict[str, str] = {}


class IntentPayload(BaseModel):
    action_type: str = Field(..., description="Action identifier, e.g. TRANSFER_FUNDS")
    payload: dict[str, Any] = Field(default_factory=dict)
    required_approvals: int = Field(
        1, ge=1, le=10, description="Number of distinct approvals needed"
    )


class TransitionRequest(BaseModel):
    target_status: IntentStatus


class ApprovalRequest(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject)$")
    comment: str = ""
    role: str = ""


def _check_tenant(tenant_id: str) -> None:
    if not settings.tenant_allowed(tenant_id):
        raise HTTPException(status_code=403, detail=f"Tenant '{tenant_id}' is not allowed")


@router.post("", status_code=201)
def create_intent(
    body: IntentPayload,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_quantaura_signature: Optional[str] = Header(None, alias="X-QUANTAURA-Signature"),
) -> dict[str, Any]:
    """Submit a new intent for authorization."""
    _check_tenant(x_tenant_id)
    payload_hash = compute_payload_hash(body.payload)

    must_sign = settings.require_signature or x_tenant_id in TENANT_KEYS
    if must_sign:
        if not x_quantaura_signature:
            raise HTTPException(status_code=401, detail="Signature required for this tenant")
        public_key = TENANT_KEYS.get(x_tenant_id)
        if not public_key:
            raise HTTPException(
                status_code=401,
                detail="No public key registered for tenant; POST /v1/intents/register-key",
            )
        if not verify_signature(public_key, body.payload, x_quantaura_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    decision = policy_engine.evaluate(body.action_type, body.payload)
    required = max(body.required_approvals, settings.default_required_approvals)

    if not decision.allowed:
        initial_status = IntentStatus.REJECTED
    elif decision.requires_approval or required > 1:
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
        "required_approvals": required,
    }
    store.save(record)
    store.append_audit(
        intent_id, "created", actor=x_tenant_id, detail={"status": initial_status.value}
    )
    return record


@router.get("/audit")
def export_audit(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    format: str = Query("json", pattern="^(json|csv)$"),
) -> Any:
    """Export audit trail for the tenant (JSON or CSV)."""
    _check_tenant(x_tenant_id)
    rows = list_audit_rows(store, x_tenant_id)
    if format == "csv":
        return PlainTextResponse(
            audit_to_csv(rows),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="quantaura-audit-{x_tenant_id}.csv"'
            },
        )
    return {"tenant_id": x_tenant_id, "count": len(rows), "events": rows}


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
    _check_tenant(x_tenant_id)
    record = store.get(intent_id)
    if not record:
        raise HTTPException(status_code=404, detail="Intent not found")
    if record["tenant_id"] != x_tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")

    try:
        new_status = transition_state(IntentStatus(record["status"]), body.target_status)
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
    _check_tenant(x_tenant_id)
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
        role=body.role,
        created_at=record.get("created_at"),
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
        detail={"decision": body.decision, "complete": result.complete, "role": body.role},
    )
    return record


@router.get("")
def list_intents(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
) -> list[dict[str, Any]]:
    _check_tenant(x_tenant_id)
    return store.list_for_tenant(x_tenant_id)


@router.post("/register-key")
def register_tenant_key(
    public_key_hex: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
) -> dict[str, str]:
    _check_tenant(x_tenant_id)
    TENANT_KEYS[x_tenant_id] = public_key_hex
    return {"tenant_id": x_tenant_id, "status": "registered"}
