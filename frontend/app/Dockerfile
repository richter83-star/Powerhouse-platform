# Frontend Dockerfile for Powerhouse (Next.js 14)

FROM node:20-alpine

# Create app directory
WORKDIR /app

# Install dependencies first (better layer caching)
COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps

# Copy the rest of the app
COPY . .

# Build Next.js for production
RUN npm run build

# Next.js production server listens on 3000
EXPOSE 3000

# Start the app
CMD ["npm", "run", "start"]
