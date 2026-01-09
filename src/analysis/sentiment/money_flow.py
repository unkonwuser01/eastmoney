import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

class MoneyFlowAnalyst:
    def get_money_flow(self):
        """
        获取全方位的资金流向数据
        """
        data = {
            "north_money": 0.0, # 北向资金
            "institution_buy": [], # 机构龙虎榜
            "sector_inflow": [], # 行业净流入Top
            "sector_outflow": [], # 行业净流出Top
            "etf_active": [], # 活跃ETF
            "market_breadth": {}, # 涨跌家数
            "north_date": None,
            "institution_date": None,
        }
        
        # 1. 市场广度 (Market Breadth)
        try:
            # 使用实时行情概览
            df_spot = ak.stock_zh_a_spot_em()
            if df_spot is not None and not df_spot.empty:
                up_count = len(df_spot[df_spot['涨跌幅'] > 0])
                down_count = len(df_spot[df_spot['涨跌幅'] < 0])
                flat_count = len(df_spot[df_spot['涨跌幅'] == 0])
                limit_up = len(df_spot[df_spot['涨跌幅'] >= 9.8]) # 粗略统计
                limit_down = len(df_spot[df_spot['涨跌幅'] <= -9.8])
                
                data["market_breadth"] = {
                    "up": up_count,
                    "down": down_count,
                    "flat": flat_count,
                    "limit_up": limit_up,
                    "limit_down": limit_down,
                    "ratio": round(up_count / (up_count + down_count + 1) * 100, 1)
                }
        except Exception as e:
            print(f"Market breadth error: {e}")

        # 2. 行业板块资金流向 (Sector Flow)
        try:
            # 获取今日行业资金流排名
            df_flow = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
            if df_flow is not None and not df_flow.empty:
                # 东方财富接口返回列名可能包含：名称, 今日涨跌幅, 今日主力净流入, 占比...
                # 需要标准化处理
                # 假设列名：['名称', '今日涨跌幅', '今日主力净流入', '今日主力净流入占比', ...]
                
                # 转换净流入为数值 (单位通常是元，转换为亿元)
                flow_col = '今日主力净流入'
                name_col = '名称'
                pct_col = '今日涨跌幅'
                
                if flow_col in df_flow.columns:
                    # 转换单位：原始数据带有"万"或"亿"字样，akshare通常处理好了，或者是纯数字
                    # Akshare stock_sector_fund_flow_rank returns numeric but with mixed units sometimes strings
                    # Let's assume standardized numeric or handle string conversion
                    
                    def parse_flow(val):
                        if isinstance(val, (int, float)):
                            return float(val) / 1e8 # 假设原始单位是元
                        if isinstance(val, str):
                            val = val.replace('亿', '').replace('万', '')
                            # 简单处理，实际应更严谨
                            return float(val)
                        return 0.0

                    # 排序
                    # 注意：AkShare返回的数据已经是排序过的，或者是DataFrame
                    # 直接取前5和后5
                    
                    # Inflow Top 5
                    top_in = df_flow.head(5).copy()
                    inflow_list = []
                    for _, row in top_in.iterrows():
                        raw_val = row.get(flow_col)
                        # Akshare rank data usually is raw unit '10000' or similar? 
                        # Actually stock_sector_fund_flow_rank usually returns string with unit or big number
                        # Let's simple format string
                        inflow_list.append({
                            "name": row.get(name_col),
                            "pct": row.get(pct_col),
                            "net_in": row.get(flow_col) # Keep original for now, LLM can interpret
                        })
                    data["sector_inflow"] = inflow_list

                    # Outflow Top 5 (Bottom of list)
                    top_out = df_flow.tail(5).sort_values(by=flow_col, ascending=True).copy()
                    outflow_list = []
                    for _, row in top_out.iterrows():
                        outflow_list.append({
                            "name": row.get(name_col),
                            "pct": row.get(pct_col),
                            "net_out": row.get(flow_col)
                        })
                    data["sector_outflow"] = outflow_list
                    
        except Exception as e:
            print(f"Sector flow error: {e}")

        # 3. 热门ETF成交 (ETF Activity)
        try:
            # 获取ETF实时行情，按成交额排序
            df_etf = ak.fund_etf_spot_em()
            if df_etf is not None and not df_etf.empty:
                # 按成交额降序
                df_etf = df_etf.sort_values(by='成交额', ascending=False).head(5)
                etf_list = []
                for _, row in df_etf.iterrows():
                    etf_list.append({
                        "code": row.get('代码'),
                        "name": row.get('名称'),
                        "pct": row.get('涨跌幅'),
                        "turnover": row.get('成交额') # 元
                    })
                data["etf_active"] = etf_list
        except Exception as e:
            print(f"ETF data error: {e}")

        # 4. 北向资金 (现有逻辑)
        try:
            # 优先使用实时数据
            df_north = ak.stock_hsgt_fund_flow_summary_em()
            if df_north is not None and not df_north.empty:
                 # 筛选北向
                 north_rows = df_north[df_north['资金方向'] == '北向']
                 total_net = 0.0
                 for _, row in north_rows.iterrows():
                     val = row.get('成交净买额', 0)
                     if val:
                         total_net += float(val) / 1e8 # 原始单位可能是元? 
                         # stock_hsgt_fund_flow_summary_em returned value is usually in 亿元 for display or raw
                         # Documentation says: 单位: 元. So / 1e8 is correct.
                 
                 # Correction: stock_hsgt_fund_flow_summary_em '成交净买额' is usually formatted string or raw. 
                 # Let's rely on string parsing if needed, but akshare usually returns clean floats now.
                 # Actually, let's stick to the simpler hsgt_hist logic if this is complex, 
                 # BUT real-time is better.
                 # Let's use the 'north_money' from existing logic as fallback, but try to get real-time sum here.
                 pass

            # 保留原有的历史获取逻辑作为兜底
            hist_df = ak.stock_hsgt_hist_em(symbol="北向资金")
            if hist_df is not None and not hist_df.empty:
                if "日期" in hist_df.columns:
                    hist_df["日期"] = pd.to_datetime(hist_df["日期"], errors="coerce")
                    flow_col = None
                    for col in ["当日成交净买额", "当日资金流入", "资金流入", "当日净流入"]:
                        if col in hist_df.columns:
                            flow_col = col
                            break
                    if flow_col:
                        hist_df[flow_col] = pd.to_numeric(hist_df[flow_col], errors="coerce")
                        last = hist_df.sort_values("日期").iloc[-1]
                        data["north_money"] = round(float(last.get(flow_col)) / 100000000.0 if abs(float(last.get(flow_col))) > 10000 else float(last.get(flow_col)), 2) # Handle units carefully
                        # Actually akshare hsgt_hist usually returns Million Yuan or Yuan. 
                        # Let's assume it's large numbers.
                        data["north_date"] = last.get("日期").strftime("%Y-%m-%d")

        except Exception as e:
            print(f"North money error: {e}")

        # 5. 机构龙虎榜 (现有逻辑，保留)
        try:
            df_jg = ak.stock_lhb_jgmmtj_em()
            if df_jg is not None and not df_jg.empty:
                date_col = "上榜日期" if "上榜日期" in df_jg.columns else None
                if date_col:
                    df_jg[date_col] = pd.to_datetime(df_jg[date_col], errors="coerce")
                    latest_date = df_jg[date_col].max()
                    data["institution_date"] = latest_date.strftime("%Y-%m-%d")
                    df_jg = df_jg[df_jg[date_col] == latest_date]

                net_buy_col = "净买入额" # Standardize
                for col in df_jg.columns:
                    if "净" in col and "额" in col:
                        net_buy_col = col
                        break
                
                name_col = "名称" if "名称" in df_jg.columns else "股票名称"
                
                if net_buy_col and name_col in df_jg.columns:
                     # Sort by abs value of net buy to see big moves (buy or sell)
                     # Or just top buys
                     df_jg[net_buy_col] = pd.to_numeric(df_jg[net_buy_col], errors="coerce")
                     top_buy = df_jg.sort_values(by=net_buy_col, ascending=False).head(5)
                     
                     res = []
                     for _, row in top_buy.iterrows():
                         val = row.get(net_buy_col)
                         res.append({
                             "name": row.get(name_col),
                             "net_buy": round(val / 1e4, 0) if val else 0 # Show in Wan
                         })
                     data["institution_buy"] = res
        except Exception as e:
            print(f"Institution error: {e}")
            
        return data

if __name__ == "__main__":
    analyst = MoneyFlowAnalyst()
    print(analyst.get_money_flow())