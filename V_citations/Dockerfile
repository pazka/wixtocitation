FROM python:3.14-alpine

WORKDIR /

COPY requirements.txt /

RUN pip install -r requirements.txt

COPY . /

CMD ["python","-u", "main.py"]