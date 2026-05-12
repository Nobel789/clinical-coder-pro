from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .coding_pipeline import suggest_codes


class CodingRequest(BaseModel):
    raw_note_text: str = Field(..., min_length=1)
    note_date: date | None = None


class AuditEvent(BaseModel):
    action: str
    candidate_id: str | None = None
    code: str | None = None
    code_system: str | None = None
    status: str | None = None
    reviewer: str = "demo.coder"
    note: str | None = None


AUDIT_LOG: list[dict] = []


app = FastAPI(
    title="Clinical Coder Pro Prototype",
    description="Clinical note to candidate coding API with human review and audit support.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/suggest-codes")
def suggest_codes_endpoint(request: CodingRequest) -> dict:
    return suggest_codes(request.raw_note_text, request.note_date)


@app.post("/api/audit-events")
def record_audit_event(event: AuditEvent) -> dict:
    audit_entry = event.model_dump()
    audit_entry["id"] = str(uuid4())
    audit_entry["created_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    AUDIT_LOG.append(audit_entry)
    return {"status": "recorded", "audit_event": audit_entry}


@app.get("/api/audit-events")
def list_audit_events() -> dict:
    return {"events": AUDIT_LOG[-100:]}
