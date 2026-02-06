"""
基金实时估值计算模块
支持两种计算方式：
1. ETF联接基金：通过ETF实时价格计算
2. 主动型基金：通过持仓信息计算

优化特性：
- 失败缓存：记录API失败的基金，避免重复尝试
- 智能路由：根据历史成功率选择最优数据源
"""
import akshare as ak
import pandas as pd
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import os
import time
import threading

# 配置代理（如果启用）
PROXY_ENABLED = os.environ.get('PROXY_POOL_ENABLED', 'false').lower() == 'true'
if PROXY_ENABLED:
    PROXY_HOST = os.environ.get('PROXY_POOL_HOST', 'host.docker.internal')
    PROXY_PORT = os.environ.get('PROXY_POOL_HTTP_PORT', '17286')
    PROXY_URL = f"http://{PROXY_HOST}:{PROXY_PORT}"
    
    # 设置环境变量，让requests使用代理
    os.environ['HTTP_PROXY'] = PROXY_URL
    os.environ['HTTPS_PROXY'] = PROXY_URL
    print(f"[Proxy] Enabled proxy: {PROXY_URL}")
else:
    print(f"[Proxy] Proxy disabled")


# ETF联接基金映射表（基金代码 -> ETF代码）
ETF_LINKAGE_MAP = {
    '008888': '159995',  # 华夏国证半导体芯片ETF联接C -> 国证半导体芯片ETF
    '008887': '159995',  # 华夏国证半导体芯片ETF联接A -> 国证半导体芯片ETF
    '110026': '159915',  # 易方达创业板ETF联接A -> 创业板ETF
    '003957': '159915',  # 易方达创业板ETF联接C -> 创业板ETF
    '007339': '510300',  # 易方达沪深300ETF联接A -> 沪深300ETF
    '007340': '510300',  # 易方达沪深300ETF联接C -> 沪深300ETF
    # 可以继续添加更多ETF联接基金
}


# ==================== 失败缓存机制 ====================
# 记录哪些基金在东方财富API中不存在，避免重复查询
_eastmoney_not_found_cache: Set[str] = set()
_eastmoney_cache_lock = threading.Lock()
_eastmoney_cache_timestamp = 0.0
_EASTMONEY_CACHE_TTL = 3600  # 1小时后重置缓存

# 记录股票API是否可用
_stock_api_available = True
_stock_api_last_check = 0.0
_STOCK_API_CHECK_INTERVAL = 300  # 5分钟检查一次


def _is_eastmoney_api_cached_not_found(fund_code: str) -> bool:
    """检查基金是否在东方财富API的不存在缓存中"""
    global _eastmoney_cache_timestamp
    
    with _eastmoney_cache_lock:
        # 检查缓存是否过期
        now = time.time()
        if now - _eastmoney_cache_timestamp > _EASTMONEY_CACHE_TTL:
            _eastmoney_not_found_cache.clear()
            _eastmoney_cache_timestamp = now
            return False
        
        return fund_code in _eastmoney_not_found_cache


def _mark_eastmoney_not_found(fund_code: str):
    """标记基金在东方财富API中不存在"""
    with _eastmoney_cache_lock:
        _eastmoney_not_found_cache.add(fund_code)
        print(f"[Cache] Marked {fund_code} as not found in Eastmoney API")


def _is_stock_api_available() -> bool:
    """检查股票API是否可用（避免频繁尝试失败的API）"""
    global _stock_api_available, _stock_api_last_check
    
    now = time.time()
    # 如果最近检查过且不可用，直接返回
    if not _stock_api_available and (now - _stock_api_last_check) < _STOCK_API_CHECK_INTERVAL:
        return False
    
    return True


def _mark_stock_api_unavailable():
    """标记股票API不可用"""
    global _stock_api_available, _stock_api_last_check
    _stock_api_available = False
    _stock_api_last_check = time.time()
    print(f"[Cache] Marked stock API as unavailable for {_STOCK_API_CHECK_INTERVAL}s")


