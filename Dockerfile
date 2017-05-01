FROM python:3.6.1
RUN apt-get update && apt-get install -y libsdl2-2.0 && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
ADD requirements.txt /usr/src/app/requirements.txt
RUN pip install -U websocket-client

ADD base/ /usr/src/app/base/
ADD *.py /usr/src/app/

CMD ["python", "bot_path_collect.py", "--no-ui", "-name", "$BOT_NAME", "-g", "$BOT_MODE"]
