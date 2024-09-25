FROM python:3.12.6-slim-bullseye
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN apt update && apt install -y python3-sphinx
