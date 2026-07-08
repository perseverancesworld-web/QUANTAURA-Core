# Contributing to QUANTAURA-Core

Welcome! This document explains how to contribute to QUANTAURA-Core, from bug fixes to new plugins and research features.

---

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and adhere to our Code of Conduct (see `CODE_OF_CONDUCT.md`).

**TL;DR:** Be respectful, inclusive, and assume good intent.

---

## Getting Started

### 1. Set Up Your Dev Environment

```bash
# Clone the repo
git clone https://github.com/perseverancesworld-web/QUANTAURA-Core.git
cd QUANTAURA-Core

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov=quantaura

# Start the dev server
uvicorn api.main:app --reload
```

### 2. Understand the Project Structure

```
QUANTAURA-Core/
├── quantaura/              # Core library
│   ├── api/                # FastAPI application
│   ├── core/               # Plugins, experiments, simulations
│   ├── models/             # Cognitive architectures, math models
│   ├── observability/      # Logging, metrics, tracing
│   └── security/           # RBAC, auth, audit
├── plugins/                # Reference plugins (ACT-R, agents, etc.)
├── examples/               # Usage examples
├── tests/                  # Test suite
├── docs/                   # Architecture, guides
├── docker-compose.yml      # Production stack
└── setup.py                # Package metadata
```

---

## How to Contribute

### 🐛 Report a Bug

1. Check existing issues to avoid duplicates
2. Open a new GitHub Issue with:
   - **Title:** Clear, specific summary
   - **Description:** What you expected vs. what happened
   - **Reproduction:** Minimal code example
   - **Environment:** Python version, OS, relevant dependencies
3. Add labels: `bug`, `priority:high/medium/low`

### 💡 Suggest a Feature

1. Open a GitHub Discussion (not an Issue) with tag `#feature-request`
2. Describe:
   - What problem does it solve?
   - Why would others benefit?
   - Any implementation ideas (optional)
3. Community votes; core team evaluates for roadmap

### ✨ Contribute Code

#### Small Fixes (typos, docs, minor bugs)

1. Fork the repo
2. Create a branch: `git checkout -b fix/issue-description`
3. Make changes, add tests
4. Commit with semantic message: `fix: correct typo in README`
5. Push and open a PR

#### Medium Features (new CLI command, dashboard component)

1. Create an issue first (discuss before coding)
2. Link to the issue in your PR
3. Fork, branch, implement, test
4. Ensure 80%+ test coverage for new code
5. Update docs/examples

#### Large Features (new plugin system, workspace collaboration)

1. **Open a GitHub Discussion** — describe the scope, design, timeline
2. **Wait for feedback** — core team will guide design decisions
3. **Claim the issue** — tag with `accepted` once approved
4. **Implement in phases** — break into PRs (~500 LOC each)
5. **Request design review** — before final merge

### 🔌 Write a Plugin

Plugins are the heart of QUANTAURA. See `docs/plugin-development.md` for the full guide.

**Quick Start:**

```python
# plugins/my_experiment/plugin.py
from quantaura.core import ExperimentPlugin

class MyExperiment(ExperimentPlugin):
    """My custom experiment."""
    
    metadata = {
        "name": "my_experiment",
        "version": "0.1.0",
        "author": "Your Name",
        "description": "Does something amazing"
    }
    
    def validate(self, config: dict) -> bool:
        """Check if config is valid."""
        return "param1" in config
    
    def execute(self, config: dict) -> dict:
        """Run the experiment."""
        result = config["param1"] * 2
        return {"output": result}
    
    def visualize(self, result: dict) -> str:
        """Return HTML for visualization."""
        return f"<p>Result: {result['output']}</p>"
```

Then register in `quantaura/core/plugin_registry.py`:

```python
from plugins.my_experiment.plugin import MyExperiment

REGISTRY["my_experiment"] = MyExperiment()
```

**Next Steps:**
- Add tests: `tests/plugins/test_my_experiment.py`
- Add example: `examples/my_experiment_demo.py`
- Submit PR with plugin + tests + docs

---

## Code Standards

### Style Guide

- **Python:** PEP 8 (use `black` for formatting, `flake8` for linting)
- **Type Hints:** All public functions must have type annotations
- **Docstrings:** Google-style, include examples for complex functions

```python
# Good
def calculate_sharpe_ratio(returns: list[float], risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sharpe ratio from return series.
    
    Args:
        returns: List of periodic returns (e.g., daily).
        risk_free_rate: Annual risk-free rate (default 0%).
    
    Returns:
        Sharpe ratio (annualized).
    
    Example:
        >>> returns = [0.01, 0.02, -0.01, 0.03]
        >>> calculate_sharpe_ratio(returns)
        1.234
    """
    ...
```

### Testing Requirements

- **Minimum coverage:** 80% for new code
- **Test frameworks:** pytest, hypothesis (for property-based tests)
- **Naming:** `test_<function>_<scenario>.py`

```bash
# Run tests with coverage
pytest tests/ --cov=quantaura --cov-report=html

# Run specific test
pytest tests/test_api.py::test_create_workspace -v
```

### Security Checklist

- [ ] No hardcoded secrets (use environment variables)
- [ ] Input validation on all API endpoints
- [ ] SQL injection protection (use parameterized queries)
- [ ] CORS configured correctly
- [ ] Rate limiting enabled

---

## Pull Request Process

1. **Branch naming:** `feature/`, `fix/`, `docs/`, `refactor/`, `test/`
2. **Keep it focused:** One feature/fix per PR
3. **Commit messages:** Use semantic commits
   ```
   feat: add collaborative workspaces
   fix: handle NaN in Sharpe ratio calculation
   docs: update plugin development guide
   test: add tests for experiment versioning
   ```
4. **PR description:**
   - What does it do?
   - Why is it needed?
   - How to test?
   - Closes #123
5. **Tests:** All tests pass, coverage maintained
6. **Docs:** Update README/docs if needed
7. **Review:** Address reviewer feedback promptly

---

## Semantic Versioning

QUANTAURA follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0 → 2.0.0): Breaking API changes
- **MINOR** (1.0.0 → 1.1.0): New features (backward compatible)
- **PATCH** (1.0.0 → 1.0.1): Bug fixes

### Release Checklist (for maintainers)

- [ ] All PRs merged for this version
- [ ] Tests pass (100% CI green)
- [ ] Docs updated
- [ ] Changelog updated (`CHANGELOG.md`)
- [ ] Version bumped in `setup.py` and `__init__.py`
- [ ] Tag created: `git tag -a v1.1.0 -m "v1.1.0 release"`
- [ ] GitHub release notes published
- [ ] PyPI package published: `python setup.py sdist bdist_wheel && twine upload dist/*`

---

## Documentation

Documentation is **as important as code**. When contributing:

1. **Add docstrings** to all functions/classes
2. **Update `docs/`** if architecture changes
3. **Add examples** to `examples/` for new features
4. **Update README** if it affects users
5. **Add migration guide** for breaking changes

---

## Communication

- **Discussions:** Feature ideas, design decisions
- **Issues:** Bugs, feature requests (with code)
- **Slack/Discord:** (Link in README) — real-time chat
- **Mailing list:** quantaura-dev@example.com (announcements)

---

## Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` (all contributors listed)
- GitHub "Contributors" page
- Release notes (acknowledgment section)
- Monthly "Contributor Spotlight" blog post

---

## Questions?

- Check `docs/faq.md`
- Open a GitHub Discussion
- Email: maintainers@quantaura.dev
- Office hours: Thursdays 2pm UTC (link in README)

**Happy coding!** 🚀
