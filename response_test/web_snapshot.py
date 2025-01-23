import asyncio
from pyppeteer import launch, errors

MAX_URLS_BEFORE_RESTART = 10
CONCURRENT_TASKS = 10
TASK_TIMEOUT = 30  # 30 seconds
browser_lock = asyncio.Lock()

async def screenshot_page(browser, url, idx):
    print(f"Starting task for {url} (Index: {idx})")

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    page = await browser.newPage()
    try:
        await page.goto(url, waitUntil='networkidle0', timeout=15000)
        await asyncio.sleep(2)
        height = await page.evaluate("document.body.scrollHeight")
        await page.setViewport(viewport={"width": 1920, "height": height})
        save_path = f'img/screenshot_{idx}.png'
        await page.screenshot({'path': save_path, 'fullPage': True})
        print(f"Captured screenshot for {url} (Index: {idx}) and saved as {save_path}")
    except errors.NetworkError as e:
        if 'No session with given id' not in str(e):
            print(f"Network error when processing {url} (Index: {idx}): {e}")
    except Exception as e:
        print(f"Cannot GET {url} (Index: {idx}) due to {e}")
    finally:
        await page.close()
        print(f"Finished task for {url} (Index: {idx})")

async def run_task(browser, url, idx):
    try:
        await asyncio.wait_for(screenshot_page(browser, url, idx), timeout=TASK_TIMEOUT)
    except asyncio.TimeoutError:
        print(f"Task for {url} (Index: {idx}) timed out!")
    except Exception as e:
        print(f"Error while processing {url} (Index: {idx}): {e}")

async def screenshot_all(urls):
    browser = await launch(headless=True)

    for i in range(0, len(urls), CONCURRENT_TASKS):
        tasks = [run_task(browser, url, idx) for idx, url in enumerate(urls[i:i+CONCURRENT_TASKS], start=i+1)]
        await asyncio.gather(*tasks)

        # 在处理一定数量的URL后重启浏览器实例
        if (i + CONCURRENT_TASKS) % (CONCURRENT_TASKS * MAX_URLS_BEFORE_RESTART) == 0:
            async with browser_lock:
                await browser.close()
                browser = await launch(headless=True)

    await browser.close()

with open('url.txt', 'r', encoding="utf-8") as f:
    urls = [line.strip() for line in f.readlines()]

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(screenshot_all(urls))
