# Contributing to QUANTAURA-Core

Thank you for your interest in contributing!

## Development setup

```bash
git clone https://github.com/perseverancesworld-web/QUANTAURA-Core.git
cd QUANTAURA-Core
pip install -e ".[dev]"
```

## Workflow

1. Create a feature branch from `main`
2. Implement your change with tests
3. Run the full suite:

```bash
black .
ruff check .   # optional
pytest -v
```

4. Open a pull request with a clear description

## Code of conduct

Be respectful, constructive, and focused on the science.
