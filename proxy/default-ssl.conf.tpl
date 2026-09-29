server {
    listen ${LISTEN_PORT} ssl;
    http2 on;
    server_name ${DOMAIN};

    ssl_certificate     ${SSL_CERT_PATH};
    ssl_certificate_key ${SSL_KEY_PATH};
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_session_cache   shared:SSL:10m;

    # --- Compresion: antes nunca se enviaba content-encoding ---
    gzip            on;
    gzip_vary       on;
    gzip_proxied    any;
    gzip_comp_level 5;
    gzip_min_length 256;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/json
        application/xml
        application/rss+xml
        image/svg+xml;

    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;
    send_timeout       600s;
    fastcgi_send_timeout 600s;
    fastcgi_read_timeout 600s;

    # --- Media (/static/media/): contenido reemplazable, sin immutable ---
    location /static/media/ {
        alias /vol/static/media/;

        # Solo Cache-Control (moderno). No usar 'expires' aqui: ya emitiria un
        # segundo header Cache-Control y duplicaria la directiva.
        add_header Cache-Control "public, max-age=604800" always;

        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout       600s;
        fastcgi_send_timeout 600s;
        fastcgi_read_timeout 600s;
    }

    # --- Assets estaticos: cache largo ---
    location /static {
        alias /vol/static;

        # Solo Cache-Control (moderno). 'expires' emitiria un segundo header
        # Cache-Control; ademas 'immutable' exige que la URL cambie por version,
        # y aqui los assets NO estan fingerprinted (STATIC_URL sin hash).
        add_header Cache-Control "public, max-age=2592000" always;

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
