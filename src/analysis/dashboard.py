import akshare as ak
import pandas as pd
import yfinance as yf
import os
import glob
from datetime import datetime, timedelta
from typing import Dict, Any, List
import time
import threading
import concurrent.futures

# Cache Setup
_DASHBOARD_CACHE = {}
_DASHBOARD_CACHE_LOCK = threading.Lock()
_DEFAULT_CACHE_TTL = 300  # 5 minutes

class DashboardService:
    def __init__(self, report_dir: str):
        self.report_dir = report_dir

    def _get_cached_data(self, key: str, ignore_expiry: bool = False):
        with _DASHBOARD_CACHE_LOCK:
            if key in _DASHBOARD_CACHE:
                data, expiry = _DASHBOARD_CACHE[key]
                if ignore_expiry or time.time() < expiry:
                    return data
                else:
                    del _DASHBOARD_CACHE[key]
        return None

    def _set_cached_data(self, key: str, data: Any, duration: int = _DEFAULT_CACHE_TTL):
        with _DASHBOARD_CACHE_LOCK:
            _DASHBOARD_CACHE[key] = (data, time.time() + duration)

    def _is_china_market_open(self) -> bool:
        """Check if current time is between 09:30 and 15:00"""
        now = datetime.now()
        hm = now.hour * 100 + now.minute
        return 930 <= hm < 1500

    def get_market_overview(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Section 1: Market Breadth, Indices, Turnover"""
        cache_key = "market_overview"
        # If market closed, use cache indefinitely (ignore expiry)
        ignore_expiry = not self._is_china_market_open()
        
        if not force_refresh:
            cached = self._get_cached_data(cache_key, ignore_expiry=ignore_expiry)
            if cached: return cached

        data = {
            "indices": [],
            "breadth": {"up": 0, "down": 0, "flat": 0, "limit_up": 0, "limit_down": 0},
            "turnover": {"total": 0, "change_pct": 0, "change_amt": 0},
            "main_flow": 0
        }

        try:
            # 1. Indices - MOVED to separate API (get_market_indices)
            # We no longer fetch them here to speed up the main dashboard load.
            data["indices"] = []
            
            # 2. Turnover & Breadth
            # Breadth via Legu (Fast)
            try:
                legu_df = ak.stock_market_activity_legu()
                if not legu_df.empty:
                    # Convert to dict {item: value}
                    legu_map = dict(zip(legu_df['item'], legu_df['value']))
                    data["breadth"] = {
                        "up": int(float(legu_map.get("上涨", 0))),
                        "down": int(float(legu_map.get("下跌", 0))),
                        "flat": int(float(legu_map.get("平盘", 0))),
                        "limit_up": int(float(legu_map.get("涨停", 0))),
                        "limit_down": int(float(legu_map.get("跌停", 0)))
                    }
                
                # df_spot = ak.stock_zh_a_spot_em()
                # if df_spot is not None and not df_spot.empty:
                #     up_count = len(df_spot[df_spot['涨跌幅'] > 0])
                #     down_count = len(df_spot[df_spot['涨跌幅'] < 0])
                #     flat_count = len(df_spot[df_spot['涨跌幅'] == 0])
                #     limit_up = len(df_spot[df_spot['涨跌幅'] >= 9.8]) # 粗略统计
                #     limit_down = len(df_spot[df_spot['涨跌幅'] <= -9.8])

                #     data["breadth"] = {
                #         "up": up_count,
                #         "down": down_count,
                #         "flat": flat_count,
                #         "limit_up": limit_up,
                #         "limit_down": limit_down
                #     }
            except Exception as e:
                print(f"stock_zh_a_spot_em fetch failed: {e}")

            # Turnover via Specific Daily Indices (SH Composite + SZ Composite)
            # Much faster than fetching all spot indices
            try:
                # sh000001 = SH Composite, sz399106 = SZ Composite
                sh_df = ak.stock_zh_index_daily_em(symbol="sh000001")
                sz_df = ak.stock_zh_index_daily_em(symbol="sz399106")
                
                total_to = 0
                if not sh_df.empty:
                    total_to += float(sh_df.iloc[-1]['amount'])
                if not sz_df.empty:
                    total_to += float(sz_df.iloc[-1]['amount'])
                
                if total_to > 0:
                     # Convert to Billions (Yi)
                    data["turnover"]["total"] = round(total_to / 100000000, 2)
            except Exception as e:
                print(f"Turnover fetch failed: {e}")
                
            # 3. Main Capital Flow
            # stock_individual_fund_flow_rank gives individual flows, sum top?
            # Or market level flow: stock_market_fund_flow
            try:
                flow_df = ak.stock_market_fund_flow()
                if not flow_df.empty:
                    # Usually returns historical data. Get last row
                    last = flow_df.iloc[-1]
                    val = last.get('主力净流入-净额', 0)
                    try:
                        if str(val).strip() == '-':
                            val = 0.0
                        else:
                            val = float(val)
                    except:
                        val = 0.0
                    data["main_flow"] = round(val / 100000000, 2)
            except:
                pass
                
        except Exception as e:
            print(f"Error fetching market overview: {e}")

        self._set_cached_data(cache_key, data)
        return data

    def get_gold_macro(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Section 2: Gold & Macro (YFinance)"""
        cache_key = "gold_macro"
        if not force_refresh:
            cached = self._get_cached_data(cache_key)
            if cached: return cached
        
        data = {"symbol": "GC=F", "price": 0, "change_pct": 0, "dxy": 0}
        try:
            # Gold
            gold = yf.Ticker("GC=F")
            hist = gold.history(period="2d")
            if not hist.empty:
                last = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else last
                data["price"] = round(last['Close'], 2)
                data["change_pct"] = round(((last['Close'] - prev['Close']) / prev['Close']) * 100, 2)
            
            # DXY
            dxy = yf.Ticker("DX-Y.NYB")
            hist_dxy = dxy.history(period="1d")
            if not hist_dxy.empty:
                data["dxy"] = round(hist_dxy.iloc[-1]['Close'], 2)
                
        except Exception as e:
            print(f"Error fetching gold/macro: {e}")
            
        self._set_cached_data(cache_key, data)
        return data

    def get_sectors(self, force_refresh: bool = False) -> Dict[str, List]:
        """Section 3: Sector Performance"""
        cache_key = "sectors"
        ignore_expiry = not self._is_china_market_open()
        
        if not force_refresh:
            cached = self._get_cached_data(cache_key, ignore_expiry=ignore_expiry)
            if cached: return cached
        
        result = {"gainers": [], "losers": []}
        try:
            df = ak.stock_board_industry_name_em()
            if not df.empty:
                # Sort by change
                sorted_df = df.sort_values(by='涨跌幅', ascending=False)
                
                # Top 10 Gainers
                for _, row in sorted_df.head(10).iterrows():
                    result["gainers"].append({
                        "name": row['板块名称'],
                        "change": row['涨跌幅'],
                        "flow": 0 # EM name API doesn't have flow, need merge or ignore
                    })
                
                # Top 10 Losers
                for _, row in sorted_df.tail(10).iterrows():
                    result["losers"].append({
                        "name": row['板块名称'],
                        "change": row['涨跌幅'],
                        "flow": 0
                    })
        except Exception as e:
            print(f"Error fetching sectors: {e}")
            
        self._set_cached_data(cache_key, result)
        return result

    def get_abnormal_movements(self, force_refresh: bool = False) -> List[Dict]:
        """Section 4: Abnormal Movements (Stock Level Feed)"""
        cache_key = "abnormal_feed"
        ignore_expiry = not self._is_china_market_open()
        
        if not force_refresh:
            cached = self._get_cached_data(cache_key, ignore_expiry=ignore_expiry)
            if cached: return cached
        
        moves = []
        try:
            # Fetch various types of real-time signals
            # Rocket (Rapid Rise), Dive (Rapid Fall), Limit Up, Limit Down
            targets = [
                ("火箭发射", "🚀 拉升"), 
                ("高台跳水", "📉 跳水"),
                ("封涨停板", "🔴 封涨停"),
                ("封跌停板", "🟢 封跌停")
            ]
            
            for symbol, label in targets:
                try:
                    df = ak.stock_changes_em(symbol=symbol)
                    if not df.empty:
                        # Normalize columns if needed, usually they are consistent
                        for _, row in df.head(10).iterrows(): # Take top 10 of each type
                            moves.append({
                                "time": str(row.get('时间', '')),
                                "name": row.get('名称', ''),
                                "type": label,
                                "info": f"Code: {row.get('代码')}"
                            })
                except Exception as sub_e:
                    print(f"Failed to fetch {symbol}: {sub_e}")

            # Sort by time descending (HH:MM:SS)
            # Filter out empty times just in case
            moves = [m for m in moves if m['time']]
            moves.sort(key=lambda x: x['time'], reverse=True)
            
        except Exception as e:
            print(f"Error fetching abnormal movements: {e}")
            
        # Cache for 30 seconds
        result = moves[:30]
        self._set_cached_data(cache_key, result, duration=30)
        return result

    def get_top_holdings_changes(self, force_refresh: bool = False) -> List[Dict]:
        """Section 5: Top Capital Flow Stocks"""
        cache_key = "top_flow"
        ignore_expiry = not self._is_china_market_open()
        
        if not force_refresh:
            cached = self._get_cached_data(cache_key, ignore_expiry=ignore_expiry)
            if cached: return cached
        
        stocks = []
        try:
            # Main capital flow rank
            df = ak.stock_individual_fund_flow_rank(indicator="今日")
            if not df.empty:
                # Top 10 inflow
                for _, row in df.head(10).iterrows():
                    net_buy_val = row.get('今日主力净流入-净额', 0)
                    try:
                        if str(net_buy_val).strip() == '-':
                             net_buy_float = 0.0
                        else:
                             net_buy_float = float(net_buy_val)
                    except (ValueError, TypeError):
                        net_buy_float = 0.0
                        
                    stocks.append({
                        "code": str(row.get('代码')),
                        "name": row.get('名称'),
                        "net_buy": round(net_buy_float / 100000000, 2), # Billions? usually units vary
                        "change_pct": row.get('今日涨跌幅')
                    })
        except Exception as e:
            print(f"Error flow: {e}")
            
        self._set_cached_data(cache_key, stocks)
        return stocks

    def get_system_stats(self, user_report_dir: str = None) -> Dict[str, Any]:
        """Section 6: Report Generation Stats (Today) - User Specific"""
        # If no user_report_dir provided, use default (but this should be avoided for multi-tenant)
        target_dir = user_report_dir if user_report_dir else self.report_dir
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        stats = {
            "total": 0,
            "breakdown": {"pre": 0, "post": 0, "commodity": 0, "sentiment": 0},
            "latest": None
        }
        
        # Recursive search for .md files
        # Directories: reports/, reports/commodities/, reports/sentiment/
        # Pattern: YYYY-MM-DD*.md
        
        all_files = []
        
        if os.path.exists(target_dir):
            # Root reports (Pre/Post)
            root_files = glob.glob(os.path.join(target_dir, f"{today_str}*.md"))
            all_files.extend([(f, 'root') for f in root_files])
            
            # Commodity
            comm_files = glob.glob(os.path.join(target_dir, "commodities", f"{today_str}*.md"))
            all_files.extend([(f, 'commodity') for f in comm_files])
            
            # Sentiment (Format: sentiment_YYYYMMDD...)
            sent_date = datetime.now().strftime("%Y%m%d")
            sent_files = glob.glob(os.path.join(target_dir, "sentiment", f"sentiment_{sent_date}*.md"))
            all_files.extend([(f, 'sentiment') for f in sent_files])
        
        stats["total"] = len(all_files)
        
        # Sort by mtime
        if all_files:
            all_files.sort(key=lambda x: os.path.getmtime(x[0]), reverse=True)
            stats["latest"] = os.path.basename(all_files[0][0])
            
            for f, loc in all_files:
                fname = os.path.basename(f)
                if loc == 'commodity':
                    stats["breakdown"]["commodity"] += 1
                elif loc == 'sentiment':
                    stats["breakdown"]["sentiment"] += 1
                elif "_pre_" in fname:
                    stats["breakdown"]["pre"] += 1
                elif "_post_" in fname:
                    stats["breakdown"]["post"] += 1
                    
        return stats

    def get_full_dashboard(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Aggregate all GLOBAL data with parallelism"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_overview = executor.submit(self.get_market_overview, force_refresh)
            future_gold = executor.submit(self.get_gold_macro, force_refresh)
            future_sectors = executor.submit(self.get_sectors, force_refresh)
            future_abnormal = executor.submit(self.get_abnormal_movements, force_refresh)
            future_flows = executor.submit(self.get_top_holdings_changes, force_refresh)

            return {
                "market_overview": future_overview.result(),
                "gold_macro": future_gold.result(),
                "sectors": future_sectors.result(),
                "abnormal_movements": future_abnormal.result(),
                "top_flows": future_flows.result(),
                # System stats removed from global cache
            }
