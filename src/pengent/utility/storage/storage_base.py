from typing import Union
from abc import ABC, abstractmethod


class StorageBase(ABC):
    """
    ストレージAPIのベースクラス

    Notes:
        - ストレージサービスを統一的に扱うためのインターフェースを提供します
        - LocalStorage、MinIO、Google Cloud Storage、S5に対応予定。
        - 各ストレージサービスは、このベースクラスを継承して作成します。
    """

    def __init__(self, bucket_name: str = None, **kwargs):
        """
        コンストラクタ

        Args:
            bucket_name (str, optional): 操作対象のバケット名またはコンテナ名
            **kwargs: ストレージクライアントに必要なパラメータ

        Notes:
            - bucket_nameは、ストレージサービスに依存する場合があります。
        """
        self.bucket_name = bucket_name

    @abstractmethod
    def upload_file(self, file_path: str, object_name: str = None) -> None:
        """
        ファイルをストレージにアップロードするメソッド

        Args:
            file_path (str): ローカルファイルのパス
            object_name (str, optional): ストレージ上のオブジェクト名
              - 省略時はfile_pathと同名
        """
        pass

    @abstractmethod
    def upload_bytes(self, data: bytes, object_name: str) -> None:
        """
        バイナリデータを直接ストレージに保存するメソッド

        Args:
            object_name (str, optional): ストレージ上のオブジェクト名
              - 省略時はfile_pathと同名
        """
        pass

    @abstractmethod
    def read_bytes(self, object_name: str) -> bytes:
        """
        ストレージからバイナリデータを直接読み込むメソッド

        Args:
            object_name (str): 読み込むオブジェクト名

        Returns:
            bytes: 読み込んだバイナリデータ
        """
        pass

    @abstractmethod
    def read_json(self, object_name: str) -> Union[dict | list]:
        """
        ストレージからJSON(JSONL)データを直接読み込むメソッド

        Args:
            object_name (str): 読み込むオブジェクト名

        Returns:
            Union[dict | list]: 読み込んだJSONデータ
        """
        pass

    @abstractmethod
    def download_file(self, object_name: str, dest_path: str) -> None:
        """
        ストレージからファイルをダウンロードするメソッド

        Args:
            object_name (str): ダウンロードするオブジェクト名
            dest_path (str): ダウンロード先のローカルパス
        """
        pass

    @abstractmethod
    def delete_file(self, object_name: str) -> None:
        """
        ストレージからファイルを削除するメソッド

        Args:
            object_name (str): 削除するオブジェクト名
        """
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> list[str]:
        """
        ストレージ内のファイル一覧を取得するメソッド

        Args:
            prefix (str, optional): 絞り込み対象のプレフィックス

        Returns:
            list: オブジェクト名のリスト
        """
        pass

    @abstractmethod
    def exists_file(self, object_name: str) -> bool:
        """
        指定したファイルがストレージに存在するかを確認するメソッド

        Args:
            object_name (str): 確認対象のオブジェクト名

        Returns:
            bool: 存在する場合はTrue、存在しない場合はFalse
        """
