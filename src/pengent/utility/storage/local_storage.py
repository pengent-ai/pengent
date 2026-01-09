from typing import Union
from .storage_base import StorageBase
from ...lib.custom_logger import get_logger

logger = get_logger()


import os


class LocalStorage(StorageBase):
    """
    ローカルストレージAPIクラス

    Notes:
        - ローカルディレクトリをストレージとして扱う実装です。
        - `.storage/default/{bucket_name}` 以下に保存されます。
    """

    BASE_STORAGE_DIR = ".data/.storage"

    def __init__(self, bucket_name: str, **kwargs):
        """
        コンストラクタ

        Args:
            bucket_name (str): 使用するローカルディレクトリ名(必須)
            **kwargs: 予備パラメータ(未使用)
        """
        if not bucket_name:
            raise ValueError("bucket_nameは必須です")

        self.bucket_name = bucket_name
        self.storage_path = os.path.join(self.BASE_STORAGE_DIR, bucket_name)
        os.makedirs(self.storage_path, exist_ok=True)

    def upload_file(self, file_path: str, object_name: str = None) -> None:
        """
        ファイルをローカルストレージにアップロードするメソッド
        """
        if object_name is None:
            object_name = os.path.basename(file_path)

        dest_path = os.path.join(self.storage_path, object_name)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        with open(file_path, "rb") as src_file, open(dest_path, "wb") as dest_file:
            dest_file.write(src_file.read())

    def upload_bytes(self, data: bytes, object_name: str) -> None:
        """バイナリデータを直接ローカルストレージに保存するメソッド"""
        dest_path = os.path.join(self.storage_path, object_name)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        with open(dest_path, "wb") as dest_file:
            dest_file.write(data)

    def read_bytes(self, object_name: str) -> bytes:
        """ストレージからバイナリデータを直接読み込むメソッド"""
        file_path = os.path.join(self.storage_path, object_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ファイルが存在しません: {object_name}")

        with open(file_path, "rb") as src_file:
            return src_file.read()

    def read_json(self, object_name: str) -> Union[dict | list]:
        """ストレージからJSON(JSONL)データを直接読み込むメソッド"""
        import json

        file_path = os.path.join(self.storage_path, object_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ファイルが存在しません: {object_name}")

        with open(file_path, "r", encoding="utf-8") as src_file:
            if object_name.endswith(".jsonl"):
                return [json.loads(line) for line in src_file]
            else:
                return json.load(src_file)

    def download_file(self, object_name: str, dest_path: str) -> None:
        """
        ローカルストレージからファイルをダウンロードするメソッド
        """
        src_path = os.path.join(self.storage_path, object_name)
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"ファイルが存在しません: {object_name}")

        # 修正ポイント
        dest_dir = os.path.dirname(dest_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        with open(src_path, "rb") as src_file, open(dest_path, "wb") as dest_file:
            dest_file.write(src_file.read())

    def delete_file(self, object_name: str) -> None:
        """
        ローカルストレージからファイルを削除するメソッド
        """
        file_path = os.path.join(self.storage_path, object_name)
        if os.path.exists(file_path):
            os.remove(file_path)

    def list_files(self, prefix: str = "") -> list:
        """
        ローカルストレージ内のファイル一覧を取得するメソッド
        """
        files = []
        base_path = os.path.join(self.storage_path, prefix)
        for root, _, filenames in os.walk(base_path):
            for filename in filenames:
                rel_path = os.path.relpath(
                    os.path.join(root, filename), self.storage_path
                )
                files.append(rel_path)
        return files

    def exists_file(self, object_name: str) -> bool:
        """
        指定したファイルがローカルストレージに存在するかを確認するメソッド

        Args:
            object_name (str): 確認対象のオブジェクト名

        Returns:
            bool: 存在する場合はTrue、存在しない場合はFalse
        """
        file_path = os.path.join(self.storage_path, object_name)
        return os.path.exists(file_path)
