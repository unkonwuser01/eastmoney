"""
Stock Analysis Strategy - 个股分析策略
基本面为主，技术面为辅
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import akshare as ak
from .base_strategy import AnalysisStrategy
from src.data_sources.akshare_api import (
    get_stock_realtime_quote,
    get_stock_history,
    get_stock_announcement,
    get_stock_news_sentiment,
    get_global_macro_summary,
    get_northbound_flow,
    get_industry_capital_flow,
    get_sector_performance,
    get_sector_performance_ths,
    get_concept_board_performance,
)
from src.data_sources.technical_analysis import BasicTechnicalAnalysis, format_technical_analysis


class StockStrategy(AnalysisStrategy):
    """
    个股分析策略 - 基本面为主，技术面为辅
    支持盘前分析和盘后复盘
    """

    def __init__(self, stock_info: Dict[str, Any], llm_client, web_search):
        super().__init__(stock_info, llm_client, web_search)
        self.stock_code = stock_info.get("code")
        self.stock_name = stock_info.get("name")
        self.sector = stock_info.get("sector", "")
        self.market = stock_info.get("market", "")

    def collect_data(self, mode: str) -> Dict[str, Any]:
        """采集数据入口"""
        data = {}

        if mode == 'pre':
            # 盘前分析 - 基本面为主
            data['fundamentals'] = self._collect_fundamentals()
            data['announcements'] = self._collect_announcements()
            data['research_reports'] = self._collect_research_reports()
            data['news_sentiment'] = self._collect_news_sentiment()
            data['industry_analysis'] = self._collect_industry_analysis()
            data['northbound_holdings'] = self._collect_northbound_holdings()
            data['technical_basic'] = self._collect_basic_technicals()
            data['global_macro'] = self._collect_global_macro()

        elif mode == 'post':
            # 盘后复盘
            data['intraday_performance'] = self._collect_intraday_performance()
            data['volume_analysis'] = self._collect_volume_analysis()
            data['capital_flow'] = self._collect_capital_flow()
            data['dragon_tiger'] = self._collect_dragon_tiger()
            data['sector_comparison'] = self._collect_sector_comparison()
            data['intraday_news'] = self._collect_intraday_news()
            data['technical_basic'] = self._collect_basic_technicals()

        return data

    def generate_report(self, mode: str, data: Dict[str, Any]) -> str:
        """使用LLM生成分析报告"""
        today = datetime.now().strftime("%Y-%m-%d")

        if mode == 'pre':
            prompt = self._build_pre_market_prompt(data, today)
        else:
            prompt = self._build_post_market_prompt(data, today)

        report = self.llm.generate_content(prompt)
        return report + self.get_sources()

    # ==========================
    # 盘前数据采集方法 (Pre-Market)
    # ==========================

    def _collect_fundamentals(self) -> Dict:
        """采集基本面数据：PE、PB、市值、ROE等"""
        print(f"  📊 Collecting Fundamentals for {self.stock_name}...")
        try:
            quote = get_stock_realtime_quote(self.stock_code)

            # 获取更详细的基本面数据
            df_info = ak.stock_individual_info_em(symbol=self.stock_code)
            info_map = dict(zip(df_info['item'], df_info['value'])) if not df_info.empty else {}

            return {
                "current_price": quote.get('最新价') if quote else 'N/A',
                "prev_close": quote.get('昨收') if quote else 'N/A',
                "change_pct": quote.get('涨跌幅') if quote else 'N/A',
                "pe_ttm": info_map.get("市盈率(动态)", "N/A"),
                "pb": info_map.get("市净率", "N/A"),
                "market_cap": info_map.get("总市值", "N/A"),
                "float_cap": info_map.get("流通市值", "N/A"),
                "industry": info_map.get("行业", self.sector),
                "roe": info_map.get("净资产收益率", "N/A"),
                "total_shares": info_map.get("总股本", "N/A"),
                "float_shares": info_map.get("流通股", "N/A"),
            }
        except Exception as e:
            print(f"    Error collecting fundamentals: {e}")
            return {"error": str(e)}

    def _collect_announcements(self) -> List[Dict]:
        """采集最新公告（高优先级）"""
        print(f"  📢 Collecting Announcements for {self.stock_name}...")
        announcements = []

        # 方法1: AkShare API
        try:
            ak_announcements = get_stock_announcement(self.stock_code, self.stock_name)
            if ak_announcements:
                for a in ak_announcements[:5]:
                    announcements.append(a)
                    self._add_source("公告", a.get('标题', a.get('title', '公告')),
                                    a.get('url', ''), "东方财富")
        except Exception as e:
            print(f"    AkShare announcements error: {e}")

        # 方法2: Web搜索补充
        try:
            web_results = self.web_search.search_news(f"{self.stock_name} 公告", max_results=3)
            for r in web_results:
                self._add_source("公告", r.get('title'), r.get('url'))
                announcements.append({
                    'title': r.get('title'),
                    'url': r.get('url'),
                    'source': 'web'
                })
        except Exception as e:
            print(f"    Web search announcements error: {e}")

        return announcements[:8]

    def _collect_research_reports(self) -> List[Dict]:
        """采集卖方研报/评级"""
        print(f"  📑 Collecting Research Reports for {self.stock_name}...")
        reports = []

        try:
            # 搜索研报
            results = self.web_search.search_news(f"{self.stock_name} 研报 评级", max_results=5)
            for r in results:
                self._add_source("研报", r.get('title'), r.get('url'))
                reports.append({
                    'title': r.get('title'),
                    'url': r.get('url'),
                    'snippet': r.get('snippet', r.get('content', ''))[:200]
                })
        except Exception as e:
            print(f"    Research reports error: {e}")

        return reports

    def _collect_news_sentiment(self) -> Dict:
        """采集新闻及情绪分析"""
        print(f"  📰 Collecting News for {self.stock_name}...")

        em_news = []
        web_news = []

        # AkShare 新闻
        try:
            em_news = get_stock_news_sentiment(self.stock_name)
            for n in em_news[:5]:
                self._add_source("新闻", n.get('标题', n.get('title', '')),
                                n.get('url', n.get('新闻链接', '')), "东方财富")
        except Exception as e:
            print(f"    EM news error: {e}")

        # Web 搜索新闻
        try:
            web_news = self.web_search.search_news(f"{self.stock_name} 最新消息", max_results=5)
            for n in web_news:
                self._add_source("新闻", n.get('title'), n.get('url'))
        except Exception as e:
            print(f"    Web news error: {e}")

        return {
            "em_news": em_news[:5],
            "web_news": web_news
        }

    def _collect_industry_analysis(self) -> Dict:
        """采集行业关联和产业链数据"""
        print(f"  🏭 Collecting Industry Analysis for {self.sector}...")
        result = {
            "sector_performance": {},
            "concept_boards": [],
            "industry_chain": [],
            "policy": []
        }

        try:
            # 行业板块表现
            if self.sector:
                sector_data = get_sector_performance_ths(self.sector)
                if not sector_data:
                    sector_data = get_sector_performance(self.sector)
                result["sector_performance"] = sector_data or {}
        except Exception as e:
            print(f"    Sector performance error: {e}")

        try:
            # 概念板块
            concepts = get_concept_board_performance()
            if concepts and isinstance(concepts, dict):
                result["concept_boards"] = concepts.get("概念板块Top10", [])[:5]
        except Exception as e:
            print(f"    Concept boards error: {e}")

        try:
            # 产业链新闻
            if self.sector:
                chain_news = self.web_search.search_news(f"{self.sector} 产业链", max_results=3)
                for n in chain_news:
                    self._add_source("产业链", n.get('title'), n.get('url'))
                result["industry_chain"] = chain_news
        except Exception as e:
            print(f"    Industry chain error: {e}")

        try:
            # 政策新闻
            if self.sector:
                policy_news = self.web_search.search_news(f"{self.sector} 政策", max_results=3)
                for n in policy_news:
                    self._add_source("政策", n.get('title'), n.get('url'))
                result["policy"] = policy_news
        except Exception as e:
            print(f"    Policy news error: {e}")

        return result

    def _collect_northbound_holdings(self) -> Dict:
        """采集北向资金持仓变化"""
        print(f"  🌏 Collecting Northbound Holdings for {self.stock_code}...")
        result = {
            "market_flow": {},
            "individual_holdings": {}
        }

        # 整体北向资金流向
        try:
            nb = get_northbound_flow()
            result["market_flow"] = {
                "latest": nb.get('最新净流入', 'N/A'),
                "5d_total": nb.get('5日累计净流入', 'N/A'),
                "date": nb.get('数据日期', 'N/A')
            }
        except Exception as e:
            print(f"    Northbound flow error: {e}")

        # 个股北向持仓 (如果有接口)
        try:
            df = ak.stock_hsgt_individual_em(symbol=self.stock_code)
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                result["individual_holdings"] = {
                    "holding_shares": latest.get("持股数量", "N/A"),
                    "holding_ratio": latest.get("持股占比", "N/A"),
                    "change": latest.get("持股数量变化", "N/A"),
                    "date": str(latest.get("日期", "N/A"))
                }
        except Exception as e:
            # 这个接口可能不是所有股票都有数据
            pass

        return result

    def _collect_basic_technicals(self) -> str:
        """采集基础技术指标"""
        print(f"  📈 Collecting Technical Analysis for {self.stock_code}...")
        try:
            analyzer = BasicTechnicalAnalysis(self.stock_code)
            analysis = analyzer.analyze()
            return format_technical_analysis(analysis)
        except Exception as e:
            print(f"    Technical analysis error: {e}")
            return f"技术分析失败: {str(e)}"

    def _collect_global_macro(self) -> str:
        """采集全球宏观环境"""
        print(f"  🌍 Collecting Global Macro Signals...")
        try:
            macro_data = get_global_macro_summary()
            output = []

            if macro_data.get("美股市场"):
                output.append("**隔夜美股:**")
                for name, d in macro_data["美股市场"].items():
                    if isinstance(d, dict):
                        output.append(f"- {name}: {d.get('最新价', 'N/A')} ({d.get('涨跌幅', 'N/A')})")

            if macro_data.get("汇率"):
                output.append("\n**汇率:**")
                for name, d in macro_data["汇率"].items():
                    if isinstance(d, dict):
                        output.append(f"- {name}: {d.get('买入价', d.get('最新价', 'N/A'))}")

            return "\n".join(output) if output else "暂无宏观数据"
        except Exception as e:
            print(f"    Macro data error: {e}")
            return "宏观数据获取失败"

    # ==========================
    # 盘后数据采集方法 (Post-Market)
    # ==========================

    def _collect_intraday_performance(self) -> Dict:
        """采集当日交易数据"""
        print(f"  📊 Collecting Intraday Performance for {self.stock_name}...")
        try:
            quote = get_stock_realtime_quote(self.stock_code)
            if not quote:
                return {"error": "无法获取行情数据"}

            return {
                "open": quote.get('今开'),
                "high": quote.get('最高'),
                "low": quote.get('最低'),
                "close": quote.get('最新价'),
                "prev_close": quote.get('昨收'),
                "change_pct": quote.get('涨跌幅'),
                "change_amount": quote.get('涨跌额'),
                "volume": quote.get('成交量'),
                "turnover": quote.get('成交额'),
                "turnover_rate": quote.get('换手'),
                "amplitude": quote.get('振幅') if quote.get('振幅') else self._calc_amplitude(quote),
                "volume_ratio": quote.get('量比'),
            }
        except Exception as e:
            print(f"    Intraday performance error: {e}")
            return {"error": str(e)}

    def _calc_amplitude(self, quote: Dict) -> Optional[float]:
        """计算振幅"""
        try:
            high = float(quote.get('最高', 0))
            low = float(quote.get('最低', 0))
            prev_close = float(quote.get('昨收', 1))
            if prev_close > 0:
                return round((high - low) / prev_close * 100, 2)
        except:
            pass
        return None

    def _collect_volume_analysis(self) -> Dict:
        """成交量对比分析"""
        print(f"  📊 Analyzing Volume for {self.stock_code}...")
        try:
            history = get_stock_history(self.stock_code, days=20)
            if not history:
                return {"error": "无法获取历史数据"}

            volumes = [h['volume'] for h in history]
            avg_5 = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else 0
            avg_20 = sum(volumes) / len(volumes) if volumes else 0
            today_vol = volumes[-1] if volumes else 0

            volume_status = "正常"
            ratio = today_vol / avg_5 if avg_5 else 1
            if ratio > 2:
                volume_status = "大幅放量"
            elif ratio > 1.5:
                volume_status = "明显放量"
            elif ratio < 0.5:
                volume_status = "大幅缩量"
            elif ratio < 0.7:
                volume_status = "明显缩量"

            return {
                "today_volume": today_vol,
                "avg_5_volume": round(avg_5, 0),
                "avg_20_volume": round(avg_20, 0),
                "volume_ratio_5": round(ratio, 2),
                "volume_status": volume_status
            }
        except Exception as e:
            print(f"    Volume analysis error: {e}")
            return {"error": str(e)}

    def _collect_capital_flow(self) -> Dict:
        """采集主力资金流向"""
        print(f"  💰 Collecting Capital Flow for {self.stock_code}...")
        try:
            # 判断市场
            market = "sh" if self.stock_code.startswith("6") else "sz"
            df = ak.stock_individual_fund_flow(stock=self.stock_code, market=market)

            if df is not None and not df.empty:
                latest = df.iloc[-1]
                return {
                    "main_net_inflow": latest.get("主力净流入-净额", "N/A"),
                    "main_net_inflow_pct": latest.get("主力净流入-净占比", "N/A"),
                    "super_large": latest.get("超大单净流入-净额", "N/A"),
                    "large": latest.get("大单净流入-净额", "N/A"),
                    "medium": latest.get("中单净流入-净额", "N/A"),
                    "small": latest.get("小单净流入-净额", "N/A"),
                    "date": str(latest.get("日期", "N/A"))
                }
        except Exception as e:
            print(f"    Capital flow error: {e}")
        return {}

    def _collect_dragon_tiger(self) -> List[Dict]:
        """采集龙虎榜数据（如有）"""
        print(f"  🐉 Checking Dragon Tiger List for {self.stock_code}...")
        try:
            today = datetime.now().strftime("%Y%m%d")
            df = ak.stock_lhb_detail_em(start_date=today, end_date=today)

            if df is not None and not df.empty:
                stock_data = df[df['代码'] == self.stock_code]
                if not stock_data.empty:
                    return stock_data.to_dict('records')
        except Exception as e:
            print(f"    Dragon tiger error: {e}")
        return []

    def _collect_sector_comparison(self) -> Dict:
        """与板块对比表现"""
        print(f"  🏢 Comparing with Sector {self.sector}...")
        result = {
            "sector_name": self.sector,
            "sector_change": "N/A",
            "relative_strength": "N/A"
        }

        if not self.sector:
            return result

        try:
            sector_data = get_sector_performance_ths(self.sector)
            if sector_data:
                sector_change = sector_data.get("涨跌幅", 0)
                result["sector_change"] = sector_change

                # 获取个股涨跌幅进行对比
                quote = get_stock_realtime_quote(self.stock_code)
                if quote:
                    stock_change = float(quote.get('涨跌幅', 0) or 0)
                    if stock_change > float(sector_change or 0):
                        result["relative_strength"] = "跑赢板块"
                    elif stock_change < float(sector_change or 0):
                        result["relative_strength"] = "跑输板块"
                    else:
                        result["relative_strength"] = "与板块持平"
        except Exception as e:
            print(f"    Sector comparison error: {e}")

        return result

    def _collect_intraday_news(self) -> List[Dict]:
        """采集盘中新闻"""
        print(f"  📰 Collecting Intraday News for {self.stock_name}...")
        news = []

        try:
            results = self.web_search.search_news(f"{self.stock_name} 今日", max_results=5)
            for n in results:
                self._add_source("盘中新闻", n.get('title'), n.get('url'))
                news.append({
                    'title': n.get('title'),
                    'url': n.get('url'),
                    'snippet': n.get('snippet', '')[:150]
                })
        except Exception as e:
            print(f"    Intraday news error: {e}")

        return news

    # ==========================
    # 提示词构建方法
    # ==========================

    def _build_pre_market_prompt(self, data: Dict, today: str) -> str:
        """构建盘前分析提示词"""
        from src.llm.prompts import PRE_MARKET_STOCK_PROMPT_TEMPLATE

        # 格式化各项数据
        fundamentals_str = self._format_fundamentals(data.get('fundamentals', {}))
        announcements_str = self._format_announcements(data.get('announcements', []))
        research_str = self._format_research(data.get('research_reports', []))
        news_str = self._format_news(data.get('news_sentiment', {}))
        industry_str = self._format_industry(data.get('industry_analysis', {}))
        northbound_str = self._format_northbound(data.get('northbound_holdings', {}))
        technical_str = data.get('technical_basic', '暂无技术分析')
        macro_str = data.get('global_macro', '暂无宏观数据')

        return PRE_MARKET_STOCK_PROMPT_TEMPLATE.format(
            stock_name=self.stock_name,
            stock_code=self.stock_code,
            sector=self.sector or "未分类",
            fundamentals_data=fundamentals_str,
            announcements_data=announcements_str,
            research_data=research_str,
            news_data=news_str,
            industry_data=industry_str,
            northbound_data=northbound_str,
            technical_data=technical_str,
            macro_data=macro_str,
            report_date=today
        )

    def _build_post_market_prompt(self, data: Dict, today: str) -> str:
        """构建盘后分析提示词"""
        from src.llm.prompts import POST_MARKET_STOCK_PROMPT_TEMPLATE

        # 格式化各项数据
        intraday_str = self._format_intraday(data.get('intraday_performance', {}))
        volume_str = self._format_volume(data.get('volume_analysis', {}))
        capital_str = self._format_capital_flow(data.get('capital_flow', {}))
        dragon_str = self._format_dragon_tiger(data.get('dragon_tiger', []))
        sector_str = self._format_sector_comparison(data.get('sector_comparison', {}))
        news_str = self._format_intraday_news(data.get('intraday_news', []))
        technical_str = data.get('technical_basic', '暂无技术分析')

        return POST_MARKET_STOCK_PROMPT_TEMPLATE.format(
            stock_name=self.stock_name,
            stock_code=self.stock_code,
            sector=self.sector or "未分类",
            intraday_data=intraday_str,
            volume_data=volume_str,
            capital_flow_data=capital_str,
            dragon_tiger_data=dragon_str,
            sector_comparison_data=sector_str,
            news_data=news_str,
            technical_data=technical_str,
            report_date=today
        )

    # ==========================
    # 数据格式化辅助方法
    # ==========================

    def _format_fundamentals(self, data: Dict) -> str:
        if not data or "error" in data:
            return "基本面数据获取失败"

        lines = [
            f"- 当前价格: {data.get('current_price', 'N/A')}",
            f"- 昨日收盘: {data.get('prev_close', 'N/A')}",
            f"- 涨跌幅: {data.get('change_pct', 'N/A')}%",
            f"- 市盈率(TTM): {data.get('pe_ttm', 'N/A')}",
            f"- 市净率: {data.get('pb', 'N/A')}",
            f"- 总市值: {data.get('market_cap', 'N/A')}",
            f"- 流通市值: {data.get('float_cap', 'N/A')}",
            f"- 所属行业: {data.get('industry', 'N/A')}",
            f"- ROE: {data.get('roe', 'N/A')}",
        ]
        return "\n".join(lines)

    def _format_announcements(self, data: List) -> str:
        if not data:
            return "近期无重要公告"

        lines = []
        for a in data[:5]:
            title = a.get('标题', a.get('title', '公告'))
            lines.append(f"- {title}")
        return "\n".join(lines)

    def _format_research(self, data: List) -> str:
        if not data:
            return "近期无研报"

        lines = []
        for r in data[:5]:
            lines.append(f"- {r.get('title', '研报')}")
            if r.get('snippet'):
                lines.append(f"  摘要: {r.get('snippet')[:100]}...")
        return "\n".join(lines)

    def _format_news(self, data: Dict) -> str:
        lines = []

        em_news = data.get('em_news', [])
        web_news = data.get('web_news', [])

        if em_news:
            for n in em_news[:3]:
                title = n.get('标题', n.get('title', ''))
                if title:
                    lines.append(f"- {title}")

        if web_news:
            for n in web_news[:3]:
                lines.append(f"- {n.get('title', '')}")

        return "\n".join(lines) if lines else "近期无重要新闻"

    def _format_industry(self, data: Dict) -> str:
        lines = []

        # 板块表现
        sector = data.get('sector_performance', {})
        if sector:
            lines.append(f"**板块表现:** {sector.get('板块名称', self.sector)} 涨跌: {sector.get('涨跌幅', 'N/A')}%")

        # 产业链
        chain = data.get('industry_chain', [])
        if chain:
            lines.append("\n**产业链动态:**")
            for c in chain[:3]:
                lines.append(f"- {c.get('title', '')}")

        # 政策
        policy = data.get('policy', [])
        if policy:
            lines.append("\n**相关政策:**")
            for p in policy[:3]:
                lines.append(f"- {p.get('title', '')}")

        return "\n".join(lines) if lines else "暂无行业数据"

    def _format_northbound(self, data: Dict) -> str:
        lines = []

        market = data.get('market_flow', {})
        if market:
            lines.append(f"**北向资金整体:** 今日净流入 {market.get('latest', 'N/A')}亿, 5日累计 {market.get('5d_total', 'N/A')}亿")

        individual = data.get('individual_holdings', {})
        if individual and individual.get('holding_shares'):
            lines.append(f"**个股北向持仓:** 持股 {individual.get('holding_shares')}, 占比 {individual.get('holding_ratio')}, 变化 {individual.get('change')}")

        return "\n".join(lines) if lines else "暂无北向资金数据"

    def _format_intraday(self, data: Dict) -> str:
        if not data or "error" in data:
            return "交易数据获取失败"

        lines = [
            f"- 开盘: {data.get('open', 'N/A')}",
            f"- 最高: {data.get('high', 'N/A')}",
            f"- 最低: {data.get('low', 'N/A')}",
            f"- 收盘: {data.get('close', 'N/A')}",
            f"- 涨跌幅: {data.get('change_pct', 'N/A')}%",
            f"- 成交量: {data.get('volume', 'N/A')}",
            f"- 成交额: {data.get('turnover', 'N/A')}",
            f"- 换手率: {data.get('turnover_rate', 'N/A')}%",
            f"- 振幅: {data.get('amplitude', 'N/A')}%",
            f"- 量比: {data.get('volume_ratio', 'N/A')}",
        ]
        return "\n".join(lines)

    def _format_volume(self, data: Dict) -> str:
        if not data or "error" in data:
            return "成交量分析失败"

        lines = [
            f"- 今日成交量: {data.get('today_volume', 'N/A'):,.0f}" if data.get('today_volume') else "- 今日成交量: N/A",
            f"- 5日均量: {data.get('avg_5_volume', 'N/A'):,.0f}" if data.get('avg_5_volume') else "- 5日均量: N/A",
            f"- 量比(vs 5日): {data.get('volume_ratio_5', 'N/A')}",
            f"- 量能状态: {data.get('volume_status', 'N/A')}",
        ]
        return "\n".join(lines)

    def _format_capital_flow(self, data: Dict) -> str:
        if not data:
            return "资金流向数据暂无"

        lines = [
            f"- 主力净流入: {data.get('main_net_inflow', 'N/A')}",
            f"- 主力净占比: {data.get('main_net_inflow_pct', 'N/A')}",
            f"- 超大单: {data.get('super_large', 'N/A')}",
            f"- 大单: {data.get('large', 'N/A')}",
            f"- 中单: {data.get('medium', 'N/A')}",
            f"- 小单: {data.get('small', 'N/A')}",
        ]
        return "\n".join(lines)

    def _format_dragon_tiger(self, data: List) -> str:
        if not data:
            return "今日未上龙虎榜"

        lines = ["**今日上榜龙虎榜:**"]
        for item in data[:3]:
            lines.append(f"- 上榜原因: {item.get('上榜原因', 'N/A')}")
            lines.append(f"  买入金额: {item.get('买入金额', 'N/A')}, 卖出金额: {item.get('卖出金额', 'N/A')}")
        return "\n".join(lines)

    def _format_sector_comparison(self, data: Dict) -> str:
        if not data or not data.get('sector_name'):
            return "暂无板块对比数据"

        lines = [
            f"- 所属板块: {data.get('sector_name')}",
            f"- 板块涨跌: {data.get('sector_change', 'N/A')}%",
            f"- 相对强度: {data.get('relative_strength', 'N/A')}",
        ]
        return "\n".join(lines)

    def _format_intraday_news(self, data: List) -> str:
        if not data:
            return "今日无重要新闻"

        lines = []
        for n in data[:5]:
            lines.append(f"- {n.get('title', '')}")
        return "\n".join(lines)
