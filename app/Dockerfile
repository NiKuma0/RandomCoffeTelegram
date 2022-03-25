FROM python:alpine3.14
WORKDIR /code
COPY requirements.txt /code
RUN pip install -U pip; pip install -r requirements.txt
COPY . .
CMD python main.py
