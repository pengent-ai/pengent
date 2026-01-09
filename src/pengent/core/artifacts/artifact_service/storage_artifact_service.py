from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from .base_artifact_service import ArtifactServiceBase
from ..artifact import ArtifactBase
from ....utility.storage import StorageBase, LocalStorage

GLOBAL_SESSION_KEY = "__global__"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _session_key(session_id: Optional[str]) -> str:
    return session_id or GLOBAL_SESSION_KEY


@dataclass(frozen=True)
class _ArtifactMeta:
    artifact_id: str
    filename: str
    session_id: Optional[str]
    version: int
    mime_type: str
    created_at: str
    metadata: dict[str, Any]


class StorageArtifactService(ArtifactServiceBase):
    """ストレージベースのアーティファクトサービス

    ファイル構造:
        {user_id}/{session_id}/{filename}/{version}/meta_info.json
        {user_id}/{session_id}/{filename}/{version}/{filename}
    """

    def __init__(self, storage: StorageBase = None):
        if storage:
            self.storage = storage
        else:
            self.storage = LocalStorage(bucket_name="artifact")

    def _build_base_path(
        self, user_id: str, session_id: Optional[str], filename: str
    ) -> str:
        """ベースパスを構築"""
        session = _session_key(session_id)
        return f"{user_id}/{session}/{filename}"

    def _build_version_path(
        self,
        user_id: str,
        session_id: Optional[str],
        filename: str,
        version: int,
    ) -> str:
        """バージョンパスを構築"""
        base = self._build_base_path(user_id, session_id, filename)
        return f"{base}/{version}"

    def _build_meta_path(
        self,
        user_id: str,
        session_id: Optional[str],
        filename: str,
        version: int,
    ) -> str:
        """メタデータパスを構築"""
        version_path = self._build_version_path(user_id, session_id, filename, version)
        return f"{version_path}/meta_info.json"

    def _build_data_path(
        self,
        user_id: str,
        session_id: Optional[str],
        filename: str,
        version: int,
    ) -> str:
        """データパスを構築"""
        version_path = self._build_version_path(user_id, session_id, filename, version)
        return f"{version_path}/{filename}"

    def _get_latest_version(
        self, user_id: str, session_id: Optional[str], filename: str
    ) -> Optional[int]:
        """最新のバージョン番号を取得"""
        base_path = self._build_base_path(user_id, session_id, filename)
        try:
            files = self.storage.list_files(prefix=base_path)
            versions = set()
            for file in files:
                # base_path/{version}/... から version を抽出
                parts = file.replace(base_path + "/", "").split("/")
                if parts and parts[0].isdigit():
                    versions.add(int(parts[0]))
            return max(versions) if versions else None
        except Exception:
            return None

    def _save_meta(self, meta: _ArtifactMeta, meta_path: str) -> None:
        """メタデータを保存"""
        meta_dict = asdict(meta)
        meta_json = json.dumps(meta_dict, ensure_ascii=False, indent=2)
        self.storage.upload_bytes(meta_json.encode("utf-8"), meta_path)

    def _load_meta(self, meta_path: str) -> Optional[_ArtifactMeta]:
        """メタデータを読み込み"""
        try:
            meta_dict = self.storage.read_json(meta_path)
            return _ArtifactMeta(**meta_dict)
        except Exception:
            return None

    def save_artifact(
        self,
        *,
        user_id: str,
        filename: str,
        artifact: ArtifactBase,
        session_id: Optional[str] = None,
        custom_metadata: Optional[dict[str, Any]] = None,
    ) -> int:
        """アーティファクトを保存"""
        # 最新バージョンを取得して +1
        latest = self._get_latest_version(user_id, session_id, filename)
        version = (latest or 0) + 1

        # メタデータを作成
        meta = _ArtifactMeta(
            artifact_id=str(uuid.uuid4()),
            filename=filename,
            session_id=session_id,
            version=version,
            mime_type=artifact.mime_type,
            created_at=_now_iso(),
            metadata=custom_metadata or {},
        )

        # パスを構築
        meta_path = self._build_meta_path(user_id, session_id, filename, version)
        data_path = self._build_data_path(user_id, session_id, filename, version)

        # メタデータを保存
        self._save_meta(meta, meta_path)

        # データを保存
        if artifact.text is not None:
            self.storage.upload_bytes(artifact.text.encode("utf-8"), data_path)
        elif artifact.blob is not None:
            self.storage.upload_bytes(artifact.blob, data_path)
        return version

    def load_artifact(
        self,
        *,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Optional[ArtifactBase]:
        """アーティファクトを読み込み"""
        # バージョンが指定されていない場合は最新を取得
        if version is None:
            version = self._get_latest_version(user_id, session_id, filename)
            if version is None:
                return None

        # メタデータを読み込み
        meta_path = self._build_meta_path(user_id, session_id, filename, version)
        meta = self._load_meta(meta_path)
        if not meta:
            return None

        # データを読み込み
        data_path = self._build_data_path(user_id, session_id, filename, version)
        try:
            data = self.storage.read_bytes(data_path)

            # mime_typeに応じて適切なArtifactBaseを構築
            if meta.mime_type.startswith("text/"):
                return ArtifactBase(mime_type=meta.mime_type, text=data.decode("utf-8"))
            else:
                return ArtifactBase(mime_type=meta.mime_type, blob=data)
        except Exception:
            return None

    def list_artifacts_keys(
        self,
        *,
        user_id: str,
        session_id: Optional[str] = None,
    ) -> list[str]:
        """アーティファクトの一覧を取得"""
        session = _session_key(session_id)
        prefix = f"{user_id}/{session}/"

        try:
            files = self.storage.list_files(prefix=prefix)
            # {user_id}/{session}/{filename}/{version}/... から filename を抽出
            filenames = set()
            for file in files:
                parts = file.replace(prefix, "").split("/")
                if len(parts) >= 2:
                    filenames.add(parts[0])
            return sorted(filenames)
        except Exception:
            return []

    async def delete_artifacts(
        self,
        *,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
    ) -> None:
        """アーティファクトを削除（全バージョン）"""
        base_path = self._build_base_path(user_id, session_id, filename)

        try:
            files = self.storage.list_files(prefix=base_path)
            for file in files:
                self.storage.delete_file(file)
        except Exception:
            pass

    def list_versions(
        self,
        *,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
    ) -> list[int]:
        """アーティファクトの全バージョンを一覧表示"""
        base_path = self._build_base_path(user_id, session_id, filename)

        try:
            files = self.storage.list_files(prefix=base_path)
            versions = set()
            for file in files:
                parts = file.replace(base_path + "/", "").split("/")
                if parts and parts[0].isdigit():
                    versions.add(int(parts[0]))
            return sorted(versions)
        except Exception:
            return []

    def get_artifact_version(
        self,
        *,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Optional[dict[str, Any]]:
        """アーティファクトの特定バージョンのメタデータを取得"""
        # バージョンが指定されていない場合は最新を取得
        if version is None:
            version = self._get_latest_version(user_id, session_id, filename)
            if version is None:
                return None

        meta_path = self._build_meta_path(user_id, session_id, filename, version)
        meta = self._load_meta(meta_path)
        if not meta:
            return None

        return {
            "artifact_id": meta.artifact_id,
            "filename": meta.filename,
            "session_id": meta.session_id,
            "mime_type": meta.mime_type,
            "version": meta.version,
            "created_at": meta.created_at,
            "metadata": meta.metadata,
        }
