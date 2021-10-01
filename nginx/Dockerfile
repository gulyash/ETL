FROM nginx:1.19.2

COPY nginx.conf /etc/nginx/nginx.conf
COPY site.conf /etc/nginx/conf.d/site.conf

RUN rm /etc/nginx/conf.d/default.conf
