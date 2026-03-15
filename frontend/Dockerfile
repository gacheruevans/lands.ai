FROM node:22-bookworm-slim AS base

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .


FROM base AS test

CMD ["npm", "test"]


FROM base AS runtime

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0", "-p", "3000"]
