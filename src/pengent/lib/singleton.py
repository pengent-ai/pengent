"""Singleton pattern implementation in Python.

This implementation is thread-safe and ensures
that only one instance of the class is created.

Singleton が提供するのは「同じインスタンスを返す仕組み」
* __init__() は毎回呼ばれる(多くの人が意図しない動作)
* __init__の2回目は_initialized というフラグは 使う側で管理する必要がある。
"""

import threading


class Singleton(object):
    """Singletonパターンの実装クラス"""
    _instances = {}
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:  # ダブルチェック
                    cls._instances[cls] = super(Singleton, cls).__new__(cls)
        return cls._instances[cls]
