# リリース手順

## リポジトリ構成

| リモート | URL                                               | 用途                 |
| -------- | ------------------------------------------------- | -------------------- |
| `origin` | https://gitea.pglikers.com/ai-program/pengent.git | メイン開発リポジトリ |
| `github` | https://github.com/pengent-ai/pengent.git         | 公開配布用ミラー     |

### ブランチ運用

```
main          ← リリース済みの安定版
develop       ← 開発中の変更を集約するブランチ
release/x.y.z ← リリース準備ブランチ
distribution  ← GitHub 公開用スナップショット（origin とは無関係な独立ブランチ）
```

---

## リリース手順

### 1. CHANGELOG を更新する

[CHANGELOG](../CHANGELOG) に新バージョンのセクションを追加する。

```
## [x.y.z] - YYYY-MM-DD

### Added
- 追加した機能

### Changed
- 変更した内容

### Breaking Changes
- 互換性のない変更
```

### 2. バージョン番号を更新する

[pyproject.toml](../pyproject.toml) の `version` を新しいバージョンに書き換える。

```toml
[project]
version = "x.y.z"
```

### 3. テストを実行して確認する

```bash
# ユニットテスト（必ず全件パスさせる）
python -m pytest tests/ -q
```

> 統合テスト (`test_integreations/`) は外部 API に依存するため、
> API クォータ切れなどで失敗する場合は無視してよい。

### 4. release ブランチを作成して Gitea にプッシュする

```bash
git checkout -b release/x.y.z
git push origin release/x.y.z
```

プッシュ後、Gitea の Web UI から `release/x.y.z` → `main` への PR を作成してマージする。

---

## PyPI へのアップロード

### 0. 事前準備（初回のみ）

`build` と `twine` が未インストールだと `python -m build` が失敗するため、先にインストールしておく。

実行する Python が `pyenv` 側を向いてしまうことがあるため、以降は `.venv` の Python を明示して実行する。

```bash
VENV_PY=.venv/bin/python
$VENV_PY -m pip install -U build twine
```

### 5. パッケージをビルドする

```bash
# 古いビルドを削除してからビルド
rm dist/*
$VENV_PY -m build
```

`dist/` に以下の2ファイルが生成される。

```
pengent-x.y.z-py3-none-any.whl
pengent-x.y.z.tar.gz
```

### 6. twine でアップロードする

事前に `~/.pypirc` に API トークンを設定しておく。

```bash
ls -l ~/.pypirc
```

```ini
[distutils]
index-servers = pypi

[pypi]
username = __token__
password = pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

```bash
$VENV_PY -m twine check dist/*
$VENV_PY -m twine upload dist/*
```

アップロード後は https://pypi.org/project/pengent/ で公開を確認する。

---

## GitHub（公開ミラー）への反映

GitHub の `distribution` ブランチは Gitea `main` とは無関係な独立ブランチで、
公開スナップショットとして管理している。

### 7. distribution ブランチを更新してプッシュする

```bash
# distribution ブランチに切り替える
git checkout distribution

# release ブランチの変更を distribution に取り込む
git checkout release/x.y.z -- <変更されたファイル一覧>
# distribution ブランチ上で実行
# git checkout release/x.y.z -- $(git diff --name-only --diff-filter=AMR distribution..release/x.y.z)
# git diff --name-only --diff-filter=D distribution..release/x.y.z | xargs -I{} git rm -f "{}"

# スナップショットコミットを作成する
git commit -m "Snapshot Vx.y.z"

# GitHub にプッシュする
git push github distribution

# 作業ブランチに戻る
git checkout release/x.y.z
```

変更ファイルの一覧は以下で確認できる。

```bash
git diff distribution..release/x.y.z --name-only
```

---

## リリース後の確認チェックリスト

- [ ] `python -m pytest tests/ -q` が全件パス
- [ ] CHANGELOG にバージョンと日付が記載されている
- [ ] `pyproject.toml` のバージョンが正しい
- [ ] Gitea の `release/x.y.z` → `main` PR がマージされている
- [ ] PyPI で新バージョンが公開されている (`pip install pengent==x.y.z` で確認)
- [ ] GitHub `distribution` ブランチが "Snapshot Vx.y.z" コミットで更新されている
