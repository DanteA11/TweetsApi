FROM python:3.12

RUN apt-get update && apt-get install -y python3-dev supervisor nginx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt
COPY . /app/
RUN mkdir -p /app/static/medias
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.ini /etc/supervisor/conf.d/supervisord.ini

WORKDIR /app

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.ini"]
