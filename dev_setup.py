"""Development environment setup and utilities."""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_dev_environment():
    """Set up development environment."""
    repo_root = Path(__file__).parent
    
    logger.info("Setting up QUANTAURA-Core v0.4 development environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ required")
        sys.exit(1)
    
    logger.info(f"Python version: {sys.version}")
    
    # Install dependencies
    logger.info("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(repo_root)])
    
    # Install dev dependencies
    logger.info("Installing development dependencies...")
    dev_deps = [
        "pytest>=7.0",
        "pytest-asyncio>=0.20.0",
        "pytest-cov>=4.0",
        "black>=22.0",
        "flake8>=4.0",
        "mypy>=0.990",
        "isort>=5.10",
    ]
    
    for dep in dev_deps:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        except subprocess.CalledProcessError:
            logger.warning(f"Failed to install {dep}")
    
    # Create necessary directories
    logger.info("Creating directories...")
    dirs = [
        repo_root / "logs",
        repo_root / "data",
        repo_root / "results",
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(exist_ok=True)
        logger.info(f"  Created {dir_path}")
    
    logger.info("\n" + "="*60)
    logger.info("Development environment setup complete!")
    logger.info("="*60)
    logger.info("\nNext steps:")
    logger.info("  1. Read the documentation: docs/GETTING_STARTED.md")
    logger.info("  2. Run the examples: python examples/fractal_experiment.py")
    logger.info("  3. Run tests: pytest tests/ -v")
    logger.info("  4. Check code quality: flake8 quantaura/")
    logger.info("\n")


if __name__ == "__main__":
    setup_dev_environment()
