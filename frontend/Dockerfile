# Multi-stage build for React frontend
FROM node:18 AS builder

# Set working directory
WORKDIR /app

# Copy package.json only (not package-lock.json to avoid rollup issues)
COPY package.json ./

# Install all dependencies with fresh lock file
RUN npm install

# Copy source code
COPY . .

# Set production environment and backend URL
ENV VITE_ENVIRONMENT=production
ENV VITE_PROD_BACKEND_URL=https://nestle-ai-chatbot-backend.whitewater-4228c4bc.canadaeast.azurecontainerapps.io

# Build the application
RUN npm run build

# Production stage with lightweight Node server
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install serve package globally and curl for health checks
RUN npm install -g serve && \
    apk add --no-cache curl

# Copy built files from builder stage
COPY --from=builder /app/dist ./dist

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 -G nodejs && \
    chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Start the server
CMD ["serve", "-s", "dist", "-l", "3000"] 