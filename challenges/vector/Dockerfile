# Use the official Apache image from Docker Hub
FROM httpd:latest

# Copy your files into the container
COPY ./files /usr/local/apache2/htdocs/

# Remove default index.html file if it exists (ignore errors)
RUN rm -f /usr/local/apache2/htdocs/index.html.orig

# Change permissions to make all files readable by the web server
RUN chmod -R 755 /usr/local/apache2/htdocs/

# Expose port 80 to make the web server accessible
EXPOSE 80