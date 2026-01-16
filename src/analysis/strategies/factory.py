from typing import Dict, Any
from .commodity import CommodityStrategy
from .equity import EquityStrategy
from .stock import StockStrategy


class StrategyFactory:
    @staticmethod
    def get_strategy(item_info: Dict[str, Any], llm_client, web_search):
        """
        Returns the appropriate strategy instance based on asset type and characteristics.

        Supports:
        - type="stock": Individual stock analysis (StockStrategy)
        - type="fund" with commodity keywords: Commodity fund analysis (CommodityStrategy)
        - type="fund" (default): Equity fund analysis (EquityStrategy)
        """
        item_type = item_info.get("type", "fund")

        # 股票类型 - 使用 StockStrategy
        if item_type == "stock":
            return StockStrategy(item_info, llm_client, web_search)

        # 基金类型 - 根据名称判断
        name = item_info.get("name", "")

        # 商品类基金
        if any(k in name for k in ["黄金", "白银", "有色", "油", "石油", "贵金属", "商品"]):
            return CommodityStrategy(item_info, llm_client, web_search)

        # 默认股票型/混合型基金
        return EquityStrategy(item_info, llm_client, web_search)
