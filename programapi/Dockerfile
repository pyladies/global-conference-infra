FROM python:3.12

WORKDIR /srv

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY Makefile .

RUN mkdir -p /srv/data/raw/pyladiescon-2024/
RUN mkdir -p /srv/data/public/pyladiescon-2024/


CMD ["make", "all"]
