FROM node:22-alpine AS builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
COPY frontend/apps ./apps
COPY frontend/packages ./packages
COPY frontend/postcss.config.cjs ./postcss.config.cjs
COPY frontend/tailwind.config.cjs ./tailwind.config.cjs
COPY frontend/tsconfig.base.json ./tsconfig.base.json

RUN npm ci
RUN npm run build

FROM nginx:1.27-alpine AS runtime

COPY frontend/docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/apps/user-web/dist/ /usr/share/nginx/html/
COPY --from=builder /app/apps/admin-web/dist/ /usr/share/nginx/html/admin/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
