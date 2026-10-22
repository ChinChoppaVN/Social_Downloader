FROM nginx:alpine
LABEL maintainer="ChinChoppa"

# Copy static assets to nginx html directory
COPY . /usr/share/nginx/html

# Expose port 80 inside container
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