def _safe_float(val, default=0.0):
    """安全转换为浮点数"""
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return default
        return float(val)
    except:
        return default


def _safe_str(val, default=""):
    """安全转换为字符串"""
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return default
        return str(val)
    except:
        return default


def get_etf_realtime_data_from_sina(etf_code: str) -> Optional[Dict]:
    """
    从新浪财经获取ETF实时行情数据（免费、稳定）
    
    Args:
        etf_code: ETF代码（如 159995）
    
    Returns:
        {'code': str, 'price': float, 'change_pct': float} 或 None
    """
    import requests
    
    print(f"[ETF-Sina] Fetching realtime data for ETF: {etf_code}")
    
    try:
        # 判断市场代码（上海sh/深圳sz）
        if etf_code.startswith('5'):
            market_code = f'sh{etf_code}'
        else:
            market_code = f'sz{etf_code}'
        
        # 新浪财经实时行情API
        url = f'http://hq.sinajs.cn/list={market_code}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'http://finance.sina.com.cn'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code != 200:
            print(f"[ETF-Sina] HTTP error: {response.status_code}")
            return None
        
        # 解析数据
        text = response.text.strip()
        if not text or '=""' in text:
            print(f"[ETF-Sina] No data returned for {etf_code}")
            return None
        
        # 格式: var hq_str_sh516650="有色金属ETF基金,2.101,2.209,2.155,..."
        parts = text.split('="')
        if len(parts) < 2:
            print(f"[ETF-Sina] Invalid data format")
            return None
        
        data_str = parts[1].rstrip('";')
        data = data_str.split(',')
        
        if len(data) < 6:
            print(f"[ETF-Sina] Insufficient data fields")
            return None
        
        name = data[0]
        current_price = _safe_float(data[3])
        prev_close = _safe_float(data[2])
        
        if current_price <= 0 or prev_close <= 0:
            print(f"[ETF-Sina] Invalid price data")
            return None
        
        # 计算涨跌幅
        change_pct = (current_price - prev_close) / prev_close * 100
        
        result = {
            'code': etf_code,
            'name': name,
            'price': current_price,
            'change_pct': round(change_pct, 2),
            'prev_close': prev_close,
            'open': _safe_float(data[1]),
            'high': _safe_float(data[4]),
            'low': _safe_float(data[5]),
        }
        
        print(f"[ETF-Sina] Got realtime data for {etf_code}: price={result['price']}, change={result['change_pct']}%")
        return result
    except Exception as e:
        print(f"[ETF-Sina] Error fetching data for {etf_code}: {e}")
        return None


def get_etf_realtime_data(etf_code: str) -> Optional[Dict]:
    """
    获取ETF实时行情数据（多数据源，带重试机制）
    优先级：
    1. 新浪财经（免费、稳定、快速）
    2. 东方财富（AkShare）
    
    Args:
        etf_code: ETF代码（如 159995）
    
    Returns:
        {'code': str, 'price': float, 'change_pct': float} 或 None
    """
    import time
    
    print(f"[ETF] Fetching realtime data for ETF: {etf_code}")
    
    # 方法1: 优先使用新浪财经（免费、稳定）
    print(f"[ETF] Method 1: Trying Sina Finance API...")
    result = get_etf_realtime_data_from_sina(etf_code)
    if result:
        return result
    
    print(f"[ETF] Sina Finance failed, trying Eastmoney API...")
    
    # 方法2: 降级到东方财富（AkShare）
    print(f"[ETF] Method 2: Using AkShare API: fund_etf_spot_em()")
    
    # 重试2次
    for attempt in range(2):
        try:
            print(f"[ETF] Attempt {attempt + 1}/2...")
            
            df = ak.fund_etf_spot_em()
            
            if df is None or df.empty:
                print(f"[ETF] API returned empty data")
                if attempt < 1:
                    time.sleep(2)
                    continue
                return None
            
            print(f"[ETF] Successfully fetched {len(df)} ETFs")
            
            etf_row = df[df['代码'] == etf_code]
            if etf_row.empty:
                print(f"[ETF] ETF code {etf_code} not found in market data")
                return None
            
            row = etf_row.iloc[0]
            result = {
                'code': etf_code,
                'name': _safe_str(row.get('名称')),
                'price': _safe_float(row.get('最新价')),
                'change_pct': _safe_float(row.get('涨跌幅')),
                'volume': _safe_float(row.get('成交量')),
                'amount': _safe_float(row.get('成交额')),
            }
            print(f"[ETF] Got realtime data for {etf_code}: price={result['price']}, change={result['change_pct']}%")
            return result
        except Exception as e:
            print(f"[ETF] Attempt {attempt + 1}/2 failed for {etf_code}: {e}")
            if attempt < 1:
                time.sleep(2)
    
    print(f"[ETF] All methods failed for {etf_code}")
    return None


