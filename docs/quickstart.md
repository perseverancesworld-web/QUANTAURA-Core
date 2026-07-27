# Quickstart

## Local development

```bash
git clone https://github.com/perseverancesworld-web/QUANTAURA-Core.git
cd QUANTAURA-Core
pip install -e ".[dev]"
quantaura-serve --reload
```

Open http://localhost:8000 and http://localhost:8000/docs

## Tests

```bash
pytest -v
```

## Docs

```bash
mkdocs serve
```

## Docker

```bash
docker compose --profile dev up
docker compose --profile prod up
```
