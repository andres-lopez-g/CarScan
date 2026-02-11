FROM node:18-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Run in development mode (skip build for hot-reload with volumes)
CMD ["npm", "run", "dev"]
