# Deploy / hosted demo

## Local demo (Docker)

```bash
docker compose --profile demo up --build
# http://localhost:8000/docs
```

## Production profile

```bash
export QUANTAURA_API_KEYS="replace-me"
export QUANTAURA_RATE_LIMIT_PER_MIN=120
docker compose --profile prod up --build -d
```

## Fly.io

```bash
fly launch --name quantaura-demo --region iad
fly secrets set QUANTAURA_API_KEYS=... QUANTAURA_ENV=production
fly deploy
```

## Policy packs

```bash
export QUANTAURA_POLICY_PACK=configs/policy_packs/enterprise.yaml
quantaura-serve
```

## API keys

When `QUANTAURA_API_KEYS` is set, send header `X-API-Key`. Public without key: `/`, `/health`, `/docs`.
