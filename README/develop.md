# Develop

## Documentation(ドキュメンテーション)

Rstファイルを生成する

```sh
sphinx-apidoc -o docs/source src/pengent
```


```sh
make clean html 
make html 
```


```bat
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"
```

```powershell
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```

## DNS ngrok(開発時のポート開放)

```sh
ngrok http 8080
```
