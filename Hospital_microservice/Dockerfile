FROM python:3.12-slim
WORKDIR /Volga-IT

COPY ./requirements.txt /Volga-IT/requirements.txt

RUN pip install -r /Volga-IT/requirements.txt \
    && rm -rf /root/.cache/pip

COPY . /Volga-IT/