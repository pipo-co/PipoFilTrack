#!/usr/bin/env bash
envsubst '$APP_ADDR $SERVER_NAME' < /tmp/$CONF_TEMPLATE > /etc/nginx/conf.d/$CONF_TEMPLATE && nginx -g 'daemon off;'
