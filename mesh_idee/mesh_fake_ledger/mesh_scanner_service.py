# mesh_scanner_service.py

from __future__ import annotations

import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mesh_scanner.config import ScannerConfig
from mesh_scanner.scanner import run_scan
from mesh_scanner.storage import init_db, save_results

from ledger_client import LedgerClient, LedgerClientConfig, PaymentRequiredError


# ---------------------------------------------------------
# Config
# ---------------------------------------------------------

DB_PATH = Path("mesh_scanner.sqlite3")
PROVIDER_ACCOUNT_ID = "mesh_scanner_provider"

# Ledger-Client: hier HTTP-Mode als Beispiel
ledger = LedgerClient(
    LedgerClientConfig(
        base_url="http://localhost:8001",  # dein Ledger-HTTP-Service
        service=None,                      # oder direkt FakeLedger-Instanz
    )
)

# Optional: sicherstellen, dass Provider-Account existiert
try:
    ledger.ensure_account(PROVIDER_ACCOUNT_ID, initial_balance=0)
except Exception:
    # im Zweifel ignoriere Fehler beim Startup
    pass


# ---------------------------------------------------------
# Pydantic-Schemas
# ---------------------------------------------------------

class ScanJobRequest(BaseModel):
    cidr: str = Field(..., description="z. B. 192.168.0.0/24")
    ports: List[int] = Field(..., description="Liste von Ports")
    account_id: str = Field(..., description="Zahlender Account")
    timeout: float = 2.0
    max_hosts: int = 256
    concurrency: int = 200
    banner_bytes: int = 2048


class ScanJobResponse(BaseModel):
    job_id: str
    targets_scanned: int
    open_ports: int
    estimated_tokens: int


class PaymentRequiredPayload(BaseModel):
    error: str = "payment_required"
    reason: str = "insufficient_compute_tokens"
    account_id: str
    required_tokens: int
    current_balance: int


# ---------------------------------------------------------
# Kostenmodell (vereinfachte Heuristik)
# ---------------------------------------------------------

def estimate_cost_tokens(host_count: int, port_count: int) -> int:
    """
    Simples Modell:
    - 1 Token pro (Host × Port) / 10, aufgerundet
    - Minimum 1 Token
    """
    raw = host_count * port_count
    tokens = (raw + 9) // 10  # ceil(raw / 10)
    return max(tokens, 1)


# ---------------------------------------------------------
# FastAPI-App
# ---------------------------------------------------------

app = FastAPI(title="Mesh Scanner Service", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    init_db(DB_PATH)


@app.post("/scan-jobs", response_model=ScanJobResponse)
async def create_scan_job(req: ScanJobRequest) -> ScanJobResponse:
    # 1) Kosten abschätzen
    from mesh_scanner.ip_range import expand_cidr

    hosts = expand_cidr(req.cidr, max_hosts=req.max_hosts)
    host_count = len(hosts)
    port_count = len(req.ports)

    if host_count == 0:
        raise HTTPException(status_code=400, detail="No hosts in CIDR / max_hosts=0")

    cost_tokens = estimate_cost_tokens(host_count, port_count)

    # 2) Account sicherstellen (optional)
    try:
        ledger.ensure_account(req.account_id, initial_balance=0)
    except Exception:
        # je nach Philosophie: Fehler durchreichen oder still ignorieren
        pass

    # 3) Charge versuchen → 402 bei zu wenig Guthaben
    try:
        ledger.charge(
            payer_id=req.account_id,
            receiver_id=PROVIDER_ACCOUNT_ID,
            amount=cost_tokens,
            job_id=None,
        )
    except PaymentRequiredError as e:
        payload = PaymentRequiredPayload(
            account_id=e.account_id,
            required_tokens=e.required,
            current_balance=e.balance,
        )
        # 402 Payment Required
        raise HTTPException(status_code=402, detail=payload.dict())

    # 4) Scan ausführen (hier synchron, für „echten“ Betrieb eher als Background-Task)
    cfg = ScannerConfig(
        timeout=req.timeout,
        max_hosts=req.max_hosts,
        concurrency=req.concurrency,
        banner_max_bytes=req.banner_bytes,
    )

    results = await run_scan(req.cidr, req.ports, cfg)
    save_results(DB_PATH, results)

    open_ports = sum(1 for r in results if r.is_open)
    job_id = str(uuid.uuid4())

    return ScanJobResponse(
        job_id=job_id,
        targets_scanned=host_count,
        open_ports=open_ports,
        estimated_tokens=cost_tokens,
    )
