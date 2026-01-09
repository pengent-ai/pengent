from pydantic import Field, BaseModel, model_validator
from typing import Literal, Optional
import mimetypes
import requests


class ArtifactBase(BaseModel):
    """アーティファクトを表すクラス"""

    mime_type: str
    text: Optional[str] = Field(None, description="テキストデータ")
    blob: Optional[bytes] = Field(None, description="バイナリデータ")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} mime_type={self.mime_type!r}>"

    def __str__(self) -> str:
        # logger.info(f"{artifact}") 用
        return self.__repr__()

    @model_validator(mode="after")
    def validate_single_payload(self):
        values = [self.text, self.blob]
        if sum(v is not None for v in values) != 1:
            raise ValueError("Artifact must have exactly one of text, url, or blob")
        return self


class ArtifactText(ArtifactBase):
    """テキストアーティファクトを表すクラス"""

    mime_type: Literal["text/plain"] = "text/plain"
    text: str


class ArtifactBlob(ArtifactBase):
    """バイナリアーティファクトを表すクラス"""

    mime_type: str = "application/octet-stream"
    blob: bytes

    @classmethod
    def create_blob_from_file(cls, file_path: str, mime_type: str = None):
        """ファイルからバイナリアーティファクトを作成する"""
        # ファイルの拡張子からMIMEタイプを推測する
        if mime_type is None:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

        with open(file_path, "rb") as f:
            blob_data = f.read()
        return cls(mime_type=mime_type, blob=blob_data)

    @classmethod
    def create_blob_from_url(
        cls,
        url: str,
        header: Optional[dict[str, str]] = None,
    ):
        """URLからバイナリアーティファクトを作成する"""
        response = requests.get(url, headers=header)
        response.raise_for_status()  # 失敗時に例外を投げる
        content_type = response.headers.get("Content-Type", "application/octet-stream")
        mime_type = content_type.split(";", 1)[0].strip()
        return cls(mime_type=mime_type, blob=response.content)
