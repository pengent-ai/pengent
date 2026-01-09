"""
ユーリティ関数(カテゴライズ)
エージェントのカテゴライズ機能を提供するモジュールです。
"""

from dataclasses import dataclass
from ...type.llm.llm_message import LLMMessage
from ...type.llm.llm_response import LLMResponse
from typing import List, Union
from ...llm import LLMClientBase, LLMOpenAIClient


@dataclass
class CategoryLabel:
    """カテゴリラベルのデータクラス"""

    name: str
    description: str = None

    def __str__(self):
        if self.description:
            return f"{self.name}: {self.description}"
        return self.name


def categorize(
    labels: List[Union[CategoryLabel, dict, str]],
    messages: List[LLMMessage],
    llm_client: LLMClientBase = None,
    attempt: int = 3,
) -> str:
    if not labels:
        raise ValueError("labels must not be empty")
    if attempt < 1:
        raise ValueError("attempt must be >= 1")

    # labels -> _labels
    if isinstance(labels[0], dict):
        _labels = [CategoryLabel(**label) for label in labels]  # type: ignore[arg-type]
    elif isinstance(labels[0], str):
        _labels = [CategoryLabel(name=label) for label in labels]  # type: ignore[arg-type]
    else:
        _labels = labels  # type: ignore[assignment]

    label_names = [label.name for label in _labels]

    text = "\n".join([f"{m.role}: {m.content}" for m in messages])
    labels_str = "\n".join([str(label) for label in _labels])

    base_prompt = f"""以下の会話をカテゴリに分類してください。

カテゴリ:
{labels_str}

会話:
{text}"""

    if llm_client is None:
        llm_client = LLMOpenAIClient(
            temperature=0.2,
            config={"max_tokens": 100},
            system_prompt=f"""あなたは優秀なカテゴライズエージェントです。

制約:
- 必ず次のカテゴリ名のいずれか1つだけを返してください。
- 出力はカテゴリ名と完全一致しなければなりません。

カテゴリ名一覧:
{", ".join(label_names)}

出力形式:
- カテゴリ名のみを1行で返す
""",
        )

    last_err: Exception | None = None
    for i in range(attempt):
        prompt = base_prompt
        if i > 0:
            prompt += (
                "\n\n出力が不正でした。次のいずれかを**完全一致**で1つだけ返してください:\n"
                + "\n".join(label_names)
            )

        try:
            response: LLMResponse = llm_client.request(prompt=prompt)
            response_text = response.get_message().strip()

            if response_text in label_names:
                return response_text

            last_err = ValueError(
                f"Invalid category label: {response_text}.\n"
                f"Expected one of: {label_names}"
            )

        except Exception as e:
            last_err = e

    raise RuntimeError(
        f"categorize failed after {attempt} attempts: {last_err}"
    ) from last_err
