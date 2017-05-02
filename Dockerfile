FROM python:3.6.1

WORKDIR /usr/src/app
ADD requirements.txt /usr/src/app/requirements.txt
RUN pip install -U websocket-client

ADD base/ /usr/src/app/base/
ADD *.py /usr/src/app/

CMD ["python", "bot_blob.py", "--no-ui"]
