FROM python:3.10-alpine

WORKDIR /

COPY requirements.txt /

RUN pip install -r requirements.txt

COPY . /

CMD ["python", "main.py"]