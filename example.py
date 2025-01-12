#!/usr/bin/env python3

"""
NoteDx API Client Example Script
This script demonstrates how to initialize and configure the NoteDx API client
with different authentication methods.
"""

import sys
import os

# Add src directory to Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from notedx_sdk import NoteDxClient

def main():
    # Initialize client with API key
    client = NoteDxClient(
        base_url="https://api.notedx.io/v1",
        api_key="your_api_key"  # Replace with your API key
    )
    
    # Or initialize with email/password
    # client = NoteDxClient(
    #     base_url="https://api.notedx.io/v1",
    #     email="your_email@example.com",
    #     password="your_password"
    # )
    
    return client

if __name__ == "__main__":
    client = main() 