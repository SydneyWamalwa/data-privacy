FROM node:20-alpine

WORKDIR /app

# First copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Then copy source files
COPY . .

EXPOSE 3000

# Set OpenSSL legacy mode for Webpack compatibility
ENV NODE_OPTIONS="--openssl-legacy-provider"

CMD ["npm", "start"]
