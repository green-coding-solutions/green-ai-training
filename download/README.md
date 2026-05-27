## Running these scenarios

The scenarios expects downloadable files to be available at http://192.168.178.21:6000/*.bin

This URL is natively available if you run the scenario in the [GMT Cluster](https://metrics.green-coding.io/cluster-status.html).

If you run these scenarios locally be sure to set up a local NGINX server that serves a static file from
that route which has the appropriate size.

## Sample local file server

`compose.yml`
```compose
services:
  nginx:
    image: nginx:alpine
    container_name: registry-nginx
    restart: always
    ports:
      - "6000:6000"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./1MB.bin:/var/www/static/1MB.bin
      - ./10MB.bin:/var/www/static/10MB.bin
      - ./100MB.bin:/var/www/static/100MB.bin
      - ./1GB.bin:/var/www/static/1GB.bin
```

nginx.conf
```nginx
worker_processes 1;

events { worker_connections 1024; }

http {

    log_format docker '$remote_addr - $remote_user [$time_local] '
                      '"$request" $status $body_bytes_sent '
                      '"$http_referer" "$http_user_agent" $body_bytes_sent $request_time';

    access_log /var/log/nginx/access.log docker;

    server {
        listen 6000;

	gzip off;


        root /var/www/static;

        location / {
             # serve files directly, no proxying
             try_files $uri $uri/ =404;
         }

         # optional: disable directory listing
         autoindex off;
    }
}
```
