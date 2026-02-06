# -*- coding: utf-8 -*-
"""
数据迁移脚本：为已有基金自动检测并添加ETF联接信息
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.storage.db import get_all_funds, upsert_fund
from app.core.etf_linkage_detector import detect_etf_linkage


def migrate_etf_linkage_data():
    """
    迁移已有基金数据，自动检测ETF联接基金
    """
    print("=" * 60)
    print("开始迁移ETF联接基金数据...")
    print("=" * 60)
    
    # 获取所有基金（不限用户）
    all_funds = get_all_funds()
    
    if not all_funds:
        print("未找到任何基金数据")
        return
    
    print(f"找到 {len(all_funds)} 个基金，开始检测...")
    print()
    
    updated_count = 0
    etf_linkage_count = 0
    
    for fund in all_funds:
        code = fund['code']
        name = fund['name']
        user_id = fund.get('user_id')
        
        # 检查是否已经有ETF信息
        if fund.get('is_etf_linkage') or fund.get('etf_code'):
            print(f"[跳过] {code} {name} - 已有ETF信息")
            continue
        
        # 自动检测
        print(f"[检测] {code} {name}...", end=" ")
        detection_result = detect_etf_linkage(code, name)
        
        if detection_result['is_etf_linkage']:
            etf_linkage_count += 1
            print(f"✓ ETF联接基金 -> {detection_result['etf_code']}")
            
            # 更新数据库
            fund_dict = dict(fund)
            fund_dict['is_etf_linkage'] = True
            fund_dict['etf_code'] = detection_result['etf_code']
            
            try:
                upsert_fund(fund_dict, user_id=user_id)
                updated_count += 1
            except Exception as e:
                print(f"  [错误] 更新失败: {e}")
        else:
            print("✗ 非ETF联接基金")
    
    print()
    print("=" * 60)
    print(f"迁移完成！")
    print(f"总基金数: {len(all_funds)}")
    print(f"检测到ETF联接基金: {etf_linkage_count}")
    print(f"成功更新: {updated_count}")
    print("=" * 60)


if __name__ == "__main__":
    migrate_etf_linkage_data()
