import json
import time
from ssl import SSLCertVerificationError, SSLError
import datetime

import aiohttp
import asyncio
from threading import Thread, Event
from urllib.parse import urlparse
from bs4 import BeautifulSoup

MAX_CONCURRENT_REQUESTS = 10

semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


def is_valid_url(url):       #解析url
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


class URLScannerModule:
    def __init__(self):
        self.url_queue = asyncio.Queue()
        self.url_status = {}
        self.results = {}
        self.pause_event = Event()
        self.stop_event = Event()

    async def fetch(self, session, url):
        async with semaphore:
            try:
                # 如果URL不以http://或https://开头，则添加http://前缀
                if not url.startswith(("http://", "https://")):
                    url = "http://" + url
                    print(url)
                async with session.get(url, ssl=False) as response:
                    if response.status in [502, 400] and url.startswith("http://"):
                        # 尝试使用https前缀重新访问
                        url = url.replace("http://", "https://")
                        async with session.get(url, ssl=False) as https_response:
                            return await self._process_response(https_response, url)
                    else:
                        return await self._process_response(response, url)


            except SSLError as e:
                if 'dh key too small' in str(e).lower():
                    print(f"DH密钥太小: {url} - {e}")
                else:
                    print(f"SSL错误: {url} - {e}")
                return None
            except SSLCertVerificationError as e:
                print(f"SSL证书验证错误: {url} - {e}")
                return None
            except aiohttp.ClientConnectorError as e:
                print(f"连接错误: {url} - {e}")
                return None
            except Exception as e:
                print(f"请求错误: {e}")
                return None

    async def _process_response(self, response, url):
        html_content = await response.text()
        soup = BeautifulSoup(html_content, 'lxml')        #解析html
        text_content = soup.get_text(separator=' ', strip=True)

        # 限制 text_content 的长度为 4096 字符
        text_content = text_content[:64]

        return {
            'status': response.status,
            'title': self.parse_title(html_content),
            'content': text_content,
            'url': url
        }

    @staticmethod
    def parse_title(html_content):
        import re
        title_match = re.search('<title>(.*?)</title>', html_content, re.IGNORECASE)
        if title_match:
            return title_match.group(1)
        return None

    async def worker(self, session):
        while not self.stop_event.is_set():
            if self.pause_event.is_set():
                await asyncio.sleep(1)
                continue

            try:
                url = self.url_queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(1)
                continue

            response_data = await self.fetch(session, url)
            if response_data:
                self.results[url] = {
                    'status': response_data['status'],
                    'title': response_data['title'],
                    'content': response_data['content'],
                    'url': response_data['url']
                }
                self.url_status[url] = "已完成"
                self.url_queue.task_done()

    async def main_worker(self):
        async with aiohttp.ClientSession() as session:
            tasks = [self.worker(session) for _ in range(MAX_CONCURRENT_REQUESTS)]
            await asyncio.gather(*tasks)

    def start(self):
        self.thread = Thread(target=self.main_thread)
        self.thread.start()

    def main_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.main_worker())

    def pause(self):
        self.pause_event.set()

    def resume(self):
        self.pause_event.clear()

    def stop(self):
        self.stop_event.set()
        self.thread.join()

    def add_url(self, url):
        if url not in self.url_status:
            self.url_queue.put_nowait(url)
            self.url_status[url] = "待处理"
        else:
            print(f"已在队列中: {url}")

    def get_status(self, url=None):
        if url:
            return self.url_status.get(url, None)
        return self.url_status

    def get_results(self, url=None):
        if url:
            return self.results.get(url, None)
        return self.results


if __name__ == "__main__":
    scanner = URLScannerModule()
    
    try:
        with open("url.txt", "r", encoding='utf-8') as f:
            for i in f.readlines():
                scanner.add_url(i)
        
        scanner.start()
        
        while True:
            try:
                # 先读取现有结果
                existing_results = {}
                try:
                    with open("res2.json", "r", encoding='utf-8') as f:
                        existing_results = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    pass

                # 更新结果
                current_results = scanner.get_results()
                existing_results.update(current_results)

                # 保存合并后的结果
                with open("res2.json", "w", encoding='utf-8') as f:
                    print(scanner.get_status())
                    json.dump(existing_results, f, ensure_ascii=False, indent=2)
                time.sleep(5)
                
            except KeyboardInterrupt:
                print("\n正在保存结果并退出...")
                # 同样的合并操作用于最终保存
                try:
                    with open("res2.json", "r", encoding='utf-8') as f:
                        existing_results = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    existing_results = {}
                existing_results.update(scanner.get_results())
                with open("res2.json", "w", encoding='utf-8') as f:
                    json.dump(existing_results, f, ensure_ascii=False, indent=2)
                scanner.stop()
                break
            
    except Exception as e:
        print(f"发生错误: {e}")
        # 确保发生错误时也保存结果
        with open("res2.json", "w+", encoding='utf-8') as f:
            json.dump(scanner.get_results(), f, ensure_ascii=False, indent=2)
        scanner.stop()

    # 获取特定URL的状态
    # print(scanner.get_status("https://www.example.com"))

    # 获取所有URL的状态
