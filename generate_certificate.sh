#!/usr/bin/env bash

export $(cat .env | xargs)

mkdir -p $CERTBOT_PATH/www 

docker run -it --user "$(id -u):$(id -g)" \
    -v "$CERTBOT_PATH/:/tmp/" \
    -v "$CERTBOT_PATH/letsencrypt/:/etc/letsencrypt/" --rm \
    certbot/certbot certonly --webroot --webroot-path /tmp/www/ -d $SERVER_NAME \
    --config-dir /tmp/certbot/config --logs-dir /tmp/certbot/logs --work-dir /tmp/certbot/work
