# Base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
VOLUME [ “/sys/fs/cgroup” ]
RUN npm install
RUN   apk update && \
      apk add --no-cache openssh-keygen && \
      apk add --no-cache openssh && \
      apk add --no-cache openrc 

# Copy source code
COPY server.js .

# Set environment variables
ENV PORT=3000

# Expose port
EXPOSE $PORT


# Start the app
RUN sed -i 's/flagGoesHere/sup3rs3cr3tr3souc3fulflag/g' server.js
RUN sed -i 's/flag2GoesHere/noActualEC2IMDShereS0rry/g' server.js
RUN sed -i 's/flag3GoesHere/fr33b13/g' server.js
RUN sed -i 's/flag5GoesHere/n3v3r_saw_1t_c0m1ng/g' server.js
RUN sed -i 's/flag6GoesHere/f0rg3d_in_f1r3/g' server.js


# Set a lower user and make a home flag
RUN adduser -D appuser
USER appuser
#COPY homeflag.txt /home/appuser/flag.txt


ENTRYPOINT ["sh", "-c", "npm start"]
