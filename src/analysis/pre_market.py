"""
Pre-Market Analyst - 专业级盘前情报系统
=====================================
模拟专业基金经理团队的盘前研究流程：
1. 全球宏观信号收集（隔夜美股、A50、汇率）
2. 北向资金与行业资金流向
3. 重仓股深度监控（公告、研报、风险）
4. 行业政策与产业链动态
5. 信号汇总与交叉验证
"""

import json
import sys
import os
from typing import List, Dict, Optional
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import FUNDS_FILE
from src.data_sources.akshare_api import (
    get_fund_holdings,
    get_market_indices,
    get_global_macro_summary,
    get_northbound_flow,
    get_industry_capital_flow,
    get_sector_performance,
    get_concept_board_performance,
    get_stock_realtime_quote
)
from src.data_sources.web_search import WebSearch
from src.llm.client import get_llm_client
from src.llm.prompts import PRE_MARKET_PROMPT_TEMPLATE


class PreMarketAnalyst:
    """
    专业级盘前分析师
    模拟基金经理团队的晨会研究流程
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
            'category': category,  # e.g., '宏观新闻', '持仓公告', '研报', '政策'
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
        output.append("- AkShare: A股指数、北向资金、行业资金流向")
        output.append("- 东方财富: 基金持仓数据")
        output.append("- Tavily Search API: 实时新闻与研报搜索")
        
        return "\n".join(output)

    # =========================================================================
    # Layer 1: 全球宏观数据收集
    # =========================================================================
    
    def collect_global_macro(self) -> str:
        """收集全球宏观数据：美股、A50、汇率"""
        print("  📡 收集全球宏观信号...")
        
        macro_data = get_global_macro_summary()
        
        # 格式化输出
        output = []
        
        # 美股市场
        if macro_data.get("美股市场"):
            output.append("**隔夜美股:**")
            for name, data in macro_data["美股市场"].items():
                if isinstance(data, dict):
                    price = data.get('最新价', data.get('收盘', 'N/A'))
                    change = data.get('涨跌幅', data.get('涨跌', 'N/A'))
                    output.append(f"- {name}: {price} ({change})")
        
        # A50期货 / 亚太指数
        if macro_data.get("A50期货"):
            a50_data = macro_data["A50期货"]
            if isinstance(a50_data, dict):
                # 检查是否是旧格式（直接有收盘字段）还是新格式（多个指数）
                if '说明' in a50_data:
                    output.append(f"\n**亚太市场:** {a50_data.get('说明', 'N/A')}")
                elif '收盘' in a50_data:
                    # 旧格式
                    output.append("\n**富时A50期货:**")
                    output.append(f"- 最新: {a50_data.get('收盘', 'N/A')}")
                    if '夜盘涨跌幅' in a50_data:
                        output.append(f"- 夜盘涨跌: {a50_data['夜盘涨跌幅']}%")
                else:
                    # 新格式：多个亚太指数
                    output.append("\n**亚太市场指数:**")
                    for idx_name, idx_data in a50_data.items():
                        if isinstance(idx_data, dict):
                            price = idx_data.get('最新价', 'N/A')
                            change = idx_data.get('涨跌幅', 'N/A')
                            if change != 'N/A':
                                change = f"{change}%" if not str(change).endswith('%') else change
                            output.append(f"- {idx_name}: {price} ({change})")
        
        # 汇率
        if macro_data.get("汇率"):
            output.append("\n**汇率:**")
            for name, data in macro_data["汇率"].items():
                if isinstance(data, dict):
                    rate = data.get('买入价', data.get('最新价', 'N/A'))
                    output.append(f"- {name}: {rate}")
        
        # 补充：搜索宏观事件新闻
        print("  📡 搜索隔夜宏观事件...")
        macro_news = self.web_search.search_macro_events(max_results=3)
        if macro_news:
            output.append("\n**隔夜重要事件:**")
            for news in macro_news:
                title = news.get('title', news.get('content', '')[:100])
                output.append(f"- {title}")
                # 追踪来源
                self._add_source(
                    category="🌍 宏观新闻",
                    title=title,
                    url=news.get('url'),
                    source_name=news.get('source', 'Web Search')
                )
        
        return "\n".join(output) if output else "全球宏观数据暂时无法获取"

    # =========================================================================
    # Layer 2: 资金流向分析
    # =========================================================================
    
    def collect_capital_flow(self, fund_focus: List[str]) -> tuple:
        """收集北向资金和行业资金流向"""
        print("  💰 分析资金流向...")
        
        # 北向资金
        northbound = get_northbound_flow()
        nb_output = []
        if northbound:
            if northbound.get('最新净流入'):
                latest = northbound['最新净流入']
                nb_output.append(f"**最新北向资金:** {latest}")
            if northbound.get('5日累计净流入'):
                nb_output.append(f"**5日累计:** {northbound['5日累计净流入']}亿")
        
        northbound_str = "\n".join(nb_output) if nb_output else "北向资金数据暂无"
        
        # 行业资金流向
        sector_flow = get_industry_capital_flow()
        sector_output = []
        if sector_flow.get('行业资金流向Top10'):
            sector_output.append("**行业资金流向Top10:**")
            for item in sector_flow['行业资金流向Top10'][:5]:
                if isinstance(item, dict):
                    name = item.get('名称', 'N/A')
                    flow = item.get('今日主力净流入', item.get('主力净流入', 'N/A'))
                    sector_output.append(f"- {name}: {flow}")
        
        # 查找基金关注的行业
        for focus in fund_focus[:2]:
            industry_data = get_industry_capital_flow(focus)
            if industry_data and isinstance(industry_data, dict) and '名称' in industry_data:
                sector_output.append(f"\n**{focus}板块资金:** {industry_data}")
        
        sector_str = "\n".join(sector_output) if sector_output else "行业资金流向数据暂无"
        
        return northbound_str, sector_str

    # =========================================================================
    # Layer 3: 持仓股深度分析
    # =========================================================================
    
    def collect_holdings_data(self, fund_code: str) -> tuple:
        """收集持仓数据和深度信息"""
        print("  📊 获取基金持仓...")
        
        holdings_df = get_fund_holdings(fund_code)
        
        if holdings_df.empty:
            return "持仓数据暂无", "持仓深度信息暂无", []
        
        # 提取持仓基本信息
        holdings_output = []
        name_col = next((col for col in holdings_df.columns if '名称' in col), None)
        code_col = next((col for col in holdings_df.columns if '代码' in col), None)
        ratio_col = next((col for col in holdings_df.columns if '比例' in col), None)
        
        # 获取最新一期持仓（通常按季度）
        if '季度' in holdings_df.columns:
            latest_quarter = holdings_df['季度'].iloc[0]
            holdings_df = holdings_df[holdings_df['季度'] == latest_quarter]
        
        top_holdings = holdings_df.head(10)
        holdings_list = []
        
        holdings_output.append(f"**最新持仓（Top 10）:**")
        for _, row in top_holdings.iterrows():
            name = row.get(name_col, 'N/A') if name_col else 'N/A'
            code = row.get(code_col, '') if code_col else ''
            ratio = row.get(ratio_col, 'N/A') if ratio_col else 'N/A'
            holdings_output.append(f"- {name}({code}): {ratio}%")
            if name != 'N/A':
                holdings_list.append({'name': name, 'code': str(code)})
        
        holdings_str = "\n".join(holdings_output)
        

        # 深度分析Top 5持仓
        print("  🔍 深度分析重仓股...")
        deep_dive_output = []
        
        for holding in holdings_list[:5]:
            stock_name = holding['name']
            stock_code = holding['code']
            
            deep_dive_output.append(f"\n**{stock_name}:**")
            
            # 分层搜索
            search_results = self.web_search.comprehensive_stock_search(stock_name)
            
            # 公告
            if search_results.get('announcements'):
                deep_dive_output.append("  *公告:*")
                for ann in search_results['announcements'][:2]:
                    title = ann.get('title', ann.get('content', ''))[:80]
                    deep_dive_output.append(f"    - {title}")
                    # 追踪来源
                    self._add_source(
                        category="📢 公司公告",
                        title=f"[{stock_name}] {title}",
                        url=ann.get('url'),
                        source_name=ann.get('source', 'Web Search')
                    )
            
            # 研报
            if search_results.get('analyst_reports'):
                deep_dive_output.append("  *研报/评级:*")
                for report in search_results['analyst_reports'][:2]:
                    title = report.get('title', report.get('content', ''))[:80]
                    deep_dive_output.append(f"    - {title}")
                    # 追踪来源
                    self._add_source(
                        category="📊 研究报告",
                        title=f"[{stock_name}] {title}",
                        url=report.get('url'),
                        source_name=report.get('source', 'Web Search')
                    )
            
            # 风险
            if search_results.get('risk_events'):
                deep_dive_output.append("  *风险监控:*")
                for risk in search_results['risk_events'][:1]:
                    title = risk.get('title', risk.get('content', ''))[:80]
                    deep_dive_output.append(f"    - {title}")
                    # 追踪来源
                    self._add_source(
                        category="⚠️ 风险事件",
                        title=f"[{stock_name}] {title}",
                        url=risk.get('url'),
                        source_name=risk.get('source', 'Web Search')
                    )
        
        deep_dive_str = "\n".join(deep_dive_output) if deep_dive_output else "持仓深度分析暂无"
        
        return holdings_str, deep_dive_str, holdings_list

    # =========================================================================
    # Layer 4: 行业政策分析
    # =========================================================================
    
    def collect_policy_news(self, fund_focus: List[str]) -> str:
        """收集行业政策新闻"""
        print("  📰 搜索行业政策...")
        
        policy_output = []
        
        for industry in fund_focus[:3]:
            print(f"    - 搜索 {industry} 政策...")
            news = self.web_search.search_policy_news(industry, max_results=2)
            
            if news:
                policy_output.append(f"**{industry}:**")
                for item in news:
                    title = item.get('title', item.get('content', ''))[:100]
                    confidence = item.get('confidence', 'MEDIUM')
                    policy_output.append(f"- [{confidence}] {title}")
                    # 追踪来源
                    self._add_source(
                        category="📜 行业政策",
                        title=f"[{industry}] {title}",
                        url=item.get('url'),
                        source_name=item.get('source', 'Web Search')
                    )
                policy_output.append("")
        
        return "\n".join(policy_output) if policy_output else "暂无相关行业政策新闻"

    # =========================================================================
    # 主分析流程
    # =========================================================================
    
    def analyze_fund(self, fund: Dict) -> str:
        """
        单只基金的完整盘前分析流程
        """
        fund_code = fund.get("code")
        fund_name = fund.get("name")
        fund_style = fund.get("style", "混合型")
        fund_focus = fund.get("focus", [])
        
        print(f"\n{'='*60}")
        print(f"🔍 分析基金: {fund_name} ({fund_code})")
        print(f"{'='*60}")
        
        # 重置来源追踪
        self._reset_sources()
        
        # Step 1: 全球宏观
        global_macro = self.collect_global_macro()
        
        # Step 2: 资金流向
        northbound_data, sector_flow_data = self.collect_capital_flow(fund_focus)
        
        # Step 3: 持仓分析
        holdings_data, holdings_deep_dive, holdings_list = self.collect_holdings_data(fund_code)
        
        # Step 4: 行业政策
        policy_news = self.collect_policy_news(fund_focus)
        
        print(" 收集到的行业政策信息：", policy_news)

        # Step 5: 构建Prompt并调用LLM
        print("  🤖 AI 综合研判中...")
        
        prompt = PRE_MARKET_PROMPT_TEMPLATE.format(
            fund_name=fund_name,
            fund_code=fund_code,
            fund_style=fund_style,
            fund_focus=", ".join(fund_focus) if fund_focus else "综合",
            global_macro_data=global_macro,
            northbound_data=northbound_data,
            sector_flow_data=sector_flow_data,
            holdings_data=holdings_data,
            holdings_deep_dive=holdings_deep_dive,
            policy_news=policy_news,
            report_date=self.today  # 传入实际日期
        )
        
        # 调用LLM生成报告
        report = self.llm.generate_content(prompt)
        
        # 附加数据来源
        sources_section = self._format_sources()
        if sources_section:
            report = report + sources_section
        
        print(f"  📚 收集到 {len(self.sources)} 个数据来源")
        print("  ✅ 分析完成")
        return report

    def run_all(self) -> str:
        """
        运行所有基金的盘前分析
        """
        print(f"\n{'#'*60}")
        print(f"# 盘前情报系统启动 - {self.today}")
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
                reports.append(f"## {fund.get('name')} 分析失败\n错误: {str(e)}")
        
        return "\n\n---\n\n".join(reports)

    def run_one(self, fund_code: str) -> str:
        """
        运行指定基金的盘前分析
        """
        target_fund = next((f for f in self.funds if f["code"] == fund_code), None)
        if not target_fund:
            return f"Error: Fund with code {fund_code} not found in configuration."
        
        return self.analyze_fund(target_fund)


if __name__ == "__main__":
    analyst = PreMarketAnalyst()
    print(analyst.run_all())
