# mesh_scanner/config.py

from dataclasses import dataclass


@dataclass
class ScannerConfig:
    timeout: float = 2.0
    max_hosts: int = 512
    concurrency: int = 200
    banner_max_bytes: int = 2048

    def copy_with(
        self,
        timeout: float | None = None,
        max_hosts: int | None = None,
        concurrency: int | None = None,
        banner_max_bytes: int | None = None,
    ) -> "ScannerConfig":
        return ScannerConfig(
            timeout=timeout if timeout is not None else self.timeout,
            max_hosts=max_hosts if max_hosts is not None else self.max_hosts,
            concurrency=concurrency if concurrency is not None else self.concurrency,
            banner_max_bytes=(
                banner_max_bytes
                if banner_max_bytes is not None
                else self.banner_max_bytes
            ),
        )
