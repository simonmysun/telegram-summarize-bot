FROM python:alpine3.20

WORKDIR /app/

ADD . /app/

RUN pip install -q -r requirements.txt

CMD ["python", "bot.py"]