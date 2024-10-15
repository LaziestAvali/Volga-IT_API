FROM python:3.12-slim
WORKDIR /Volga-IT

COPY ./requirements.txt /Volga-IT/requirements.txt

RUN apt-get update \
    && apt-get install gcc -y \
    && apt-get clean

RUN pip install -r /Volga-IT/requirements.txt \
    && rm -rf /root/.cache/pip

COPY . /Volga-IT/