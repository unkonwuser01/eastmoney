"""
ETF联接基金识别模块
自动识别基金是否为ETF联接基金，并获取关联的ETF代码
"""
import akshare as ak
import pandas as pd
from typing import Optional, Dict


def _safe_str(val, default=""):
    """安全转换为字符串"""
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return default
        return str(val)
    except:
        return default


def _safe_float(val, default=0.0):
    """安全转换为浮点数"""
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return default
        return float(val)
    except:
        return default


# 常见ETF联接基金映射表（作为备选方案）
ETF_LINKAGE_MAP = {
    '008888': '159995',  # 华夏国证半导体芯片ETF联接C -> 国证半导体芯片ETF
    '008887': '159995',  # 华夏国证半导体芯片ETF联接A -> 国证半导体芯片ETF
    '110026': '159915',  # 易方达创业板ETF联接A -> 创业板ETF
    '003957': '159915',  # 易方达创业板ETF联接C -> 创业板ETF
    '007339': '510300',  # 易方达沪深300ETF联接A -> 沪深300ETF
    '007340': '510300',  # 易方达沪深300ETF联接C -> 沪深300ETF
    '110020': '510050',  # 易方达上证50指数A -> 上证50ETF
    '004746': '510050',  # 易方达上证50指数C -> 上证50ETF
    '000961': '510500',  # 天弘中证500指数A -> 中证500ETF
    '000962': '510500',  # 天弘中证500指数C -> 中证500ETF
    '016708': '516650',  # 华夏有色金属ETF联接C -> 华夏细分有色金属产业主题ETF
    '016707': '516650',  # 华夏有色金属ETF联接A -> 华夏细分有色金属产业主题ETF
    '018897': '562950',  # 易方达消费电子ETF联接C -> 易方达中证消费电子主题ETF
    '018896': '562950',  # 易方达消费电子ETF联接A -> 易方达中证消费电子主题ETF
}


def is_etf_linkage_fund(fund_name: str) -> bool:
    """
    判断基金是否为ETF联接基金
    
    Args:
        fund_name: 基金名称
    
    Returns:
        是否为ETF联接基金
    """
    if not fund_name:
        return False
    
    # 方法1：名称包含"ETF联接"
    if 'ETF联接' in fund_name or 'etf联接' in fund_name.lower():
        return True
    
    # 方法2：名称包含"ETF指数"（部分联接基金这样命名）
    if 'ETF指数' in fund_name:
        return True
    
    return False


def get_etf_code_from_holdings(fund_code: str) -> Optional[str]:
    """
    通过持仓信息获取ETF代码（联接基金的第一大持仓通常是ETF）
    
    Args:
        fund_code: 基金代码
    
    Returns:
        ETF代码或None
    """
    try:
        from datetime import datetime
        year = str(datetime.now().year)
        
        # 获取持仓信息
        df = ak.fund_portfolio_hold_em(symbol=fund_code, date=year)
        
        if df is None or df.empty:
            # 尝试上一年
            df = ak.fund_portfolio_hold_em(symbol=fund_code, date=str(int(year) - 1))
        
        if df is None or df.empty:
            return None
        
        # 获取最新季度数据
        if '季度' in df.columns:
            latest_quarter = df['季度'].max()
            df = df[df['季度'] == latest_quarter]
        
        # 获取第一大持仓
        if len(df) > 0:
            first_holding = df.iloc[0]
            holding_code = _safe_str(first_holding.get('股票代码', ''))
            holding_name = _safe_str(first_holding.get('股票名称', ''))
            holding_weight = _safe_float(first_holding.get('占净值比例', 0))
            
            # 判断是否为ETF（持仓比例通常>80%，且代码是ETF格式）
            if holding_weight > 80 and holding_code:
                # ETF代码通常是6位数字，且以1、5开头
                if len(holding_code) == 6 and holding_code[0] in ['1', '5']:
                    print(f"[ETF Detector] Found ETF from holdings: {fund_code} -> {holding_code} ({holding_name}, {holding_weight}%)")
                    return holding_code
        
        return None
    except Exception as e:
        print(f"[ETF Detector] Error getting holdings for {fund_code}: {e}")
        return None


def get_etf_code_from_map(fund_code: str) -> Optional[str]:
    """
    从映射表获取ETF代码
    
    Args:
        fund_code: 基金代码
    
    Returns:
        ETF代码或None
    """
    return ETF_LINKAGE_MAP.get(fund_code)


def detect_etf_linkage(fund_code: str, fund_name: str) -> Dict:
    """
    检测基金是否为ETF联接基金，并获取关联的ETF代码
    
    Args:
        fund_code: 基金代码
        fund_name: 基金名称
    
    Returns:
        {
            'is_etf_linkage': bool,
            'etf_code': str or None,
            'detection_method': str  # 'name', 'holdings', 'map', 'none'
        }
    """
    result = {
        'is_etf_linkage': False,
        'etf_code': None,
        'detection_method': 'none'
    }
    
    # 1. 判断是否为ETF联接基金
    if not is_etf_linkage_fund(fund_name):
        return result
    
    result['is_etf_linkage'] = True
    
    # 2. 获取ETF代码（优先级：映射表 > 持仓查询）
    
    # 方法1：从映射表获取（最快）
    etf_code = get_etf_code_from_map(fund_code)
    if etf_code:
        result['etf_code'] = etf_code
        result['detection_method'] = 'map'
        print(f"[ETF Detector] {fund_code} is ETF linkage fund, ETF code: {etf_code} (from map)")
        return result
    
    # 方法2：从持仓信息获取（较慢但准确）
    etf_code = get_etf_code_from_holdings(fund_code)
    if etf_code:
        result['etf_code'] = etf_code
        result['detection_method'] = 'holdings'
        print(f"[ETF Detector] {fund_code} is ETF linkage fund, ETF code: {etf_code} (from holdings)")
        return result
    
    # 无法获取ETF代码
    print(f"[ETF Detector] {fund_code} is ETF linkage fund, but ETF code not found")
    return result


def add_to_etf_linkage_map(fund_code: str, etf_code: str):
    """
    将新发现的ETF联接基金映射添加到映射表
    （运行时动态添加，不持久化）
    
    Args:
        fund_code: 基金代码
        etf_code: ETF代码
    """
    ETF_LINKAGE_MAP[fund_code] = etf_code
    print(f"[ETF Detector] Added to map: {fund_code} -> {etf_code}")
