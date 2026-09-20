FROM httpd:latest
COPY ./files /usr/local/apache2/htdocs/
RUN rm -f /usr/local/apache2/htdocs/index.html.orig
RUN chmod -R 755 /usr/local/apache2/htdocs/
EXPOSE 80