def get_stock_realtime_data_from_sina(stock_codes: List[str]) -> Dict[str, Dict]:
    """
    从新浪财经批量获取股票实时行情数据（免费、稳定）
    
    Args:
        stock_codes: 股票代码列表
    
    Returns:
        {stock_code: {'price': float, 'change_pct': float}}
    """
    import requests
    
    print(f"[Stock-Sina] Fetching realtime data for {len(stock_codes)} stocks...")
    
    result = {}
    
    try:
        # 新浪财经支持批量查询，用逗号分隔
        # 需要添加市场代码前缀：sh(上海) 或 sz(深圳)
        market_codes = []
        for code in stock_codes:
            if code.startswith('6'):
                market_codes.append(f'sh{code}')
            else:
                market_codes.append(f'sz{code}')
        
        # 批量查询（每次最多20个）
        batch_size = 20
        for i in range(0, len(market_codes), batch_size):
            batch = market_codes[i:i+batch_size]
            codes_str = ','.join(batch)
            
            url = f'http://hq.sinajs.cn/list={codes_str}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://finance.sina.com.cn'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"[Stock-Sina] HTTP error: {response.status_code}")
                continue
            
            # 解析每只股票的数据
            lines = response.text.strip().split('\n')
            for line in lines:
                if not line or '=""' in line:
                    continue
                
                try:
                    # 格式: var hq_str_sz300394="天孚通信,188.45,..."
                    parts = line.split('="')
                    if len(parts) < 2:
                        continue
                    
                    # 提取股票代码
                    market_code = parts[0].split('_')[-1]
                    stock_code = market_code[2:]  # 去掉sh/sz前缀
                    
                    # 解析数据
                    data_str = parts[1].rstrip('";')
                    data = data_str.split(',')
                    
                    if len(data) < 6:
                        continue
                    
                    current_price = _safe_float(data[3])
                    prev_close = _safe_float(data[2])
                    
                    if current_price > 0 and prev_close > 0:
                        change_pct = (current_price - prev_close) / prev_close * 100
                        result[stock_code] = {
                            'price': current_price,
                            'change_pct': round(change_pct, 2),
                        }
                        print(f"[Stock-Sina] {stock_code}: price={current_price}, change={change_pct:.2f}%")
                except Exception as e:
                    print(f"[Stock-Sina] Failed to parse line: {e}")
                    continue
            
            # 添加小延迟
            if i + batch_size < len(market_codes):
                import time
                time.sleep(0.2)
        
        print(f"[Stock-Sina] Successfully fetched {len(result)}/{len(stock_codes)} stocks")
        return result
    except Exception as e:
        print(f"[Stock-Sina] Error: {e}")
        return {}


