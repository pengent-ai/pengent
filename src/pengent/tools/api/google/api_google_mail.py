import os
import json
import base64
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class ApiGoogleMail:
    """Google Mail APIクライアント"""
    
    def __init__(self, token_file: str = "token.json"):
        if not os.path.exists(token_file):
            raise FileNotFoundError(f"Token file not found: {token_file}")
        with open(token_file, "r") as f:
            creds_data = json.load(f)
        self.creds = Credentials.from_authorized_user_info(creds_data)
        self.service = build("gmail", "v1", credentials=self.creds)

    def send_mail(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
    ) -> str:
        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject
        if from_email:
            message["from"] = from_email

        message.attach(MIMEText(body, "plain"))
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        result = (
            self.service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )

        return result.get("id", "unknown")
