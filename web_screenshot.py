#!/usr/bin/env python3

import asyncio
import argparse

from pyppeteer import launch


async def get_page(url, screen_shot_file_path):
    browser = await launch(args=['--no-sandbox', '--window-size=1920,1080'], headless=True, defaultViewport={'width': 1920, 'height': 1080})
    page = await browser.newPage()
    await page.goto(url)
    await page.screenshot({'path': screen_shot_file_path, 'type': 'jpeg', 'quality': 50})
    await browser.close()


def main():
    ap = argparse.ArgumentParser(
        prog='web_screenshot',
        usage='%(prog)s.py [options]',
        description='uses headless Chrome to take a screen shot of a URL'
    )
    ap.add_argument(
        '--url',
        help='URL to get screenshot',
        required=True
    )
    ap.add_argument(
        '--screenshot',
        help='file path for the screenshot to write',
        required=True
    )
    args = ap.parse_args()
    asyncio.get_event_loop().run_until_complete(get_page(args.url, args.screenshot))


if __name__ == '__main__':
    main()
