"""QUANTAURA-Core FastAPI application and CLI entry point."""

from __future__ import annotations

import argparse

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from quantaura.api.routes.intents import router as intents_router
from quantaura.api.routes.research import router as research_router
from quantaura.api.routes.qpie import router as qpie_router
from quantaura.config import settings

app = FastAPI(
    title="QUANTAURA-Core API",
    description=(
        "Agent Execution Authorization Kernel + QPIE Physical Intelligence Engine. "
        "No execution occurs without a verified, authorized intent."
    ),
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intents_router)
app.include_router(research_router)
app.include_router(qpie_router)


@app.get("/")
def root():
    return {
        "service": "quantaura-core",
        "version": "0.4.0",
        "status": "ok",
        "kernel": "Execution Authorization Kernel",
        "qpie": "Physical Intelligence Engine",
        "invariant": "No execution occurs without a verified, authorized intent.",
        "environment": settings.environment,
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/system/status")
def system_status():
    return {
        "status": "operational",
        "version": "0.4.0",
        "platform": "QUANTAURA-Core",
        "environment": settings.environment,
        "components": {
            "crypto": "active",
            "state_machine": "active",
            "policy_engine": "active",
            "intent_api": "active",
            "audit_export": "active",
            "research_api": "active",
            "qpie": "active",
        },
        "tenancy": {
            "allowed_tenants_configured": bool(settings.allowed_tenants),
            "require_signature": settings.require_signature,
        },
    }


def cli_serve() -> None:
    parser = argparse.ArgumentParser(prog="quantaura-serve")
    parser.add_argument("--host", default="0.0.0.0", type=str)
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    uvicorn.run("quantaura.api.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    cli_serve()
