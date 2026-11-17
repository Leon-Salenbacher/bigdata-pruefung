
# Stage 1: Build React application
FROM node:24-alpine AS build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy application source
COPY . .

# Build production application
RUN npm run build


# Stage 2: Serve with Nginx
FROM nginx:stable-alpine

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built React application
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
