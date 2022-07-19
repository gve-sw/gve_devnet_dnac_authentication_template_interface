FROM python:3.8-slim-buster

RUN apt-get update && apt-get -y install procps libnss-wrapper

ADD requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

ADD . .

EXPOSE 8756

CMD ["python","app.py"]