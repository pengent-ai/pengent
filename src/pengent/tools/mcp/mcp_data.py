from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelContextProtocolData:
    """
    MCP(Model Context Protocol)サーバーのデータクラス
    """

    name: str
    stream_type: str
    args: Optional[list[str]] = None
    url: Optional[str] = None
    allowed_methods: Optional[list[str]] = None
    headers: Optional[dict[str, str]] = None
    command: Optional[str] = None
    tools: Optional[list[dict]] = None
    status: Optional[str] = "initializing"
    env: Optional[dict[str, str]] = field(
        default=None, repr=False
    )  # 環境変数は表示しない

    def to_dict(self) -> dict:
        data = {
            "name": self.name,
            "stream_type": self.stream_type,
            "status": self.status,
            "tools": self.to_dict_tools(),
        }
        if self.stream_type == "stdio":
            data["command"] = self.command
            data["args"] = self.args
        elif self.stream_type == "streamable-http":
            data["url"] = self.url
            data["allowed_methods"] = self.allowed_methods
            data["headers"] = self.headers
        return data

    def to_dict_tools(self) -> dict[str, str]:
        """
        MCPサーバーのツールの辞書表現を返します。(OpenAI仕様)

        Notes:
            - このメソッドは、ローカル用のツール情報を辞書形式で提供します。
            - LLMクライアントのToolsに設定することでFunctionCallを実行する


        Example::

            [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    }
                }
            ]
        """
        ret = []
        for tool in self.tools or []:
            ret.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description") or "No description.",
                        "parameters": tool["inputSchema"],
                    },
                }
            )
        return ret

    def to_dict_mcp_http_stream(self) -> dict[str, str]:
        """
        Http用のMCPサーバーツールの辞書表現を返します(OpenAI仕様)

        Notes:
            - このメソッドは、HTTPストリーミングMCPサーバー情報を辞書形式で提供します。
            - LLMクライアントに設定することでLLMが自動的にツールを選択して実行する


        Example::

            {
                "type": "mcp",
                "server_url": self.url,
                "allowed_tools": self.allowed_methods,
                "headers": self.headers,
            }
        """
        if not self.stream_type == "streamable-http":
            raise ValueError(
                "Only 'streamable-http' is supported for MCP server tools."
            )

        return {
            "type": "mcp",
            "server_url": self.url,
            "allowed_tools": self.allowed_methods,
            "headers": self.headers,
        }

    @classmethod
    def create_mcp_stdio(
        cls,
        name: str,
        command: str,
        args: list[str],
        env: Optional[dict[str, str]] = None,
    ) -> "ModelContextProtocolData":
        return cls(stream_type="stdio", name=name, command=command, args=args, env=env)

    @classmethod
    def create_mcp_http_stream(
        cls,
        name: str,
        url: str,
        allowed_methods: Optional[list[str]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> "ModelContextProtocolData":
        return cls(
            stream_type="streamable-http",
            name=name,
            url=url,
            allowed_methods=allowed_methods,
            headers=headers,
        )
