import re
import base64
import mimetypes
from typing import Tuple

_DATA_URL_RE = re.compile(r"^data:(?P<mime>[^;]+);base64,(?P<b64>[A-Za-z0-9+/=]+)$")


def strip_json_fence(text: str) -> str:
    """
    テキストが先頭と末尾で ```json ... ``` 形式で囲まれている場合に、
    その囲いを取り除いて中身だけ返す。マッチしなければそのまま返す。
    """
    match = re.fullmatch(r"\s*```json\s*(.*?)\s*```\s*", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def encode_base64_from_binary(
    data: bytes,
    mime_type: str = None,
    file_path: str = None,
) -> Tuple[str, str]:
    """
    指定されたファイルを読み込み、Base64エンコードした文字列を返す

    Args:
        data (bytes): エンコードするバイナリデータ
        mime_type (str): データのMIMEタイプ
        file_path (str): 元のファイルパス（MIMEタイプ推測用）
    Returns:
        Tuple[str, str]: エンコードされたBase64文字列とMIMEタイプ
    """
    encoded = base64.b64encode(data).decode("utf-8")
    if mime_type is None:
        if file_path:
            mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"

    return encoded, mime_type


def encode_base64_from_file(
    file_path: str,
    mime_type: str = None,
) -> str:
    """
    指定されたファイルを読み込み、Base64エンコードした文字列を返す

    Args:
        file_path (str): エンコードするファイルのパス
        mime_type (str): ファイルのMIMEタイプ
    """
    with open(file_path, "rb") as file:
        data = file.read()

    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"

    return encode_base64_from_binary(data, mime_type)
