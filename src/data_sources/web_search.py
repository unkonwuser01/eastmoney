from tavily import TavilyClient
import os
import sys
from typing import List, Dict, Optional
from datetime import datetime
from itertools import cycle

# Add project root to sys.path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import TAVILY_API_KEY

class WebSearch:
    """
    专业级搜索引擎 - 分层搜索策略
    Layer 1: 官方公告 (最高优先级)
    Layer 2: 卖方研报/评级
    Layer 3: 产业链动态
    Layer 4: 一般新闻/舆情
    """
    
    def __init__(self):
        if not TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is not set in environment variables.")
        
        # Support multiple keys separated by comma
        keys = [k.strip() for k in TAVILY_API_KEY.split(',') if k.strip()]
        if not keys:
            raise ValueError("No valid TAVILY_API_KEY found.")
            
        self.clients = [TavilyClient(api_key=key) for key in keys]
        self.client_cycle = cycle(self.clients)
        print(f"WebSearch initialized with {len(keys)} Tavily keys.")
        
        # 高质量财经信源域名
        self.quality_domains = [
            "eastmoney.com",      # 东方财富
            "cninfo.com.cn",      # 巨潮资讯（官方公告）
            "sse.com.cn",         # 上交所
            "szse.cn",            # 深交所
            "cs.com.cn",          # 中证网
            "stcn.com",           # 证券时报
            "nbd.com.cn",         # 每日经济新闻
            "caixin.com",         # 财新
            "yicai.com",          # 第一财经
            "finance.sina.com.cn" # 新浪财经
        ]

    def _get_client(self):
        """Get the next client in the rotation"""
        return next(self.client_cycle)

    def search_news(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search for news articles related to the query.
        """
        try:
            client = self._get_client()
            response = client.search(
                query=query,
                search_depth="advanced",
                topic="news",
                max_results=max_results,
                include_answer=False,
                include_raw_content=False,
                include_images=False,
            )
            return response.get("results", [])
        except Exception as e:
            print(f"Error searching Tavily: {e}")
            return []

    def search_general(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        General web search (not restricted to news).
        """
        try:
            client = self._get_client()
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results
            )
            return response.get("results", [])
        except Exception as e:
            print(f"Error searching Tavily (General): {e}")
            return []

    # =========================================================================
    # 专业分层搜索方法
    # =========================================================================
    
    def search_stock_announcements(self, stock_name: str, max_results: int = 3) -> List[Dict]:
        """
        Layer 1: 搜索公司公告（最高置信度）
        """
        query = f"{stock_name} 公告 site:eastmoney.com OR site:cninfo.com.cn"
        results = self.search_general(query, max_results)
        for r in results:
            r['source_type'] = '官方公告'
            r['confidence'] = 'HIGH'
        return results

    def search_analyst_reports(self, stock_name: str, max_results: int = 3) -> List[Dict]:
        """
        Layer 2: 搜索卖方研报/评级变化
        """
        today = datetime.now().strftime("%Y年%m月")
        query = f"{stock_name} 研报 评级 目标价 {today}"
        results = self.search_news(query, max_results)
        for r in results:
            r['source_type'] = '研报/评级'
            r['confidence'] = 'MEDIUM-HIGH'
        return results

    def search_industry_chain(self, stock_name: str, industry: str = None, max_results: int = 3) -> List[Dict]:
        """
        Layer 3: 搜索产业链上下游动态
        """
        if industry:
            query = f"{stock_name} {industry} 上游 OR 下游 OR 供应链 OR 客户 最新"
        else:
            query = f"{stock_name} 产业链 供应商 OR 客户 动态"
        results = self.search_news(query, max_results)
        for r in results:
            r['source_type'] = '产业链动态'
            r['confidence'] = 'MEDIUM'
        return results

    def search_risk_events(self, stock_name: str, max_results: int = 3) -> List[Dict]:
        """
        Layer 4: 搜索风险事件/负面舆情
        """
        query = f"{stock_name} 诉讼 OR 处罚 OR 减持 OR 高管变动 OR 违规 OR 风险"
        results = self.search_news(query, max_results)
        for r in results:
            r['source_type'] = '风险监控'
            r['confidence'] = 'MEDIUM'
        return results

    def search_policy_news(self, industry: str, max_results: int = 3) -> List[Dict]:
        """
        搜索行业政策新闻
        """
        today = datetime.now().strftime("%Y年%m月")
        query = f"{industry} 政策 OR 补贴 OR 规划 OR 监管 {today}"
        results = self.search_news(query, max_results)
        for r in results:
            r['source_type'] = '政策动态'
            r['confidence'] = 'HIGH'
        return results

    def search_macro_events(self, max_results: int = 5) -> List[Dict]:
        """
        搜索宏观经济事件（美联储、央行等）
        """
        query = "美联储 OR 央行 OR 降息 OR 加息 OR 非农 OR CPI 最新"
        results = self.search_news(query, max_results)
        for r in results:
            r['source_type'] = '宏观事件'
            r['confidence'] = 'HIGH'
        return results

    def comprehensive_stock_search(self, stock_name: str, industry: str = None) -> Dict[str, List[Dict]]:
        """
        综合搜索：一次性获取某只股票的多维度信息
        返回结构化的分层数据
        """
        return {
            "announcements": self.search_stock_announcements(stock_name, 2),
            "analyst_reports": self.search_analyst_reports(stock_name, 2),
            "industry_chain": self.search_industry_chain(stock_name, industry, 2),
            "risk_events": self.search_risk_events(stock_name, 2)
        }

    def get_market_sentiment_news(self, topics: List[str], max_per_topic: int = 2) -> List[Dict]:
        """
        批量获取多个主题的市场情绪新闻
        """
        all_news = []
        for topic in topics:
            news = self.search_news(f"{topic} 最新动态 分析", max_per_topic)
            for item in news:
                item['topic'] = topic
            all_news.extend(news)
        return all_news
