from __future__ import annotations

from typing import Optional, Protocol

from assessor.schemas import VendorProfile


class VendorResearchPort(Protocol):
    def research(self, vendor: str, official_domain: Optional[str] = None) -> VendorProfile: ...
