#!/usr/bin/env python3

import asyncio
import aiohttp
import ssl
import certifi
import os
from urllib.parse import urlparse

async def test_aiohttp_ssl_configurations():
    """Test different aiohttp SSL configurations to reproduce certificate verification error"""
    
    api_url = "https://api.devin.ai/v1/sessions"
    headers = {
        "Authorization": f"Bearer {os.getenv('DEVIN_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    print("=== Testing aiohttp SSL Configurations ===")
    print(f"aiohttp version: {aiohttp.__version__}")
    print(f"SSL version: {ssl.OPENSSL_VERSION}")
    print(f"certifi version: {certifi.__version__}")
    print(f"CA bundle: {certifi.where()}")
    
    print("\n1. Testing default SSL context...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers) as response:
                print(f"✅ Default SSL: Status {response.status}")
    except Exception as e:
        print(f"❌ Default SSL error: {e}")
    
    print("\n2. Testing strict SSL context...")
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(api_url, headers=headers) as response:
                print(f"✅ Strict SSL: Status {response.status}")
    except Exception as e:
        print(f"❌ Strict SSL error: {e}")
        if "certificate verify failed" in str(e):
            print("🎯 REPRODUCED: SSL certificate verification error!")
    
    print("\n3. Testing custom SSL context...")
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_default_certs()
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(api_url, headers=headers) as response:
                print(f"✅ Custom SSL: Status {response.status}")
    except Exception as e:
        print(f"❌ Custom SSL error: {e}")
        if "certificate verify failed" in str(e):
            print("🎯 REPRODUCED: SSL certificate verification error!")
    
    print("\n4. Testing simulated newer aiohttp behavior...")
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            enable_cleanup_closed=True,
            force_close=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(api_url, headers=headers) as response:
                print(f"✅ Newer aiohttp simulation: Status {response.status}")
    except Exception as e:
        print(f"❌ Newer aiohttp simulation error: {e}")
        if "certificate verify failed" in str(e):
            print("🎯 REPRODUCED: SSL certificate verification error!")
    
    print("\n5. Testing with system CA bundle vs certifi bundle...")
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.load_default_certs()  # Load system certs instead of certifi
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(api_url, headers=headers) as response:
                print(f"✅ System CA bundle: Status {response.status}")
    except Exception as e:
        print(f"❌ System CA bundle error: {e}")
        if "certificate verify failed" in str(e):
            print("🎯 REPRODUCED: SSL certificate verification error!")

if __name__ == "__main__":
    asyncio.run(test_aiohttp_ssl_configurations())
