# Frontend Dockerfile for Powerhouse (Next.js 14)

FROM node:20-alpine

# Create app directory
WORKDIR /app

# Install dependencies first (better layer caching)
# Copy Prisma schema early so `npm install` (which runs `prisma generate` via postinstall) can find it.
COPY package.json package-lock.json* ./
COPY prisma ./prisma
RUN npm install --legacy-peer-deps

# Copy the rest of the app
COPY . .

# Build Next.js for production
RUN npm run build

# Next.js production server listens on 3000
EXPOSE 3000

# Start the app
# Next.js standalone mode - copy required files and run server
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
CMD ["sh", "-c", "if [ -d .next/standalone ]; then cp -r .next/static .next/standalone/.next/ 2>/dev/null || true; cp -r public .next/standalone/ 2>/dev/null || true; cd .next/standalone && node server.js; else npm run start; fi"]
