FROM node:14-alpine

# Copy the JavaScript files to the container
COPY app.js package.json /app/

# Copy the SQLite database file to the container
COPY users.db /app/

# Copy views
COPY views/ /app/views

# Copy the public sections to the container
COPY public/ /app/public

# Copy logs
COPY logs/ /app/logs
RUN chmod 707 /app/logs/access.log

# Copy orders
COPY orders/ /app/orders

# Set the working directory to the app directory
WORKDIR /app

# Install the required dependencies
RUN npm install

# Expose the port that the web application listens on
EXPOSE 3000

RUN echo "LOCAL USERS: appuser" > /app/logs/users.log

# Set a lower user and make a home flag
RUN adduser -D appuser
USER appuser
COPY homeflag.txt /home/appuser/flag.txt


# Start the web application when the container starts
CMD ["npm", "start"]