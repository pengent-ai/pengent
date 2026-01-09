from playwright.async_api import async_playwright

from ...lib import get_logger

logger = get_logger()


class HtmlReader:
    """非同期HTMLリーダー"""
    @classmethod
    async def get_content(cls, url: str) -> str:
        logger.info(f"Fetching content from {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-http2",  # HTTP/2を無効化
                    "--disable-features=VizDisplayCompositor",
                    "--disable-web-security",
                    "--disable-features=TranslateUI",
                    "--no-first-run",
                    "--disable-default-apps",
                    "--disable-extensions",
                    "--disable-blink-features=AutomationControlled",  # 自動化検出を回避
                    "--no-sandbox",  # サンドボックスを無効化
                    "--disable-setuid-sandbox",  # setuidサンドボックスを無効化
                    "--disable-dev-shm-usage",  # /dev/shmの使用を無効化
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu",  # GPUを無効化
                    "--window-size=1920,1080",  # ウィンドウサイズを設定
                ],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"),
                viewport={"width": 1920, "height": 1080},
                locale="ja-JP",
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
                    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "max-age=0",
                    "sec-ch-ua": (
                        '"Not_A Brand";v="8", '
                        '"Chromium";v="120", "Google Chrome";v="120"'),
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "none",
                    "sec-fetch-user": "?1",
                    "upgrade-insecure-requests": "1",
                    "Connection": "keep-alive",
                },
            )
            page = await context.new_page()

            # 不要なリソース(画像・CSS・フォントなど)をブロック
            async def _route_intercept(route):
                if route.request.resource_type in {"image", "stylesheet", "font"}:
                    return await route.abort()
                return await route.continue_()

            page.route("**/*", _route_intercept)

            # 自動化検知回避スクリプト
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'permissions', {
                  get: () => ({ query: () => Promise.resolve({ state: 'granted' }) })
                });
                Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3] });
            """)

            response = await page.goto(
                url,
                timeout=120000,  # 120秒
                wait_until="domcontentloaded",
                referer="https://www.google.com/",
            )
            if response and response.status >= 400:
                logger.warning(f"HTTP error status: {response.status}")

            # ネットワークがアイドルになるのを待つが、タイムアウトでスキップ
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                logger.warning("networkidle timeout; continuing")

            html = await page.content()
            print(f"Fetched HTML content length: {len(html)} characters")
            await browser.close()
            return html
