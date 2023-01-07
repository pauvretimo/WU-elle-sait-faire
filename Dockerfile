FROM python:3.10.9-alpine3.17

WORKDIR /home/challenge

RUN useradd challenge && \
    chown -R challenge:challenge /home/challenge

USER challenge

RUN python3 -m pip install --no-cache-dir flask waitress

COPY . .

EXPOSE 80

CMD [ "python3", "./app.py" ]
