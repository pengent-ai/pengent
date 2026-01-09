import os
import importlib.util
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, registry, Session
from typing import Optional, Generator
from contextlib import contextmanager

# グローバルで使えるBaseを定義
Base: registry = declarative_base()


class Database:
    """データベース接続とセッション管理を行うクラス"""

    def __init__(self, database_url: Optional[str] = None, is_create_all: bool = True):
        self.db_url = database_url or os.getenv(
            "DATABASE_URL", "sqlite:///./.data/pengent.db"
        )
        if not self.db_url:
            raise ValueError(
                "DATABASE_URL is not set. Please provide a valid database URL."
            )
        self.engine = create_engine(self.db_url, echo=False, future=True)
        self.SessionLocal = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False
        )
        if is_create_all:
            self.create_all()

    def create_all(self):
        """
        データベースの全テーブルを作成するメソッド
        """
        try:
            Base.metadata.create_all(bind=self.engine)
        except Exception as e:
            raise RuntimeError(f"Failed to create database tables: {e}") from e

    def local_session(self) -> Session:
        """
        ローカルデータベースセッションを取得するメソッド

        Returns:
            Session: ローカルデータベースセッション
        """
        return self.SessionLocal()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        データベースセッションを取得するメソッド

        Returns:
            Session: データベースセッション
        """
        db_session = self.SessionLocal()
        try:
            yield db_session
        except Exception as e:
            db_session.rollback()
            raise RuntimeError(f"Failed to create database session: {e}") from e
        finally:
            db_session.close()

    @classmethod
    def create_database(
        cls,
        db_type: str = "sqlite",
        username: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db_name: Optional[str] = None,
        filepath: Optional[str] = "./.data/pengent.db",
    ):
        """
        データベースのURLを生成し、Databaseインスタンスを作成するクラスメソッド

        Args:
            db_type (str): DBタイプ(例: "sqlite", "postgresql", "mysql" etc.)
            username (Optional[str]): ユーザー名(PostgreSQLやMySQLの場合)
            password (Optional[str]): パスワード(PostgreSQLやMySQLの場合)
            host (Optional[str]): ホスト名(PostgreSQLやMySQLの場合)
            port (Optional[int]): ポート番号(PostgreSQLやMySQLの場合)
            db_name (Optional[str]): データベース名(PostgreSQLやMySQLの場合)
            filepath (Optional[str]): SQLiteのファイルパス
        Returns:
            Database: Databaseクラスのインスタンス
        """
        if db_type == "sqlite":
            url = f"sqlite:///{filepath}"
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        elif db_type == "mysql":
            port = port or 3306
            host = host or "localhost"
            if importlib.util.find_spec("pymysql") is None:
                raise ImportError("`pip install pymysql cryptography` が必要です")

            url = f"mysql+pymysql://{username}:{password}@{host}:{port}/{db_name}"
        elif db_type == "postgresql":
            port = port or 5432
            if importlib.util.find_spec("psycopg2") is None:
                raise ImportError("`pip install psycopg2-binary` が必要です")

            url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{db_name}"
        else:
            raise ValueError(f"Unsupported db_type: {db_type}")

        return cls(database_url=url)
