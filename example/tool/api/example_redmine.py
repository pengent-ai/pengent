import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.tools.api.project.redmine import ApiRedmine


def example_get_project():
    api = ApiRedmine()
    res = api.get_projects()
    logger.debug(res)
    # logger.debug( "\n".join( f"{p['id']} {p['name']}" for p in res))


def example_create_project():
    api = ApiRedmine()
    res = api.create_project(
        name="AI研究プロジェクト",
        identifier="ai-research",
        description="AI開発に関する実験と調査",
    )
    logger.debug(res)


def example_get_users():
    api = ApiRedmine()
    res = api.get_users()
    logger.debug(res)


def example_project_member():
    api = ApiRedmine()
    res = api.get_roles()
    logger.debug(res)

    res = api.get_project_members(project_identifier="ai-research")
    logger.debug(res)
    # res = api.create_project_member(
    #     project_identifier="ai-research",
    #     user_id=5,
    #     role_ids=[3],
    # )


def example_issue():
    api = ApiRedmine()
    res = api.get_issues()

    logger.debug(res)
    # for i in res:
    #     api.delete_issue()

    # description="Google ADK(Android Open Accessory Development Kit)について調査を行う"
    # description += "\n使用例・対応端末・制約・デプロイ方法をまとめる。"
    # issue = ApiRedmine.create_issue(
    #     project_identifier="ai-research",  # ← プロジェクト識別子をそのまま指定
    #     subject="Google ADK の調査",
    #     description=description,
    #     assigned_to_id=5,      # 担当者なしでOK(後から追加可能)
    #     tracker_id=2,             # 例: 機能("Feature")に該当
    #     priority_id=2             # 高めの優先度
    # )
    # 27
    api.update_issue(
        issue_id=27,  # 対象チケットID
        notes="""
■ タスクの進め方:
1. Google ADK の概要を公式ページで確認
2. 使用可能なハードウェアを洗い出し
3. 既存のサンプルコードを実行して評価
4. 制約事項・必要ライブラリを整理

■ 成果物:
- 調査メモ(Google Docsに記録済み)
- 動作確認済みのサンプルコード(GitにPush済み)
- 対応可否まとめ(Slackで共有済)

作業完了後に「調査完了」としてステータス更新予定。
""",
    )


def example_wiki():
    api = ApiRedmine()
    api.create_or_update_wiki(
        project_identifier="ai-research",
        title="Google ADK 調査",
        content="""
h1. Google ADK 調査まとめ

h2. 概要

Googleの「Agent Development Kit(ADK)」は、Geminiをはじめとする大規模言語モデル(LLM)を活用して、AIエージェントを簡単かつ柔軟に開発・デプロイするためのモジュール型フレームワークです。

主に以下の目的で設計されています：

* マルチエージェント構成の構築
* LLMによる判断・制御・オーケストレーションの実現
* Vertex AI や Cloud Run との連携による実運用

h2. 主な機能

* *柔軟なオーケストレーション*
  Sequential(直列)、Parallel(並列)、Loop(ループ)などのワークフロー制御が可能。

* *LlmAgentによるルーティング*
  LLMが状況に応じて実行エージェントを選択する高度なルーティング。

* *ツールとの統合*
  検索、計算、コード実行などの組み込みツールや、LangChain・CrewAIなど外部ライブラリも使用可能。

* *マルチエージェント構成*
  個別タスクを処理する専門エージェントを階層的に構成できる。

* *コンテナ化 & デプロイ可能*
  ローカル実行の他、Cloud Run や Vertex AI Agent Engine へのスケーラブルなデプロイに対応。

* *テストと評価機能*
  テストケースを使った自動評価、ステップ実行の追跡など。

h2. 利用例(Python)

以下はADKのPython実装(@google/adk-python)を使った最小構成の例です：

<pre><code class="python">
from adk import Agent, Tool

class HelloTool(Tool):
    def run(self, input):
        return f"こんにちは、{input}さん！"

agent = Agent(
    tools={"hello": HelloTool()},
    prompt="ユーザーに挨拶してください"
)

response = agent.run("ユーザー名")
print(response)
</code></pre>

h2. 関連リンク

* "Agent Development Kit 公式ドキュメント":https://google.github.io/adk-docs/
* "GitHubリポジトリ(adk-python)":https://github.com/google/adk-python
* "Google Cloud Blog: ADK紹介記事":https://developers.googleblog.com/en/agent-development-kit-easy-to-build-multi-agent-applications/

h2. 調査メモ

* Gemini との連携が前提にあるため、Google Cloud アカウントが必須
* オーケストレーション構造がシンプルで、LangChain よりも軽量
* ローカルからコンテナ実行まで対応し、CI/CD統合も視野に入る

h2. 今後の検討

* Pengentフレームワークとの統合可能性
* CrewAI / LangGraph との比較調査
* 実務導入を想定したセキュリティ/スケーラビリティ検証
""",  # noqa: E501
        comments="内容を修正しました。",
    )


def example_file():
    api = ApiRedmine()
    dockerfile_content = """
# ベースイメージとしてPython 3.10を使用
FROM python:3.10-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y git && apt-get clean

# Google ADKをインストール
RUN pip install google-adk

# アプリケーションのコードをコピー
COPY . /app

# 依存関係をインストール(必要に応じてrequirements.txtを使用)
# RUN pip install -r requirements.txt

# アプリケーションを実行
CMD ["python", "main.py"]
""".encode("utf-8")

    res = api.create_project_file_content(
        project_identifier="ai-research",
        file_content=dockerfile_content,
        filename="Dockerfile",
        version_name="ADKエージェント用Dockerfile",
        content_type="text/plain",
    )
    logger.debug(res)


def example_get_issue_statuses():
    api = ApiRedmine()
    statuses = api.get_issue_statuses()
    logger.debug(statuses)
    logger.debug("\n".join(f"{s['id']}: {s['name']}" for s in statuses))


#     # 追加の処理


example_get_issue_statuses()
# example_get_project()