def get_stock_realtime_data(stock_codes: List[str]) -> Dict[str, Dict]:
    """
    批量获取股票实时行情数据
    优先级：
    1. 新浪财经（免费、稳定、快速）
    2. 东方财富（AkShare）
    
    Args:
        stock_codes: 股票代码列表
    
    Returns:
        {stock_code: {'price': float, 'change_pct': float}}
    """
    import time
    
    print(f"[Stock] Fetching realtime data for {len(stock_codes)} stocks: {stock_codes[:5]}...")
    
    # 方法1: 优先使用新浪财经（免费、稳定）
    print(f"[Stock] Method 1: Trying Sina Finance API...")
    result = get_stock_realtime_data_from_sina(stock_codes)
    if result and len(result) >= len(stock_codes) * 0.5:  # 至少成功50%
        return result
    
    print(f"[Stock] Sina Finance returned {len(result)} stocks, trying Eastmoney API...")
    
    # 方法2: 降级到东方财富（如果API可用）
    if not _is_stock_api_available():
        print(f"[Stock] Eastmoney stock API marked as unavailable, using Sina results")
        return result
    
    # 尝试使用东方财富API补充缺失的股票
    try:
        print(f"[Stock] Method 2: Using Eastmoney API for remaining stocks...")
        
        remaining_codes = [code for code in stock_codes if code not in result]
        if not remaining_codes:
            return result
        
        for code in remaining_codes:
            try:
                df = ak.stock_individual_info_em(symbol=code)
                if df is not None and not df.empty:
                    data_dict = dict(zip(df['item'], df['value']))
                    price = _safe_float(data_dict.get('最新价', 0))
                    change_pct = _safe_float(data_dict.get('涨跌幅', 0))
                    
                    if price > 0:
                        result[code] = {
                            'price': price,
                            'change_pct': change_pct,
                        }
                        print(f"[Stock] {code}: price={price}, change={change_pct}%")
                
                time.sleep(0.1)
            except Exception as e:
                print(f"[Stock] Eastmoney failed for {code}: {e}")
                # 如果连续失败，标记API不可用
                if len([c for c in remaining_codes if c in result]) == 0 and remaining_codes.index(code) >= 2:
                    _mark_stock_api_unavailable()
                    break
                continue
        
        print(f"[Stock] Total fetched: {len(result)}/{len(stock_codes)} stocks")
        return result
    except Exception as e:
        print(f"[Stock] Eastmoney API failed: {e}")
        return result


