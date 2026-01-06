"""
Post-Market Analyst - 专业级盘后复盘系统
=======================================
模拟专业基金经理团队的盘后复盘流程：
1. 今日市场表现汇总
2. 基金净值与业绩归因
3. 重仓股表现分析
4. 资金流向复盘
5. 明日展望
"""

import json
import sys
import os
from typing import List, Dict
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import FUNDS_FILE
from src.data_sources.akshare_api import (
    get_fund_info,
    get_fund_holdings,
    get_market_indices,
    get_northbound_flow,
    get_industry_capital_flow,
    get_sector_performance,
    get_stock_realtime_quote
)
from src.data_sources.web_search import WebSearch
from src.llm.client import get_llm_client
from src.llm.prompts import POST_MARKET_PROMPT_TEMPLATE


class PostMarketAnalyst:
    """
    专业级盘后复盘分析师
    模拟基金经理团队的收盘后复盘流程
    """
    
    def __init__(self):
        self.web_search = WebSearch()
        self.llm = get_llm_client()
        self.funds = self._load_funds()
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.sources = []  # 数据来源追踪

    def _load_funds(self) -> List[Dict]:
        if not os.path.exists(FUNDS_FILE):
            print(f"Warning: Funds file not found at {FUNDS_FILE}")
            return []
        with open(FUNDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    # =========================================================================
    # Source Tracking Utilities
    # =========================================================================
    
    def _reset_sources(self):
        """每次分析新基金前重置来源列表"""
        self.sources = []
    
    def _add_source(self, category: str, title: str, url: str = None, source_name: str = None):
        """添加一个数据来源"""
        source_entry = {
            'category': category,
            'title': title[:100] if title else 'N/A',
            'url': url,
            'source': source_name
        }
        # 避免重复
        if not any(s['title'] == source_entry['title'] and s['url'] == source_entry['url'] for s in self.sources):
            self.sources.append(source_entry)
    
    def _format_sources(self) -> str:
        """格式化数据来源为报告附录"""
        if not self.sources:
            return ""
        
        output = []
        output.append("\n\n---")
        output.append("\n## 📚 数据来源 (Sources Used in This Report)")
        
        # 按类别分组
        categories = {}
        for source in self.sources:
            cat = source['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(source)
        
        # 格式化输出
        for cat, items in categories.items():
            output.append(f"\n### {cat}")
            for i, item in enumerate(items, 1):
                title = item['title']
                url = item['url']
                source_name = item.get('source', '')
                
                if url:
                    output.append(f"{i}. [{title}]({url})")
                else:
                    source_suffix = f" - {source_name}" if source_name else ""
                    output.append(f"{i}. {title}{source_suffix}")
        
        # 固定数据源说明
        output.append("\n### 📊 市场数据来源")
        output.append("- AkShare: A股指数、北向资金、行业资金流向、个股行情")
        output.append("- 东方财富: 基金净值、持仓数据")
        output.append("- Tavily Search API: 实时新闻搜索")
        
        return "\n".join(output)

    # =========================================================================
    # 数据收集模块
    # =========================================================================
    
    def collect_market_performance(self) -> str:
        """收集今日市场整体表现"""
        print("  📈 收集市场表现数据...")
        
        market_data = get_market_indices()
        output = []
        
        output.append("**主要指数:**")
        for name, data in market_data.items():
            if isinstance(data, dict):
                close = data.get('收盘', data.get('close', 'N/A'))
                change = data.get('涨跌幅', data.get('change', 'N/A'))
                output.append(f"- {name}: {close} ({change}%)")
        
        # 获取板块涨跌榜
        sector_perf = get_sector_performance()
        if sector_perf.get('板块涨幅榜'):
            output.append("\n**板块涨幅Top5:**")
            for item in sector_perf['板块涨幅榜'][:5]:
                if isinstance(item, dict):
                    name = item.get('板块名称', 'N/A')
                    change = item.get('涨跌幅', 'N/A')
                    output.append(f"- {name}: {change}%")
        
        return "\n".join(output) if output else "市场数据暂无"

    def collect_fund_performance(self, fund_code: str) -> str:
        """收集基金今日表现"""
        print("  💹 收集基金净值数据...")
        
        fund_df = get_fund_info(fund_code)
        
        if fund_df.empty:
            return "基金净值数据暂无"
        
        output = []
        latest = fund_df.iloc[0]
        
        output.append("**基金净值:**")
        output.append(f"- 净值日期: {latest.get('净值日期', 'N/A')}")
        output.append(f"- 单位净值: {latest.get('单位净值', 'N/A')}")
        output.append(f"- 日增长率: {latest.get('日增长率', 'N/A')}%")
        
        # 近期走势
        if len(fund_df) >= 5:
            output.append("\n**近5日走势:**")
            for i, row in fund_df.head(5).iterrows():
                date = row.get('净值日期', 'N/A')
                nav = row.get('单位净值', 'N/A')
                change = row.get('日增长率', 'N/A')
                output.append(f"- {date}: {nav} ({change}%)")
        
        return "\n".join(output)

    def collect_holdings_performance(self, fund_code: str) -> tuple:
        """收集重仓股今日表现"""
        print("  📊 分析重仓股表现...")
        
        holdings_df = get_fund_holdings(fund_code)
        
        if holdings_df.empty:
            return "重仓股数据暂无", []
        
        # 提取持仓
        name_col = next((col for col in holdings_df.columns if '名称' in col), None)
        code_col = next((col for col in holdings_df.columns if '代码' in col), None)
        ratio_col = next((col for col in holdings_df.columns if '比例' in col), None)
        
        # 获取最新一期
        if '季度' in holdings_df.columns:
            latest_quarter = holdings_df['季度'].iloc[0]
            holdings_df = holdings_df[holdings_df['季度'] == latest_quarter]
        
        top_holdings = holdings_df.head(10)
        holdings_list = []
        output = []
        
        output.append("**重仓股今日表现:**")
        
        for _, row in top_holdings.iterrows():
            name = row.get(name_col, 'N/A') if name_col else 'N/A'
            code = str(row.get(code_col, '')) if code_col else ''
            ratio = row.get(ratio_col, 'N/A') if ratio_col else 'N/A'
            
            if name != 'N/A':
                holdings_list.append({'name': name, 'code': code, 'ratio': ratio})
                
                # 获取实时行情
                quote = get_stock_realtime_quote(code)
                if quote:
                    price = quote.get('最新价', 'N/A')
                    change = quote.get('涨跌幅', 'N/A')
                    output.append(f"- {name}({code}): {price} ({change}%) [持仓{ratio}%]")
                else:
                    output.append(f"- {name}({code}): 行情暂无 [持仓{ratio}%]")
        
        return "\n".join(output), holdings_list

    def collect_capital_flow(self) -> str:
        """收集今日资金流向"""
        print("  💰 分析今日资金流向...")
        
        output = []
        
        # 北向资金
        northbound = get_northbound_flow()
        if northbound and northbound.get('最新净流入'):
            output.append("**北向资金:**")
            output.append(f"- 今日净流入: {northbound['最新净流入']}")
            if northbound.get('5日累计净流入'):
                output.append(f"- 5日累计: {northbound['5日累计净流入']}亿")
        
        # 行业资金流向
        sector_flow = get_industry_capital_flow()
        if sector_flow.get('行业资金流向Top10'):
            output.append("\n**行业主力资金流向:**")
            for item in sector_flow['行业资金流向Top10'][:5]:
                if isinstance(item, dict):
                    name = item.get('名称', 'N/A')
                    flow = item.get('今日主力净流入', item.get('主力净流入', 'N/A'))
                    output.append(f"- {name}: {flow}")
        
        return "\n".join(output) if output else "资金流向数据暂无"

    def collect_intraday_news(self, fund_name: str, holdings_list: List[Dict]) -> str:
        """收集盘中重要新闻"""
        print("  📰 搜索盘中新闻...")
        
        output = []
        
        # 搜索基金相关新闻
        fund_news = self.web_search.search_news(f"{fund_name} 今日 涨跌 原因", max_results=3)
        if fund_news:
            output.append("**基金相关:**")
            for news in fund_news:
                title = news.get('title', news.get('content', ''))[:80]
                output.append(f"- {title}")
                # 追踪来源
                self._add_source(
                    category="📰 基金新闻",
                    title=title,
                    url=news.get('url'),
                    source_name=news.get('source', 'Web Search')
                )
        
        # 搜索重仓股新闻
        for holding in holdings_list[:3]:
            stock_news = self.web_search.search_news(f"{holding['name']} 今日", max_results=1)
            if stock_news:
                output.append(f"\n**{holding['name']}:**")
                for news in stock_news:
                    title = news.get('title', news.get('content', ''))[:80]
                    output.append(f"- {title}")
                    # 追踪来源
                    self._add_source(
                        category="📊 重仓股新闻",
                        title=f"[{holding['name']}] {title}",
                        url=news.get('url'),
                        source_name=news.get('source', 'Web Search')
                    )
        
        return "\n".join(output) if output else "暂无相关盘中新闻"
        
        return "\n".join(output) if output else "暂无相关盘中新闻"

    def collect_sector_data(self, fund_focus: List[str]) -> str:
        """收集相关板块表现"""
        print("  🏢 分析相关板块...")
        
        output = []
        
        for focus in fund_focus[:3]:
            sector = get_sector_performance(focus)
            if sector and isinstance(sector, dict) and '板块名称' in sector:
                output.append(f"**{focus}板块:**")
                output.append(f"- 涨跌幅: {sector.get('涨跌幅', 'N/A')}%")
                output.append(f"- 主力净流入: {sector.get('主力净流入', 'N/A')}")
        
        return "\n".join(output) if output else "板块数据暂无"

    # =========================================================================
    # 主分析流程
    # =========================================================================
    
    def analyze_fund(self, fund: Dict) -> str:
        """
        单只基金的完整盘后复盘流程
        """
        fund_code = fund.get("code")
        fund_name = fund.get("name")
        fund_focus = fund.get("focus", [])
        
        print(f"\n{'='*60}")
        print(f"📊 复盘基金: {fund_name} ({fund_code})")
        print(f"{'='*60}")
        
        # 重置来源追踪
        self._reset_sources()
        
        # Step 1: 市场表现
        market_data = self.collect_market_performance()
        
        # Step 2: 基金表现
        fund_performance = self.collect_fund_performance(fund_code)
        
        # Step 3: 重仓股表现
        holdings_performance, holdings_list = self.collect_holdings_performance(fund_code)
        
        # Step 4: 板块表现
        sector_data = self.collect_sector_data(fund_focus)
        
        # Step 5: 资金流向
        capital_flow = self.collect_capital_flow()
        
        # Step 6: 盘中新闻
        intraday_news = self.collect_intraday_news(fund_name, holdings_list)
        
        # Step 7: 构建Prompt并调用LLM
        print("  🤖 AI 归因分析中...")
        
        prompt = POST_MARKET_PROMPT_TEMPLATE.format(
            fund_name=fund_name,
            fund_code=fund_code,
            market_data=market_data,
            fund_performance=fund_performance,
            holdings_performance=holdings_performance,
            sector_data=sector_data,
            capital_flow=capital_flow,
            intraday_news=intraday_news,
            report_date=self.today  # 传入实际日期
        )
        
        # 调用LLM生成报告
        report = self.llm.generate_content(prompt)
        
        # 附加数据来源
        sources_section = self._format_sources()
        if sources_section:
            report = report + sources_section
        
        print(f"  📚 收集到 {len(self.sources)} 个数据来源")
        print("  ✅ 复盘完成")
        return report

    def run_all(self) -> str:
        """
        运行所有基金的盘后复盘
        """
        print(f"\n{'#'*60}")
        print(f"# 盘后复盘系统启动 - {self.today}")
        print(f"# 待分析基金数量: {len(self.funds)}")
        print(f"{'#'*60}")
        
        reports = []
        for fund in self.funds:
            try:
                report = self.analyze_fund(fund)
                if report:
                    reports.append(report)
            except Exception as e:
                print(f"  ❌ 分析失败: {e}")
                reports.append(f"## {fund.get('name')} 复盘失败\n错误: {str(e)}")
        
        return "\n\n---\n\n".join(reports)

    def run_one(self, fund_code: str) -> str:
        """
        运行指定基金的盘后复盘
        """
        target_fund = next((f for f in self.funds if f["code"] == fund_code), None)
        if not target_fund:
            return f"Error: Fund with code {fund_code} not found in configuration."
        
        return self.analyze_fund(target_fund)


if __name__ == "__main__":
    analyst = PostMarketAnalyst()
    print(analyst.run_all())
