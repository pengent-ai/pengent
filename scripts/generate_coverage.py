import re


class GenerateCoverage:
    """カバレッジ結果を解析して Markdown テーブルを生成"""

    def __init__(
        self,
        coverage_file="pytest-coverage.txt",
        output_file="coverage_table.md",
    ):
        """
        初期化

        :param coverage_file: カバレッジ結果のテキストファイル
        :param output_file: 出力する Markdown ファイル
        """
        self.coverage_file = coverage_file
        self.output_file = output_file
        self.coverage_data = []
        self.markdown_table = None

    def parse_coverage(self):
        """
        coverage.txt のデータを解析してカバレッジ情報を抽出
        """
        with open(self.coverage_file, "r") as f:
            lines = f.readlines()

        coverage_info = []
        in_coverage_section = False

        for line in lines:
            # Coverage セクションの始まりを検出
            if "Name" in line and "Stmts" in line and "Miss" in line:
                in_coverage_section = True
                continue
            # セパレーター行をスキップ
            if in_coverage_section and line.strip().startswith("---"):
                continue
            # Coverage セクションの終わりを検出(TOTAL行の次の空行)
            if in_coverage_section and (
                line.strip().startswith("TOTAL")
                or line.strip().startswith("=")
            ):
                break
            # Coverage データを抽出
            if in_coverage_section:
                match = re.match(
                    r"(.+?)\s+(\d+)\s+(\d+)\s+(\d+%)\s*(.*)", line
                )
                if match:
                    filename = match.group(1).strip()
                    statements = match.group(2).strip()
                    missed = match.group(3).strip()
                    coverage = match.group(4).strip()
                    missing_lines = (
                        match.group(5).strip() if match.group(5) else "-"
                    )
                    coverage_info.append(
                        {
                            "filename": filename,
                            "statements": statements,
                            "missed": missed,
                            "coverage": coverage,
                            "missing_lines": missing_lines,
                        }
                    )

        self.coverage_data = coverage_info

    def generate_table(self):
        """
        Markdown テーブルを生成
        """
        if not self.coverage_data:
            self.parse_coverage()
            print("Parsed coverage data.")

        # Markdown テーブルヘッダー
        table_header = (
            "| File | Statements | Missed | Coverage | Missing Lines |\n"
        )
        table_header += (
            "|------|------------|--------|----------|---------------|\n"
        )

        # テーブル行を生成
        table_rows = [
            (
                f"| {data['filename']} | {data['statements']} | "
                f"{data['missed']} | {data['coverage']} | "
                f"{data['missing_lines']} |"
            )
            for data in self.coverage_data
        ]

        self.markdown_table = table_header + "\n".join(table_rows)

    def print_table(self):
        """
        テーブルをコンソールに出力
        """
        if self.markdown_table is None:
            self.generate_table()
        print(self.markdown_table)

    def save_table(self):
        """
        テーブルをファイルに保存
        """
        if self.markdown_table is None:
            self.generate_table()

        with open(self.output_file, "w", encoding="utf-8") as f:
            print(f"Markdown table has been saved to {self.output_file}")
            f.write(self.markdown_table)


if __name__ == "__main__":
    generator = GenerateCoverage()
    generator.generate_table()
    generator.save_table()
