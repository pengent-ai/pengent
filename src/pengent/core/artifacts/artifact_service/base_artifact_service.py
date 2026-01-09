from abc import ABC, abstractmethod
from typing import Any, Optional
from ..artifact import ArtifactBase


class ArtifactServiceBase(ABC):
    """アーティファクトサービスの基底クラス"""

    @abstractmethod
    def save_artifact(
        self,
        *,
        user_id: str,
        filename: str,
        artifact: ArtifactBase,
        session_id: Optional[str] = None,
        custom_metadata: Optional[dict[str, Any]] = None,
    ) -> int:
        """アーティファクトを保存する抽象メソッド

        Args:
            user_id: ユーザーの一意な識別子
            filename: アーティファクトの名前(ファイル名など)
            artifact: 保存するアーティファクトの内容
            session_id: アーティファクトが関連付けられたセッションID(オプション)
            custom_metadata: カスタムメタデータ辞書(オプション)

        Returns:
            保存されたアーティファクトのバージョン番号
        """
        pass

    @abstractmethod
    def load_artifact(
        self,
        *,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Optional[ArtifactBase]:
        """アーティファクトを読み込む抽象メソッド

        Args:
            user_id: ユーザーの一意な識別子
            filename: アーティファクトの名前(ファイル名など)
            session_id: アーティファクトが関連付けられたセッションID(オプション)
            version: 読み込むアーティファクトのバージョン番号(オプション)

        Returns:
            読み込んだアーティファクトの内容、存在しない場合はNone
        """
        pass

    @abstractmethod
    def list_artifacts_keys(
        self,
        *,
        user_id: str,
        session_id: Optional[str] = None,
    ) -> list[str]:
        """アーティファクトの一覧を取得する抽象メソッド

        Args:
            user_id: ユーザーの一意な識別子
            session_id: アーティファクトが関連付けられたセッションID(オプション)

        Returns:
            アーティファクトの名前リスト
        """
        pass

    @abstractmethod
    async def delete_artifacts(
        self,
        *,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
    ) -> None:
        """アーティファクトを削除する抽象メソッド

        Args:
            user_id: ユーザーの一意な識別子
            filename: アーティファクトの名前(ファイル名など)
            session_id: アーティファクトが関連付けられたセッションID(オプション)
        """
        pass

    @abstractmethod
    def list_versions(
        self,
        *,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
    ) -> list[int]:
        """アーティファクトの全バージョンを一覧表示する抽象メソッド

        Args:
            user_id: ユーザーの一意な識別子
            filename: アーティファクトの名前(ファイル名など)
            session_id: アーティファクトが関連付けられたセッションID(オプション)

        Returns:
            アーティファクトの全バージョン番号のリスト
        """
        pass

    @abstractmethod
    def get_artifact_version(
        self,
        *,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
        version: Optional[int] = None,
    ) -> list[int]:
        """
        アーティファクトの特定バージョンのメタデータを取得する抽象メソッド

        Args:
            user_id: ユーザーの一意な識別子
            filename: アーティファクトの名前(ファイル名など)
            session_id: アーティファクトが関連付けられたセッションID(オプション)
            version: 取得するアーティファクトのバージョン番号(オプション)
        Returns:
            指定されたアーティファクトバージョンのメタデータ、存在しない場合はNone
        """


class ExecutionArtifactService:
    """通常のArtifactServiceに加えて、ユーザーIDを保持するラッパークラス"""

    def __init__(self, base: ArtifactServiceBase, user_id: str, session_id: str):
        self._base: ArtifactServiceBase = base
        self.__user_id = user_id
        self.__session_id = session_id

    def save(
        self,
        file_name: str,
        artifact: ArtifactBase,
        custom_meta: dict = None,
    ) -> int:
        """ArtifactServiceのsaveメソッドを呼び出す"""
        return self._base.save_artifact(
            user_id=self.__user_id,
            filename=file_name,
            artifact=artifact,
            session_id=self.__session_id,
            custom_metadata=custom_meta,
        )

    def load(
        self,
        file_name: str,
        version: int = None,
    ) -> Optional[ArtifactBase]:
        """ArtifactServiceのloadメソッドを呼び出す"""
        return self._base.load_artifact(
            user_id=self.__user_id,
            filename=file_name,
            session_id=self.__session_id,
            version=version,
        )
