"""
Example integration of LedgerClient in a mesh service.

This demonstrates how to use the LedgerClient in a FastAPI service
with proper 402 Payment Required error handling.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from mesh_fake_ledger import LedgerClient, PaymentRequiredError


# Initialize the ledger client
# For local/same-process: use json_path
# For distributed/microservices: use base_url
ledger = LedgerClient(json_path="ledger.json")
# Or: ledger = LedgerClient(base_url="http://ledger-api:8000")

app = FastAPI(title="Mesh Scanner Service")


# Request/Response models
class ScanJob(BaseModel):
    """Scan job specification."""
    id: str
    target: str
    ports: list[int]
    scan_type: str = "tcp"


class ScanResult(BaseModel):
    """Scan job result."""
    job_id: str
    findings: list[dict]
    tokens_charged: int


# Custom exception handler for PaymentRequiredError
@app.exception_handler(PaymentRequiredError)
async def payment_required_handler(request: Request, exc: PaymentRequiredError):
    """
    Convert PaymentRequiredError to HTTP 402 Payment Required.
    
    Returns JSON with payment details to help the client understand
    what's needed.
    """
    return JSONResponse(
        status_code=402,
        content={
            **exc.to_json(),
            "message": "Insufficient tokens to process this request",
            "request_path": str(request.url.path)
        }
    )


def estimate_cost(job: ScanJob) -> int:
    """
    Estimate the token cost for a scan job.
    
    In a real implementation, this would consider:
    - Number of ports to scan
    - Scan type (TCP, UDP, etc.)
    - Target complexity
    - Time estimates
    """
    base_cost = 10
    port_cost = len(job.ports) * 2
    
    if job.scan_type == "intensive":
        return (base_cost + port_cost) * 2
    
    return base_cost + port_cost


def execute_scan(job: ScanJob) -> list[dict]:
    """
    Execute the actual scan.
    
    This is a placeholder - real implementation would use nmap, etc.
    """
    # Simulate scan results
    return [
        {
            "port": port,
            "status": "open" if port in [80, 443, 22] else "closed",
            "service": "http" if port in [80, 443] else "ssh" if port == 22 else "unknown"
        }
        for port in job.ports
    ]


@app.post("/scan", response_model=ScanResult)
async def run_scan_job(
    job: ScanJob,
    payer: str,
    provider: str = "mesh_scanner_service"
):
    """
    Execute a scan job with payment.
    
    This endpoint:
    1. Estimates the cost
    2. Checks if payer can afford it
    3. Executes the scan
    4. Charges the tokens
    5. Returns results
    
    Raises:
        402 Payment Required: If payer has insufficient balance
        404 Not Found: If accounts don't exist
        500 Internal Server Error: If scan fails
    """
    # 1. Estimate cost
    cost_tokens = estimate_cost(job)
    
    # 2. Check payment (raises PaymentRequiredError if insufficient)
    # This is caught by the exception handler and converted to 402
    if not ledger.can_pay(payer, cost_tokens):
        raise PaymentRequiredError(
            required=cost_tokens,
            balance=ledger.get_balance(payer),
            account_id=payer
        )
    
    # 3. Charge upfront (alternative: charge after scan completes)
    ledger.charge(payer, provider, cost_tokens, job_id=job.id)
    
    try:
        # 4. Execute scan
        findings = execute_scan(job)
        
        # 5. Return results
        return ScanResult(
            job_id=job.id,
            findings=findings,
            tokens_charged=cost_tokens
        )
    
    except Exception as e:
        # If scan fails, you might want to refund the tokens
        # ledger.charge(provider, payer, cost_tokens, job_id=f"{job.id}_refund")
        raise HTTPException(
            status_code=500,
            detail=f"Scan failed: {str(e)}"
        )


@app.post("/scan-charge-after", response_model=ScanResult)
async def run_scan_job_charge_after(
    job: ScanJob,
    payer: str,
    provider: str = "mesh_scanner_service"
):
    """
    Alternative flow: Check balance, execute scan, THEN charge.
    
    This is safer for the payer (no charge if scan fails)
    but requires trust that the scanner will execute.
    """
    cost_tokens = estimate_cost(job)
    
    # Check if payer CAN pay (but don't charge yet)
    if not ledger.can_pay(payer, cost_tokens):
        raise PaymentRequiredError(
            required=cost_tokens,
            balance=ledger.get_balance(payer),
            account_id=payer
        )
    
    # Execute scan BEFORE charging
    findings = execute_scan(job)
    
    # Charge AFTER successful completion
    ledger.charge(payer, provider, cost_tokens, job_id=job.id)
    
    return ScanResult(
        job_id=job.id,
        findings=findings,
        tokens_charged=cost_tokens
    )


@app.get("/cost-estimate")
async def get_cost_estimate(
    target: str,
    num_ports: int,
    scan_type: str = "tcp"
) -> dict:
    """
    Get cost estimate without executing scan.
    
    Useful for clients to check if they have enough tokens.
    """
    dummy_job = ScanJob(
        id="estimate",
        target=target,
        ports=list(range(num_ports)),
        scan_type=scan_type
    )
    
    cost = estimate_cost(dummy_job)
    
    return {
        "estimated_cost": cost,
        "scan_type": scan_type,
        "num_ports": num_ports
    }


@app.get("/")
async def root():
    """API root."""
    return {
        "service": "Mesh Scanner Service",
        "version": "1.0.0",
        "payment": "Token-based via ledger"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Ensure provider account exists
    ledger.ensure_account("mesh_scanner_service", initial_balance=0)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
