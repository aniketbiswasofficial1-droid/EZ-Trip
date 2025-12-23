# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json yarn.lock* ./
RUN yarn install

# Copy source code
COPY . .

# Expose the standard React port
EXPOSE 3000

# Start the development server
CMD ["yarn", "start"]