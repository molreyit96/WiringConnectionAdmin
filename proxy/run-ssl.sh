#!/bin/sh

set -e

# nginx corre como usuario no-root: el placeholder va a /tmp (escribible),
# el certificado real (certbot) se lee desde /etc/letsencrypt (solo lectura).
CERT_DIR=/etc/letsencrypt/live/wcapp
if [ -f "$CERT_DIR/fullchain.pem" ]; then
    SSL_CERT_PATH=$CERT_DIR/fullchain.pem
    SSL_KEY_PATH=$CERT_DIR/privkey.pem
else
    PLACEHOLDER=/tmp/wcapp-certs
    mkdir -p "$PLACEHOLDER"
    openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
        -keyout "$PLACEHOLDER/privkey.pem" \
        -out "$PLACEHOLDER/fullchain.pem" \
        -subj "/CN=${DOMAIN}" >/dev/null 2>&1
    SSL_CERT_PATH=$PLACEHOLDER/fullchain.pem
    SSL_KEY_PATH=$PLACEHOLDER/privkey.pem
fi

export SSL_CERT_PATH SSL_KEY_PATH LISTEN_PORT DOMAIN APP_HOST APP_PORT
envsubst '${SSL_CERT_PATH} ${SSL_KEY_PATH} ${LISTEN_PORT} ${DOMAIN} ${APP_HOST} ${APP_PORT}' \
    < /etc/nginx/default-ssl.conf.tpl > /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'