#!/usr/bin/env python3
"""
Main entry point for API Data Fetcher
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path if needed
sys.path.insert(0, str(Path(__file__).parent))

try:
    from .config import APIConfig
    from .api_fetcher import APIDataFetcher
    from .data_storage import DataStorage
    from .logger import log_info, log_error
except ImportError:
    from config import APIConfig
    from api_fetcher import APIDataFetcher
    from data_storage import DataStorage
    from logger import log_info, log_error


def fetch_user_data():
    """Example: Fetch and save user data"""
    config = APIConfig()
    fetcher = APIDataFetcher(config)
    storage = DataStorage()

    # Fetch data
    log_info("Fetching user data...")
    users = fetcher.fetch_paginated_data("/users", page_size=100)

    # Save results
    if users:
        storage.save_json(users, "users_data.json")
        storage.save_csv(users, "users_data.csv")
        log_info(f"Saved {len(users)} users")
    else:
        log_error("No data fetched")

async def fetch_multiple_endpoints():
    """Example: Fetch multiple endpoints concurrently"""
    config = APIConfig()
    fetcher = APIDataFetcher(config)

    endpoints = [
        "/users",
        "/posts", 
        "/comments"
    ]

    log_info(f"Fetching {len(endpoints)} endpoints concurrently...")
    results = await fetcher.batch_fetch(endpoints)

    for endpoint, result in zip(endpoints, results):
        if result:
            log_info(f"{endpoint}: {len(result)} items")

    return results

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='API Data Fetcher')
    parser.add_argument('--mode', choices=['users', 'batch'], default='users',
                       help='Fetch mode')

    args = parser.parse_args()

    if args.mode == 'users':
        fetch_user_data()
    elif args.mode == 'batch':
        asyncio.run(fetch_multiple_endpoints())
