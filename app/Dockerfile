###########
# BUILDER #
###########

FROM python:alpine3.14 as builder

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev

RUN pip install -U pip
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt
COPY . .



#########
# FINAL #
#########

FROM python:alpine3.14

# create user
RUN mkdir -p /home/app
RUN addgroup -S app && adduser -S app -G app
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# install dependencies
RUN apk update && apk add libpq
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --no-cache /wheels/*

# COPY ./entrypoint.prod.sh $APP_HOME
COPY . $APP_HOME

RUN chown -R app:app $APP_HOME
USER app
# ENTRYPOINT ["/home/app/web/entrypoint.prod.sh"]

CMD python main.py


# FROM python:alpine3.14
# WORKDIR /code
# COPY requirements.txt /code
# RUN pip install -U pip; pip install -r requirements.txt
# COPY . .
# CMD python main.py
