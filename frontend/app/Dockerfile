# Frontend Dockerfile for Powerhouse (Next.js 14)

FROM node:20-alpine

# Create app directory
WORKDIR /app

# Install dependencies first (better layer caching)
# Copy package files (package-lock.json is required for npm ci)
COPY package.json package-lock.json ./
COPY prisma ./prisma
# Use npm ci for reproducible builds (faster and more reliable than npm install)
RUN npm ci --legacy-peer-deps

# Copy the rest of the app
COPY . .

# Build Next.js for production
RUN npm run build

# Next.js production server listens on 3000
EXPOSE 3000

# Start the app using standard Next.js start command
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
CMD ["npm", "run", "start"]
