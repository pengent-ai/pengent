from ....type.rag_block import (
    AnyBlock,
    HeadingBlock,
    TextBlock,
)


class TextFAQParser:
    """
    テキストを解析してブロックに分割するクラス(FAQ)
    """

    @classmethod
    def parse(cls, text: str) -> list[AnyBlock]:
        """
        テキストを改行で分割してリストに変換する
        """
        blocks: list[AnyBlock] = []
        lines = text.splitlines()
        for line in lines:
            # 質問と回答を判定
            if line.startswith(("Q:", "Q．", "Q.", "質問", "？", "?")):
                blocks.append(HeadingBlock(content=line))
            elif line.startswith(("A:", "A．", "A.", "回答", "答え")):
                blocks.append(TextBlock(content=line))
            else:
                # それ以外は直前のtypeと同じと仮定して追記 or paragraphとして扱う
                if blocks and isinstance(blocks[-1], TextBlock):
                    blocks[-1].content += "\n" + line
                else:
                    blocks.append(TextBlock(content=line))

        return blocks
