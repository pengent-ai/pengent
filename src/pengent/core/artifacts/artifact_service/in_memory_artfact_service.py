from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import uuid
from .base_artifact_service import ArtifactServiceBase
from ..artifact import ArtifactBase


@dataclass
class _InMemoryArtifact:
    artifact_id: str
    filename: str
    session_id: Optional[str]
    version: int
    mime_type: str
    data: ArtifactBase
    created_at: datetime
    metadata: dict[str, Any]


class InMemoryArtifactService(ArtifactServiceBase):
    """In-memory implementation of ArtifactServiceBase"""

    def __init__(self) -> None:
        self._store: dict[
            str, dict[Optional[str], dict[str, list[_InMemoryArtifact]]]
        ] = {}

    def _get_session_bucket(
        self, user_id: str, session_id: Optional[str]
    ) -> dict[str, list[_InMemoryArtifact]]:
        user_bucket = self._store.setdefault(user_id, {})
        return user_bucket.setdefault(session_id, {})

    def _find_version(
        self,
        *,
        user_id: str,
        session_id: Optional[str],
        filename: str,
        version: Optional[int],
    ) -> Optional[_InMemoryArtifact]:
        versions = self._store.get(user_id, {}).get(session_id, {}).get(filename, [])
        if not versions:
            return None
        if version is None:
            return versions[-1]
        return next((item for item in versions if item.version == version), None)

    def save_artifact(
        self,
        *,
        user_id: str,
        filename: str,
        artifact: ArtifactBase,
        session_id: Optional[str] = None,
        custom_metadata: Optional[dict[str, Any]] = None,
    ) -> int:
        versions = self._get_session_bucket(user_id, session_id).setdefault(
            filename, []
        )
        version = len(versions) + 1
        record = _InMemoryArtifact(
            artifact_id=str(uuid.uuid4()),
            filename=filename,
            session_id=session_id,
            version=version,
            mime_type=artifact.mime_type,
            data=artifact,
            created_at=datetime.now(),
            metadata=custom_metadata or {},
        )
        versions.append(record)
        return version

    def load_artifact(
        self,
        *,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Optional[ArtifactBase]:
        record = self._find_version(
            user_id=user_id,
            session_id=session_id,
            filename=filename,
            version=version,
        )
        return record.data if record else None

    def list_artifacts_keys(
        self,
        *,
        user_id: str,
        session_id: Optional[str] = None,
    ) -> list[str]:
        session_bucket = self._store.get(user_id, {}).get(session_id, {})
        return sorted(session_bucket.keys())

    async def delete_artifacts(
        self,
        *,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
    ) -> None:
        user_bucket = self._store.get(user_id)
        if not user_bucket:
            return
        session_bucket = user_bucket.get(session_id)
        if not session_bucket or filename not in session_bucket:
            return
        del session_bucket[filename]
        if not session_bucket:
            user_bucket.pop(session_id, None)
        if not user_bucket:
            self._store.pop(user_id, None)

    def list_versions(
        self,
        *,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
    ) -> list[int]:
        versions = self._store.get(user_id, {}).get(session_id, {}).get(filename, [])
        return [item.version for item in versions]

    def get_artifact_version(
        self,
        *,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Optional[dict[str, Any]]:
        record = self._find_version(
            user_id=user_id,
            session_id=session_id,
            filename=filename,
            version=version,
        )
        if not record:
            return None
        return {
            "artifact_id": record.artifact_id,
            "filename": record.filename,
            "session_id": record.session_id,
            "mime_type": record.mime_type,
            "version": record.version,
            "created_at": record.created_at,
            "metadata": record.metadata,
        }
