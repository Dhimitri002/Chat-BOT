# =============================================
# WHATSAPP CONNECTOR - Dockerfile
# =============================================

# Base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Expose port (if the connector runs a server)
# Adjust if necessary
EXPOSE 3001

# Run the application
CMD ["node", "src/index.js"]