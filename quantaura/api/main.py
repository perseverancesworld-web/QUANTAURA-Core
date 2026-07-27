"""QUANTAURA-Core FastAPI application and CLI entry point."""

from __future__ import annotations

import argparse

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from quantaura.api.routes.intents import router as intents_router
from quantaura.api.routes.research import router as research_router

app = FastAPI(
    title="QUANTAURA-Core API",
    description=(
        "Execution Authorization Kernel + Unified research OS. "
        "No execution occurs without a verified, authorized intent."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intents_router)
app.include_router(research_router)


@app.get("/")
def root():
    return {
        "service": "quantaura-core",
        "version": "0.1.0",
        "status": "ok",
        "kernel": "Execution Authorization Kernel",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/system/status")
def system_status():
    return {
        "status": "operational",
        "version": "0.1.0",
        "platform": "QUANTAURA-Core",
        "components": {
            "crypto": "active",
            "state_machine": "active",
            "policy_engine": "active",
            "intent_api": "active",
            "research_api": "active",
        },
    }


def cli_serve() -> None:
    """CLI entry point: `quantaura-serve`."""
    parser = argparse.ArgumentParser(prog="quantaura-serve")
    parser.add_argument("--host", default="0.0.0.0", type=str, help="Host to bind.")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind.")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload.")
    args = parser.parse_args()

    uvicorn.run(
        "quantaura.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    cli_serve()
