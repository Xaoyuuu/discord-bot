FROM python:3.11

# 作業ディレクトリを /app に
WORKDIR /app

# アプリと依存ファイルのコピー
COPY app/ .
COPY app/requirements.txt .

# pipアップグレード（任意）
RUN pip install --upgrade pip

# 依存関係のインストール
RUN pip install -r requirements.txt

# ポート指定（Flaskとかなら3000でOK）
EXPOSE 3000

# アプリ起動（Flaskなら app.py / main.py）
CMD ["python", "main.py"]
