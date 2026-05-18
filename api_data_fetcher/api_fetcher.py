"""
Main API Data Fetcher with async support, rate limiting, and error handling
"""
import asyncio
import time
from typing import Dict, List, Optional
import aiohttp
import requests

try:
    from .config import APIConfig
    from .logger import log_debug, log_error, log_info, log_warning
except ImportError:
    from config import APIConfig
    from logger import log_debug, log_error, log_info, log_warning


class APIDataFetcher:
    """
    Handles API requests with retry logic, rate limiting, and error handling
    """

    def __init__(self, _config: APIConfig):
        self.config = _config
        self.session = None
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_interval = 60.0 / _config.rate_limit  # seconds between requests

    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_interval:
            sleep_time = self.rate_limit_interval - time_since_last
            log_debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def sync_fetch(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Synchronous API fetch with retry logic
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response as dictionary or None if failed
        """
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.config.max_retries):
            try:
                self._rate_limit()

                response = requests.get(
                    url,
                    headers=self.config.get_headers(),
                    params=params,
                    timeout=self.config.timeout
                )
                response.raise_for_status()

                log_info(f"Successfully fetched {url} (attempt {attempt + 1})")
                return response.json()

            except requests.exceptions.Timeout:
                log_warning(f"Timeout on attempt {attempt + 1} for {url}")
            except requests.exceptions.RequestException as e:
                log_error(f"Request failed on attempt {attempt + 1}: {str(e)}")

            if attempt < self.config.max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

        log_error(f"Failed to fetch {url} after {self.config.max_retries} attempts")
        return None

    async def async_fetch(self, session: aiohttp.ClientSession,
                         endpoint: str,
                         params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Asynchronous API fetch
        
        Args:
            session: aiohttp client session
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response as dictionary or None if failed
        """
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.config.max_retries):
            try:
                async with session.get(
                    url,
                    headers=self.config.get_headers(),
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    response.raise_for_status()
                    log_info(f"Async fetch successful: {url}")
                    return await response.json()

            except aiohttp.ClientError as e:
                log_warning(f"Async request failed (attempt {attempt + 1}): {str(e)}")

            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(2 ** attempt)

        log_error(f"Failed async fetch for {url}")
        return None

    async def batch_fetch(self, _endpoints: List[str]) -> List[Optional[Dict]]:
        """
        Fetch multiple _endpoints concurrently
        
        Args:
            _endpoints: List of API _endpoints
            
        Returns:
            List of responses (None for failed requests)
        """
        async with aiohttp.ClientSession() as session:
            tasks = [self.async_fetch(session, endpoint) for endpoint in _endpoints]
            _results = await asyncio.gather(*tasks)
            return _results

    def fetch_paginated_data(self, endpoint: str,
                            page_param: str = 'page',
                            page_size: int = 100) -> List[Dict]:
        """
        Fetch paginated API data
        
        Args:
            endpoint: API endpoint
            page_param: Parameter name for page number
            page_size: Items per page
            
        Returns:
            Combined list of all items from all pages
        """
        all_items = []
        current_page = 1

        while True:
            params = {page_param: current_page, 'limit': page_size}
            response = self.sync_fetch(endpoint, params)

            if not response or 'data' not in response:
                break

            items = response['data']
            if not items:
                break

            all_items.extend(items)
            log_info(f"Fetched page {current_page} with {len(items)} items")

            # Check if this is the last page
            if len(items) < page_size:
                break

            current_page += 1

        log_info(f"Total fetched: {len(all_items)} items from {current_page} pages")
        return all_items

# Usage example
if __name__ == "__main__":
    config = APIConfig()
    fetcher = APIDataFetcher(config)

    # Single fetch
    data = fetcher.sync_fetch("/users", {"id": 123})

    # Batch fetch
    endpoints = ["/users/1", "/users/2", "/users/3"]
    results = asyncio.run(fetcher.batch_fetch(endpoints))

    # Paginated fetch
    all_users = fetcher.fetch_paginated_data("/users", page_size=50)
