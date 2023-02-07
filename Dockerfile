FROM python:3.11-slim-buster

WORKDIR /app
COPY requirements.txt .

RUN pip install -r requirements.txt && rm requirements.txt

COPY . .

WORKDIR /app/src
CMD ["python", "app.py"]