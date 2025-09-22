#!/usr/bin/env python3

import ssl
import socket
import certifi
import aiohttp
import asyncio
import os
import sys
from urllib.parse import urlparse

def check_system_ssl_config():
    """Check system SSL configuration and certificate stores"""
    print("=== System SSL Configuration ===")
    print(f"Python version: {sys.version}")
    print(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
    print(f"OpenSSL version info: {ssl.OPENSSL_VERSION_INFO}")
    print(f"SSL module file: {ssl.__file__}")
    
    paths = ssl.get_default_verify_paths()
    print(f"\nDefault CA file: {paths.cafile}")
    print(f"Default CA path: {paths.capath}")
    print(f"OpenSSL CA bundle: {paths.openssl_cafile}")
    print(f"OpenSSL CA path: {paths.openssl_capath}")
    
    print(f"\nCertifi CA bundle: {certifi.where()}")
    
    ca_files = [paths.cafile, paths.openssl_cafile, certifi.where()]
    for ca_file in ca_files:
        if ca_file:
            exists = os.path.exists(ca_file)
            print(f"CA file exists ({ca_file}): {exists}")

def test_ssl_connection_direct():
    """Test direct SSL connection to api.devin.ai"""
    print("\n=== Direct SSL Connection Test ===")
    hostname = "api.devin.ai"
    port = 443
    
    try:
        context = ssl.create_default_context()
        print(f"SSL context created: verify_mode={context.verify_mode}, check_hostname={context.check_hostname}")
        
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                print(f"✅ Direct SSL connection successful")
                print(f"Protocol: {ssock.version()}")
                print(f"Cipher: {ssock.cipher()}")
                
                cert = ssock.getpeercert()
                print(f"Certificate subject: {cert.get('subject', 'Unknown')}")
                print(f"Certificate issuer: {cert.get('issuer', 'Unknown')}")
                print(f"Certificate expires: {cert.get('notAfter', 'Unknown')}")
                
    except ssl.SSLCertVerificationError as e:
        print(f"❌ SSL Certificate Verification Error: {e}")
        print(f"Error code: {e.verify_code}")
        print(f"Error message: {e.verify_message}")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    return True

def test_certificate_chain():
    """Test certificate chain validation for api.devin.ai"""
    print("\n=== Certificate Chain Validation ===")
    hostname = "api.devin.ai"
    port = 443
    
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert_der = ssock.getpeercert_chain()
                if cert_der:
                    print(f"Certificate chain length: {len(cert_der)}")
                    for i, cert in enumerate(cert_der):
                        cert_pem = ssl.DER_cert_to_PEM_cert(cert)
                        x509 = ssl.PEM_cert_to_DER_cert(cert_pem)
                        print(f"Certificate {i+1}: {len(x509)} bytes")
                else:
                    print("No certificate chain available")
                    
    except Exception as e:
        print(f"❌ Certificate chain error: {e}")

async def test_aiohttp_ssl_detailed():
    """Detailed aiohttp SSL testing with different configurations"""
    print("\n=== Detailed aiohttp SSL Testing ===")
    
    api_url = "https://api.devin.ai/v1/sessions"
    headers = {
        "Authorization": f"Bearer {os.getenv('DEVIN_API_KEY', 'test')}",
        "Content-Type": "application/json"
    }
    
    test_configs = [
        ("Default SSL context", None),
        ("Certifi CA bundle", ssl.create_default_context(cafile=certifi.where())),
        ("System CA bundle", ssl.create_default_context()),
        ("Strict verification", ssl.create_default_context(cafile=certifi.where())),
    ]
    
    if len(test_configs) > 3:
        strict_context = test_configs[3][1]
        strict_context.check_hostname = True
        strict_context.verify_mode = ssl.CERT_REQUIRED
        strict_context.minimum_version = ssl.TLSVersion.TLSv1_2
    
    for config_name, ssl_context in test_configs:
        print(f"\nTesting {config_name}...")
        try:
            if ssl_context:
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                timeout = aiohttp.ClientTimeout(total=10, connect=5)
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    async with session.get(api_url, headers=headers) as response:
                        print(f"✅ {config_name}: Status {response.status}")
            else:
                timeout = aiohttp.ClientTimeout(total=10, connect=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(api_url, headers=headers) as response:
                        print(f"✅ {config_name}: Status {response.status}")
                        
        except ssl.SSLCertVerificationError as e:
            print(f"❌ {config_name}: SSL Certificate Verification Error")
            print(f"   Error: {e}")
            print(f"   Verify code: {e.verify_code}")
            print(f"   Verify message: {e.verify_message}")
            if "unable to get local issuer certificate" in str(e):
                print("   🎯 REPRODUCED: Same error as user!")
        except Exception as e:
            print(f"❌ {config_name}: {type(e).__name__}: {e}")

def generate_diagnostic_report():
    """Generate a comprehensive diagnostic report"""
    print("\n" + "="*60)
    print("SSL DIAGNOSTIC REPORT FOR USER")
    print("="*60)
    print("\nPlease run this script on your system and compare the output:")
    print("python3 ssl_diagnostic_tool.py")
    print("\nKey areas to compare:")
    print("1. OpenSSL version and SSL module configuration")
    print("2. CA certificate file locations and existence")
    print("3. Direct SSL connection success/failure")
    print("4. Certificate chain validation results")
    print("5. aiohttp SSL context behavior with different configurations")
    print("\nLook for differences in:")
    print("- Missing CA certificate files")
    print("- Different OpenSSL versions")
    print("- SSL context verification modes")
    print("- Certificate chain validation failures")

async def main():
    """Run all SSL diagnostic tests"""
    print("🔍 SSL Certificate Verification Diagnostic Tool")
    print("This tool helps identify SSL configuration differences")
    print("that cause 'unable to get local issuer certificate' errors")
    
    check_system_ssl_config()
    
    direct_ssl_success = test_ssl_connection_direct()
    
    test_certificate_chain()
    
    await test_aiohttp_ssl_detailed()
    
    generate_diagnostic_report()
    
    if not direct_ssl_success:
        print("\n⚠️  Direct SSL connection failed - this indicates a system-level SSL issue")
        print("   Check your system's CA certificate store and OpenSSL configuration")
    else:
        print("\n✅ Direct SSL connection successful - issue may be aiohttp-specific")

if __name__ == "__main__":
    asyncio.run(main())
