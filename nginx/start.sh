#!/usr/bin/env bash
envsubst '$APP_ADDR $SERVER_NAME' < /tmp/default.conf > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'
