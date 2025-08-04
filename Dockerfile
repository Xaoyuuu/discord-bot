FROM python:3.11

WORKDIR /app

COPY app/ .
COPY app/requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 3000

CMD ["python", "main.py"]
