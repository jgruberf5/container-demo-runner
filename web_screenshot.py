#!/usr/bin/env python3

import asyncio
import tempfile
import os
import argparse

from pyppeteer import launch


async def get_page(url, screen_shot_file_path, working_directory=None):
    if working_directory:
        if not os.path.exists(working_directory):
            os.makedirs(working_directory)
        os.environ['PYPPETEER_HOME'] = working_directory
    browser = await launch(args=['--no-sandbox', '--window-size=1920,1080', '--user-data-dir=%s' % working_directory], headless=True, defaultViewport={'width': 1920, 'height': 1080})
    page = await browser.newPage()
    await page.goto(url)
    await page.screenshot({'path': screen_shot_file_path})
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
    ap.add_argument(
        '--working-directory',
        help='working directory for Chromium',
        required=False,
        default=None
    )
    args = ap.parse_args()
    asyncio.get_event_loop().run_until_complete(get_page(args.url, args.screenshot, args.working_directory))


if __name__ == '__main__':
    main()
