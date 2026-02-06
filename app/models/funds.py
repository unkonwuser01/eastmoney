"""
Fund-related Pydantic models.
"""
from typing import Optional, List
from pydantic import BaseModel


class FundItem(BaseModel):
    """Fund item for user's watchlist."""
    code: str
    name: str
    style: Optional[str] = "Unknown"
    focus: Optional[List[str]] = []
    pre_market_time: Optional[str] = None
    post_market_time: Optional[str] = None
    is_active: bool = True
    is_etf_linkage: Optional[bool] = False  # 是否为ETF联接基金
    etf_code: Optional[str] = None  # 关联的ETF代码


class FundCompareRequest(BaseModel):
    """Request for comparing multiple funds."""
    codes: List[str]
