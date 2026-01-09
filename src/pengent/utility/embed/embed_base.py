from abc import ABC, abstractmethod
from typing import Union, List


class EmbedderBase(ABC):
    """
    埋め込み(ベクトル化)機能を共通化するためのベースクラス。

    Notes:
        - テキストをベクトルに変換する共通インターフェースを提供します。
        - 各埋め込みエンジンはこのクラスを継承して実装します。
    """

    @abstractmethod
    def encode(
        self, texts: Union[str, List[str]], to_numpy: bool = False
    ) -> Union[List[float], List[List[float]]]:
        """
        テキストをベクトル化するメソッド。

        Args:
            texts (Union[str, List[str]]): ベクトル化対象のテキストまたはリスト
            to_numpy (bool, optional): numpy形式で出力するか。デフォルトはFalse。

        Returns:
            Union[List[float], List[List[float]]]: 1つまたは複数のベクトル
        """
        pass
