---
tags: [Dockerfile, multi-stage, container, image, non-root, Java, Next.js, alpine, frozen-lockfile]
executor: infra
---

# Dockerfile Patterns

## Java Spring Boot

```dockerfile
# Stage 1: build — full JDK
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /app
COPY mvnw pom.xml ./
COPY .mvn .mvn
RUN ./mvnw dependency:go-offline -q   # cache deps before copying source
COPY src ./src
RUN ./mvnw package -DskipTests -q

# Stage 2: runtime — minimal JRE only
FROM eclipse-temurin:21-jre-alpine AS runtime
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
USER appuser                          # never run as root
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

## Next.js

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

FROM node:20-alpine AS runtime
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
USER appuser
EXPOSE 3000
CMD ["node", "server.js"]
```

## Rules

- Always multi-stage — final image contains only runtime artefacts, no build tools
- Non-root user in final stage — never run containers as root
- Pin base image tags — never `node:latest` or `eclipse-temurin:latest`
- `--frozen-lockfile` for package installs — reproducible builds
