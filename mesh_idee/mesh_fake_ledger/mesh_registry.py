# mesh_registry.py
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

class WorkerCapability(BaseModel):
    kind: str
    cost: int  # Token cost per job

class WorkerInfo(BaseModel):
    worker_id: str
    capabilities: List[WorkerCapability]
    status: str = "online"
    last_seen: float = 0.0
    endpoint: Optional[str] = None # For remote mesh workers if needed

class WorkerRegistry:
    def __init__(self, storage_path: Path = Path("workers.json")):
        self.storage_path = storage_path
        self.workers: Dict[str, WorkerInfo] = {}
        self.load()

    def load(self):
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                raw_workers = {k: WorkerInfo(**v) for k, v in data.items()}
                
                # PRUNE stale workers (e.g. not seen for 2 minutes) on load
                # to keep the registry clean and avoid choosing dead nodes.
                now = time.time()
                self.workers = {
                    k: v for k, v in raw_workers.items() 
                    if (now - v.last_seen) < 120 # 2 minutes
                }
                
                if len(self.workers) < len(raw_workers):
                    print(f"[registry] Pruned {len(raw_workers) - len(self.workers)} stale workers.")
                    self.save() # Persist the cleanup
            except Exception:
                self.workers = {}

    def save(self):
        data = {k: v.dict() for k, v in self.workers.items()}
        self.storage_path.write_text(json.dumps(data, indent=2))

    def register(self, worker: WorkerInfo):
        worker.last_seen = time.time()
        self.workers[worker.worker_id] = worker
        self.save()

    def get_worker(self, worker_id: str) -> Optional[WorkerInfo]:
        return self.workers.get(worker_id)

    def find_workers_for_kind(self, kind: str) -> List[WorkerInfo]:
        """Finds online workers for a kind, filtering out those not seen in 60s."""
        now = time.time()
        STALE_THRESHOLD = 60 # seconds
        
        return [
            w for w in self.workers.values()
            if any(c.kind == kind for c in w.capabilities) 
            and w.status == "online"
            and (now - w.last_seen) < STALE_THRESHOLD
        ]

    def heartbeat(self, worker_id: str):
        if worker_id in self.workers:
            self.workers[worker_id].last_seen = time.time()
            self.workers[worker_id].status = "online"
            self.save()

    def get_best_worker(self, kind: str) -> Optional[WorkerInfo]:
        """Finds the cheapest online worker for a given kind."""
        candidates = self.find_workers_for_kind(kind)
        if not candidates:
            return None
        # Simple heuristic: cheapest cost for this kind
        return min(candidates, key=lambda w: next(c.cost for c in w.capabilities if c.kind == kind))
