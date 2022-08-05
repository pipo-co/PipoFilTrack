#!/usr/bin/env bash
envsubst '$APP_ADDR' < /tmp/default.conf > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'
