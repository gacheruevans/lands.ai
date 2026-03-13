# lands.ai frontend

Next.js + Tailwind scaffold for lands.ai.

## Run (development)

1. Install Node.js dependencies.
2. Copy `.env.example` to `.env.local`.
3. Start development server.

The UI calls backend at `NEXT_PUBLIC_API_BASE_URL`.

## Docker

When run via root `docker-compose.yml`, frontend is available at `http://localhost:3000` and calls backend at `http://localhost:8000/api/v1`.
