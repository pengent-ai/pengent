import httpx
from io import BytesIO


class RequestReader:
    """
    非同期HTTPリクエストでコンテンツを取得するユーティリティクラス
    """
    @classmethod
    async def get_content(cls, url: str) -> str | BytesIO:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "text" in content_type or "markdown" in content_type:
            return response.text
        elif "pdf" in content_type:
            return BytesIO(response.content)
        elif "html" in content_type:
            return response.text
        raise ValueError(f"Unsupported content type: {content_type}")
