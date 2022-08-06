#!/usr/bin/env bash
envsubst '$APP_ADDR SERVER_NAME' < /tmp/app.conf > /etc/nginx/conf.d/app.conf && nginx -g 'daemon off;'
