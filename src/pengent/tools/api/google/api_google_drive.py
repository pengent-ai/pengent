import json
import os
import io
from typing import List, Union

from ....utility.storage.storage_base import StorageBase


class ApiGoogleDrive(StorageBase):
    """Google DriveストレージAPIクラス"""

    def __init__(self, folder_id: str = None, token_file: str = "token.json", **kwargs):
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
        except ImportError as e:
            raise ImportError(
                "google-api-python-client and google-auth are required."
            ) from e

        super().__init__(folder_id, **kwargs)
        self.folder_id = folder_id

        if not os.path.exists(token_file):
            raise FileNotFoundError(f"Token file not found: {token_file}")

        with open(token_file, "r", encoding="utf-8") as f:
            creds_data = json.load(f)

        self.creds = Credentials.from_authorized_user_info(creds_data)

        # 期限切れなら refresh（refresh_token がある前提）
        if self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())

        self.service = build("drive", "v3", credentials=self.creds)

    def upload_file(self, file_path: str, object_name: str = None) -> str:
        from googleapiclient.http import MediaFileUpload

        name = object_name or os.path.basename(file_path)
        file_metadata = {"name": name}
        if self.folder_id:
            file_metadata["parents"] = [self.folder_id]

        media = MediaFileUpload(file_path, resumable=True)
        res = (
            self.service.files()
            .create(body=file_metadata, media_body=media, fields="id,name")
            .execute()
        )
        return res["id"]

    def upload_bytes(self, data: bytes, object_name: str) -> str:
        from googleapiclient.http import MediaIoBaseUpload

        file_metadata = {"name": object_name}
        if self.folder_id:
            file_metadata["parents"] = [self.folder_id]

        fh = io.BytesIO(data)
        media = MediaIoBaseUpload(
            fh, mimetype="application/octet-stream", resumable=True
        )
        res = (
            self.service.files()
            .create(body=file_metadata, media_body=media, fields="id,name")
            .execute()
        )
        return res["id"]

    def read_bytes(self, object_name: str) -> bytes:
        """
        Google Drive上のファイルを bytes として読み込む
        """
        from googleapiclient.http import MediaIoBaseDownload

        file_id = self._get_file_id_by_name(object_name)
        request = self.service.files().get_media(fileId=file_id)

        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        return buf.getvalue()

    def read_json(self, object_name: str) -> Union[dict, list]:
        """
        JSON / JSONL を自動判別して読み込む
        - .jsonl / .ndjson / .jsonlines / .jl は JSONL として扱う
        - それ以外は通常JSONとして扱う
        """
        raw = self.read_bytes(object_name)

        # 文字コードは基本 utf-8 想定（必要なら kwargs で変更可能に）
        text = raw.decode("utf-8-sig")  # BOM付きも吸収

        lower = object_name.lower()
        is_jsonl = lower.endswith((".jsonl", ".ndjson", ".jsonlines", ".jl"))

        if is_jsonl:
            # 空行は無視して 1行=1JSON として読み込む
            items = []
            for line_no, line in enumerate(text.splitlines(), start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Invalid JSONL at line {line_no} in '{object_name}': {e}"
                    ) from e
            return items

        # 通常JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in '{object_name}': {e}") from e
        

    def download_file(self, object_name: str, dest_path: str) -> None:
        from googleapiclient.http import MediaIoBaseDownload

        file_id = self._get_file_id_by_name(object_name)
        request = self.service.files().get_media(fileId=file_id)

        with io.FileIO(dest_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

    def delete_file(self, object_name: str) -> None:
        file_id = self._get_file_id_by_name(object_name)
        self.service.files().delete(fileId=file_id).execute()

    def list_files(self, prefix: str = "") -> List[str]:
        # trashed除外 + フォルダ絞り込み推奨
        q_parts = ["trashed = false"]
        if prefix:
            q_parts.append(f"name contains '{prefix}'")
        if self.folder_id:
            q_parts.append(f"'{self.folder_id}' in parents")

        query = " and ".join(q_parts)
        results = (
            self.service.files()
            .list(q=query, fields="files(id, name)", spaces="drive")
            .execute()
        )
        return [f["name"] for f in results.get("files", [])]

    def exists_file(self, object_name: str) -> bool:
        try:
            self._get_file_id_by_name(object_name)
            return True
        except FileNotFoundError:
            return False

    def _get_file_id_by_name(self, object_name: str) -> str:
        # 同名があるので folder_id 絞り込み + trashed除外
        q_parts = [f"name = '{object_name}'", "trashed = false"]
        if self.folder_id:
            q_parts.append(f"'{self.folder_id}' in parents")
        query = " and ".join(q_parts)

        results = (
            self.service.files()
            .list(
                q=query,
                fields="files(id, name, modifiedTime)",
                spaces="drive",
                orderBy="modifiedTime desc",
                pageSize=1,
            )
            .execute()
        )
        files = results.get("files", [])
        if not files:
            raise FileNotFoundError(f"File '{object_name}' not found on Google Drive.")
        return files[0]["id"]
