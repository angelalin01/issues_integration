#!/usr/bin/env python3

import ssl
import certifi

def check_ssl_configuration():
    """Check SSL certificate configuration and Python SSL settings"""
    print("=== SSL Configuration Check ===")
    print(f"Python SSL version: {ssl.OPENSSL_VERSION}")
    print(f"Default CA bundle: {ssl.get_default_verify_paths()}")
    print(f"Certifi CA bundle: {certifi.where()}")
    print(f"SSL context verify mode: {ssl.create_default_context().verify_mode}")
    
    try:
        context = ssl.create_default_context()
        print(f"SSL context created successfully")
        print(f"Check hostname: {context.check_hostname}")
        print(f"Verify mode: {context.verify_mode}")
    except Exception as e:
        print(f"Error creating SSL context: {e}")

if __name__ == "__main__":
    check_ssl_configuration()
