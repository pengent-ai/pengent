import os
import json

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from ....lib.custom_logger import get_logger

logger = get_logger()


class ApiGoogleDocs:
    """Google Docs APIクライアント"""
    def __init__(self, token_file: str = "token.json"):
        if not os.path.exists(token_file):
            raise FileNotFoundError(f"Token file not found: {token_file}")
        with open(token_file, "r") as f:
            creds_data = json.load(f)
        self.creds = Credentials.from_authorized_user_info(creds_data)
        self.service = build("docs", "v1", credentials=self.creds)

    def create_document(self, title: str = "New Document") -> dict:
        """新しいドキュメントを作成します"""
        doc = self.service.documents().create(body={"title": title}).execute()
        return doc

    def insert_text(self, document_id: str, text: str, index: int = 1):
        """指定した位置にテキストを挿入します"""
        requests = [{"insertText": {"location": {"index": index}, "text": text}}]
        self.service.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()