def get_fund_holdings(fund_code: str) -> List[Dict]:
    """
    获取基金持仓信息
    
    Args:
        fund_code: 基金代码
    
    Returns:
        [{'code': str, 'name': str, 'weight': float}]
    """
    try:
        print(f"[Holdings] Fetching holdings for fund: {fund_code}")
        # 从当前年份开始尝试，往前推2年
        current_year = datetime.now().year
        df = None
        
        for year_offset in range(3):  # 尝试当前年、去年、前年
            year = str(current_year - year_offset)
            print(f"[Holdings] Trying year {year}...")
            
            try:
                df = ak.fund_portfolio_hold_em(symbol=fund_code, date=year)
                if df is not None and not df.empty:
                    print(f"[Holdings] Successfully fetched data for year {year}")
                    break
            except Exception as e:
                print(f"[Holdings] Year {year} failed: {e}")
                continue
        
        if df is None or df.empty:
            print(f"[Holdings] No holdings data found for {fund_code}")
            return []
        
        print(f"[Holdings] Successfully fetched {len(df)} holdings records")
        
        # 获取最新季度数据
        if '季度' in df.columns:
            latest_quarter = df['季度'].max()
            df = df[df['季度'] == latest_quarter]
            print(f"[Holdings] Using latest quarter: {latest_quarter}, {len(df)} holdings")
        
        holdings = []
        for _, row in df.head(30).iterrows():  # 扩展到前30大持仓
            code = _safe_str(row.get('股票代码', ''))
            name = _safe_str(row.get('股票名称', ''))
            weight = _safe_float(row.get('占净值比例', 0))
            
            if code and weight > 0:
                holdings.append({
                    'code': code,
                    'name': name,
                    'weight': weight,
                })
                print(f"[Holdings] {code} {name}: {weight}%")
        
        print(f"[Holdings] Total valid holdings: {len(holdings)}")
        return holdings
    except Exception as e:
        print(f"[Holdings] Error fetching holdings for {fund_code}: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_fund_prev_nav(fund_code: str) -> Optional[float]:
    """
    获取基金前一日净值
    优先使用AkShare，TuShare作为备选
    
    Args:
        fund_code: 基金代码
    
    Returns:
        前一日净值（float）或 None
    """
    try:
        # 方法1: 使用AkShare获取净值历史（不需要token）
        try:
            df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
            if df is not None and not df.empty and '单位净值' in df.columns:
                # 获取最新净值
                latest_nav = df['单位净值'].iloc[-1]
                nav_value = _safe_float(latest_nav)
                if nav_value > 0:
                    print(f"[NAV] Got prev NAV for {fund_code} from AkShare: {nav_value}")
                    return nav_value
        except Exception as e:
            print(f"[NAV] AkShare failed for {fund_code}: {e}")
        
        # 方法2: 尝试从东方财富网基金排行榜获取
        try:
            for fund_type in ["股票型", "混合型", "指数型", "债券型", "QDII", "FOF"]:
                df = ak.fund_open_fund_rank_em(symbol=fund_type)
                if df is not None and not df.empty:
                    fund_row = df[df['基金代码'] == fund_code]
                    if not fund_row.empty:
                        nav = _safe_float(fund_row.iloc[0].get('单位净值'))
                        if nav > 0:
                            print(f"[NAV] Got prev NAV for {fund_code} from ranking: {nav}")
                            return nav
        except Exception as e:
            print(f"[NAV] Ranking failed for {fund_code}: {e}")
        
        # 方法3: 使用TuShare（如果配置了token）
        try:
            from src.data_sources.data_source_manager import get_fund_info_from_tushare
            
            df = get_fund_info_from_tushare(fund_code)
            if df is not None and not df.empty and '单位净值' in df.columns:
                latest_nav = df['单位净值'].iloc[-1]
                nav_value = _safe_float(latest_nav)
                if nav_value > 0:
                    print(f"[NAV] Got prev NAV for {fund_code} from TuShare: {nav_value}")
                    return nav_value
        except Exception as e:
            print(f"[NAV] TuShare failed for {fund_code}: {e}")
        
        print(f"[NAV] Failed to get prev NAV for {fund_code} from all sources")
        return None
    except Exception as e:
        print(f"[NAV] Error fetching prev NAV for {fund_code}: {e}")
        return None


def calculate_etf_linkage_estimation(fund_code: str, prev_nav: float) -> Optional[Dict]:
    """
    通过ETF实时价格计算联接基金估值
    
    Args:
        fund_code: 基金代码
        prev_nav: 前一日净值
    
    Returns:
        估值数据字典或None
    """
    etf_code = ETF_LINKAGE_MAP.get(fund_code)
    if not etf_code:
        return None
    
    etf_data = get_etf_realtime_data(etf_code)
    if not etf_data:
        return None
    
    etf_change_pct = etf_data['change_pct']
    estimated_nav = prev_nav * (1 + etf_change_pct / 100)
    
    return {
        'code': fund_code,
        'estimated_nav': round(estimated_nav, 4),
        'estimated_change_pct': round(etf_change_pct, 2),
        'prev_nav': round(prev_nav, 4),
        'estimation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'calculation_method': 'etf_linkage',
        'etf_code': etf_code,
        'etf_name': etf_data['name'],
    }


def calculate_holdings_based_estimation(fund_code: str, prev_nav: float) -> Optional[Dict]:
    """
    通过持仓信息计算基金估值
    
    Args:
        fund_code: 基金代码
        prev_nav: 前一日净值
    
    Returns:
        估值数据字典或None
    """
    # 获取持仓信息
    holdings = get_fund_holdings(fund_code)
    if not holdings:
        print(f"No holdings data for {fund_code}")
        return None
    
    # 获取持仓股票的实时行情
    stock_codes = [h['code'] for h in holdings]
    stock_data = get_stock_realtime_data(stock_codes)
    
    if not stock_data:
        print(f"No stock data for {fund_code}")
        return None
    
    # 计算加权涨跌幅
    total_weight = 0
    weighted_change = 0
    valid_holdings = []
    
    for holding in holdings:
        code = holding['code']
        weight = holding['weight']
        
        if code in stock_data:
            change_pct = stock_data[code]['change_pct']
            weighted_change += change_pct * weight
            total_weight += weight
            valid_holdings.append({
                'code': code,
                'name': holding['name'],
                'weight': weight,
                'change_pct': change_pct,
            })
    
    if total_weight == 0:
        print(f"No valid holdings for {fund_code}")
        return None
    
    # 计算估算涨跌幅（加权外推法）
    # 假设剩余未覆盖的持仓涨跌幅与已覆盖持仓成比例
    # 例如：前10大占76.51%，跌-2.38%，外推到100%：-2.38% / 0.7651 = -3.11%
    coverage_rate = total_weight / 100
    if coverage_rate > 0:
        estimated_change_pct = (weighted_change / 100) / coverage_rate
    else:
        estimated_change_pct = weighted_change / 100
    
    print(f"[Estimation] Coverage: {total_weight:.2f}%, Weighted change: {weighted_change/100:.2f}%, Extrapolated: {estimated_change_pct:.2f}%")
    
    # 计算估算净值
    estimated_nav = prev_nav * (1 + estimated_change_pct / 100)
    
    return {
        'code': fund_code,
        'estimated_nav': round(estimated_nav, 4),
        'estimated_change_pct': round(estimated_change_pct, 2),
        'prev_nav': round(prev_nav, 4),
        'estimation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'calculation_method': 'holdings_based',
        'holdings_coverage': round(total_weight, 2),
        'valid_holdings_count': len(valid_holdings),
        'top_holdings': valid_holdings[:5],  # 返回前5大持仓
    }


def get_fund_estimation_from_eastmoney(fund_code: str) -> Optional[Dict]:
    """
    直接从东方财富网获取基金估值数据
    
    Args:
        fund_code: 基金代码
    
    Returns:
        估值数据字典或None
    """
    # 检查缓存：如果之前查询过不存在，直接跳过
    if _is_eastmoney_api_cached_not_found(fund_code):
        print(f"[Cache] {fund_code} cached as not found in Eastmoney API, skipping...")
        return None
    
    try:
        print(f"[Eastmoney] Fetching estimation for {fund_code} from fund_value_estimation_em()")
        df = ak.fund_value_estimation_em()
        
        if df is None or df.empty:
            print(f"[Eastmoney] API returned empty data")
            return None
        
        # 查找指定基金
        fund_row = df[df['基金代码'] == fund_code]
        if fund_row.empty:
            print(f"[Eastmoney] Fund {fund_code} not found in estimation data")
            # 标记为不存在，下次直接跳过
            _mark_eastmoney_not_found(fund_code)
            return None
        
        row = fund_row.iloc[0]
        
        # 动态查找列名（包含日期）
        columns = df.columns.tolist()
        est_nav_col = None
        est_change_col = None
        prev_nav_col = None
        
        for col in columns:
            if '估算数据-估算值' in col:
                est_nav_col = col
            elif '估算数据-估算增长率' in col:
                est_change_col = col
            elif col.endswith('-单位净值') and '公布数据' not in col:
                prev_nav_col = col
        
        # 提取估值数据
        estimated_nav = _safe_float(row.get(est_nav_col)) if est_nav_col else 0
        est_change_str = _safe_str(row.get(est_change_col, '0')) if est_change_col else '0'
        estimated_change_pct = _safe_float(est_change_str.replace('%', '').strip())
        prev_nav = _safe_float(row.get(prev_nav_col)) if prev_nav_col else 0
        
        # 提取日期
        estimation_date = ''
        if est_nav_col:
            parts = est_nav_col.split('-估算数据')
            if parts:
                estimation_date = parts[0]
        
        if estimated_nav > 0:
            print(f"[Eastmoney] Got estimation for {fund_code}: nav={estimated_nav}, change={estimated_change_pct}%")
            return {
                'code': fund_code,
                'name': _safe_str(row.get('基金名称')),
                'estimated_nav': round(estimated_nav, 4),
                'estimated_change_pct': round(estimated_change_pct, 2),
                'prev_nav': round(prev_nav, 4),
                'prev_nav_date': estimation_date,
                'estimation_time': estimation_date,
                'calculation_method': 'eastmoney_api',
            }
        else:
            print(f"[Eastmoney] Invalid estimation data for {fund_code}")
            return None
    except Exception as e:
        print(f"[Eastmoney] Error fetching estimation for {fund_code}: {e}")
        import traceback
        traceback.print_exc()
        return None


def calculate_fund_estimation(fund_code: str, etf_code: Optional[str] = None) -> Optional[Dict]:
    """
    计算基金实时估值（自动选择计算方法）
    优先级：
    1. 东方财富网估值API（最快，覆盖2万只基金）
    2. ETF联接基金计算（通过ETF实时价格）
    3. 持仓计算（通过持仓股票实时价格）
    
    Args:
        fund_code: 基金代码
        etf_code: ETF代码（如果是ETF联接基金）
    
    Returns:
        估值数据字典或None
    """
    # 1. 优先尝试从东方财富网获取估值（最快，覆盖面广）
    result = get_fund_estimation_from_eastmoney(fund_code)
    if result:
        return result
    
    print(f"[Estimation] Fund {fund_code} not in Eastmoney API, trying custom calculation...")
    
    # 获取前一日净值（后续计算需要）
    prev_nav = get_fund_prev_nav(fund_code)
    if not prev_nav:
        print(f"[Estimation] Cannot get prev NAV for {fund_code}")
        return {
            'code': fund_code,
            'not_available': True,
            'reason': 'Cannot get previous NAV data',
        }
    
    # 2. 尝试ETF联接基金计算（使用传入的etf_code或映射表）
    etf_code_to_use = etf_code or ETF_LINKAGE_MAP.get(fund_code)
    if etf_code_to_use:
        print(f"[Estimation] Trying ETF linkage calculation with ETF: {etf_code_to_use}")
        # 临时添加到映射表（如果不存在）
        if fund_code not in ETF_LINKAGE_MAP:
            ETF_LINKAGE_MAP[fund_code] = etf_code_to_use
        
        result = calculate_etf_linkage_estimation(fund_code, prev_nav)
        if result:
            return result
        print(f"[Estimation] ETF linkage calculation failed")
    
    # 3. 尝试通过持仓计算
    print(f"[Estimation] Trying holdings-based calculation...")
    result = calculate_holdings_based_estimation(fund_code, prev_nav)
    if result:
        return result
    print(f"[Estimation] Holdings-based calculation failed")
    
    # 4. 无法计算
    return {
        'code': fund_code,
        'not_available': True,
        'reason': 'Unable to calculate estimation (not in Eastmoney API, ETF/stock data unavailable)',
    }


def batch_calculate_fund_estimation(fund_codes: List[str]) -> Dict[str, Dict]:
    """
    批量计算基金估值
    
    Args:
        fund_codes: 基金代码列表
    
    Returns:
        {fund_code: estimation_data}
    """
    results = {}
    
    for code in fund_codes:
        try:
            estimation = calculate_fund_estimation(code)
            if estimation:
                results[code] = estimation
            else:
                results[code] = {
                    'code': code,
                    'not_available': True,
                    'reason': 'Unable to calculate estimation',
                }
        except Exception as e:
            print(f"Error calculating estimation for {code}: {e}")
            results[code] = {
                'code': code,
                'not_available': True,
                'reason': str(e),
            }
    
    return results
