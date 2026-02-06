"""
代理池配置模块
用于配置和管理动态代理池连接
"""
import os
import requests
from typing import Optional, Dict


# 代理池配置
PROXY_POOL_ENABLED = os.environ.get('PROXY_POOL_ENABLED', 'true').lower() == 'true'
PROXY_POOL_HOST = os.environ.get('PROXY_POOL_HOST', 'host.docker.internal')
PROXY_POOL_HTTP_PORT = os.environ.get('PROXY_POOL_HTTP_PORT', '17286')  # RELAXED模式
PROXY_POOL_SOCKS5_PORT = os.environ.get('PROXY_POOL_SOCKS5_PORT', '17284')  # RELAXED模式

# 代理URL
HTTP_PROXY_URL = f"http://{PROXY_POOL_HOST}:{PROXY_POOL_HTTP_PORT}"
SOCKS5_PROXY_URL = f"socks5://{PROXY_POOL_HOST}:{PROXY_POOL_SOCKS5_PORT}"


def get_proxy_config(use_socks5: bool = False) -> Optional[Dict[str, str]]:
    """
    获取代理配置
    
    Args:
        use_socks5: 是否使用SOCKS5代理（默认使用HTTP代理）
    
    Returns:
        代理配置字典，如果禁用代理则返回None
    """
    if not PROXY_POOL_ENABLED:
        return None
    
    if use_socks5:
        return {
            'http': SOCKS5_PROXY_URL,
            'https': SOCKS5_PROXY_URL,
        }
    else:
        return {
            'http': HTTP_PROXY_URL,
            'https': HTTP_PROXY_URL,
        }


def test_proxy_connection() -> bool:
    """
    测试代理池连接是否正常
    
    Returns:
        True if proxy is accessible, False otherwise
    """
    if not PROXY_POOL_ENABLED:
        print("[Proxy] Proxy pool is disabled")
        return False
    
    try:
        # 测试HTTP代理
        proxies = get_proxy_config()
        response = requests.get(
            'http://www.baidu.com',
            proxies=proxies,
            timeout=5
        )
        if response.status_code == 200:
            print(f"[Proxy] HTTP proxy connection successful: {HTTP_PROXY_URL}")
            return True
        else:
            print(f"[Proxy] HTTP proxy returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"[Proxy] Proxy connection failed: {e}")
        return False


def get_requests_session_with_proxy() -> requests.Session:
    """
    创建一个配置了代理的requests会话
    
    Returns:
        配置了代理的requests.Session对象
    """
    session = requests.Session()
    
    if PROXY_POOL_ENABLED:
        proxies = get_proxy_config()
        if proxies:
            session.proxies.update(proxies)
            print(f"[Proxy] Session configured with proxy: {HTTP_PROXY_URL}")
    
    # 设置请求头
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    })
    
    return session


# 打印配置信息
if PROXY_POOL_ENABLED:
    print(f"[Proxy] Proxy pool enabled")
    print(f"[Proxy] HTTP Proxy: {HTTP_PROXY_URL}")
    print(f"[Proxy] SOCKS5 Proxy: {SOCKS5_PROXY_URL}")
else:
    print(f"[Proxy] Proxy pool disabled")
