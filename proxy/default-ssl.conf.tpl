server {
    listen ${LISTEN_PORT} ssl;
    server_name ${DOMAIN};

    ssl_certificate     ${SSL_CERT_PATH};
    ssl_certificate_key ${SSL_KEY_PATH};
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_session_cache   shared:SSL:10m;

    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;
    send_timeout       600s;
    fastcgi_send_timeout 600s;
    fastcgi_read_timeout 600s;

    location /static {
        alias /vol/static;

        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout       600s;
        fastcgi_send_timeout 600s;
        fastcgi_read_timeout 600s;
    }

    location / {
        uwsgi_read_timeout 600s;
        uwsgi_send_timeout 600s;
        uwsgi_pass              ${APP_HOST}:${APP_PORT};
        include                 /etc/nginx/uwsgi_params;
        uwsgi_param HTTP_X_FORWARDED_PROTO $scheme;
        uwsgi_param HTTP_X_FORWARDED_HOST $host;
        client_max_body_size    30M;

        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout       600s;
        fastcgi_send_timeout 600s;
        fastcgi_read_timeout 600s;
    }
}