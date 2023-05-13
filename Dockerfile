FROM python:3.6.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

ENTRYPOINT ["python", "chgkgameBot.py"]