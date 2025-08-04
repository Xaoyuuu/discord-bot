# Node.jsのバージョン、変える事。
FROM python:3.11

# 作業ディレクトリを /app に
WORKDIR /app

# app フォルダ内の内容をコンテナの /app にコピー
COPY app/ .

# 依存関係のインストール
RUN pip install -r requirements.txt

# ポートを開ける（Koyeb用）、使用してるポート番号にすること。
EXPOSE 3000

# アプリの起動、コマンドを指定しよう。index.jsなら"node", "index.js"
CMD ["python", "main.py"]
