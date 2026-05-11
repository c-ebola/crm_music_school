# nginx на Alpine
FROM nginx:alpine

# вставлякм свой конфиг
RUN rm /etc/nginx/conf.d/default.conf
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Копируем статические файлы фронта в папку, откуда nginx их раздаёт
COPY frontend/ /usr/share/nginx/html/

# nginx 80 порт
EXPOSE 80
