from ....tools.tool_utils import tool
from ....utility.storage.local_storage import LocalStorage
from ....lib.custom_logger import get_logger

logger = get_logger()
import requests


class FileTools:
    """ネットワーク・ファイルに関するツール群を提供します。

    Notes:
        - 指定したURLからファイルをダウンロードしストレージに保存します
        - ダウンロードはHttpのGETメソッドを使用して行います。
    """

    @staticmethod
    @tool(tags=["file"])
    def tool_file_download_from_url(
        url: str, file_name: str, bucket_name: str = "default"
    ) -> str:
        """
        指定したファイルをダウンロードしてファイルに保存する関数

        Parameters:
            url (str): 対象のダウンロード元のURL
            file_name (str): 保存先のファイル名(プレフィックス含む)
            bucket_name (str): 保存先のバケット名(デフォルトは"default")

        Reference:
            - ストレージ機能は未実装なので現在はstorageの指定はできません。
        """

        # ストレージの初期化
        storage = LocalStorage(bucket_name=bucket_name)

        # URLからデータを取得
        response = requests.get(url)
        response.raise_for_status()  # 失敗時に例外を投げる

        # ダウンロードしたデータをバイナリでストレージに保存
        storage.upload_bytes(response.content, file_name)
        return file_name

    @staticmethod
    @tool(tags=["file", "hearing"])
    def tool_file_save_from_content(
        content: str,
        file_name: str,
        bucket_name: str = "default",
        content_type: str = "text",
    ) -> str:
        """
        コンテンツを指定したファイルに保存する関数

        Args:
            url (str): 対象のダウンロード元のURL
            file_name (str): 保存先のファイル名(プレフィックス含む)
            bucket_name (str): 保存先のバケット名
            content_type (str): コンテンツのタイプ(["text"|"base64"])
        Reference:
            - ストレージ機能は未実装なので現在はstorageの指定はできません。
        """

        # ストレージの初期化
        storage = LocalStorage(bucket_name=bucket_name)
        if content_type == "text":
            # テキストコンテンツを保存
            storage.upload_bytes(content.encode("utf-8"), file_name)
        elif content_type == "base64":
            # Base64エンコードされたコンテンツをデコードして保存
            import base64

            decoded_content = base64.b64decode(content)
            storage.upload_bytes(decoded_content, file_name)
        else:
            raise ValueError("content_typeは'text'または'base64'を指定してください。")

        return f"file_name: {file_name} bucket_name: {bucket_name} に保存しました。"
