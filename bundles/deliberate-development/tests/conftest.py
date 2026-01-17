"""Pytest configuration and fixtures for deliberate-development bundle tests."""
import os
import pytest
import yaml
from pathlib import Path

BUNDLE_ROOT = Path(__file__).parent.parent
RECIPES_DIR = BUNDLE_ROOT / "recipes"


@pytest.fixture
def bundle_root():
    """Return path to bundle root."""
    return BUNDLE_ROOT


@pytest.fixture
def recipes_dir():
    """Return path to recipes directory."""
    return RECIPES_DIR


@pytest.fixture
def all_recipes():
    """Load all recipe YAML files."""
    recipes = {}
    for recipe_file in RECIPES_DIR.glob("*.yaml"):
        with open(recipe_file) as f:
            recipes[recipe_file.stem] = yaml.safe_load(f)
    return recipes


@pytest.fixture
def sample_project_path(tmp_path):
    """Create a temporary sample project for testing."""
    project = tmp_path / "sample-project"
    project.mkdir()
    (project / "src").mkdir()
    (project / "src" / "main.py").write_text('''
"""Sample main module for testing."""

def hello(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(hello("World"))
''')
    (project / "README.md").write_text("# Sample Project\n\nA minimal test project.")
    return project


@pytest.fixture
def mock_agent_responses():
    """Load mock agent responses for recipe testing."""
    from .mocks.agent_responses import MOCK_RESPONSES
    return MOCK_RESPONSES
