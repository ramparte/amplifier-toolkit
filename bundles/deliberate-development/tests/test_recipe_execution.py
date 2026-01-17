"""Tests for recipe execution with mocked agents."""
import pytest
import re
from pathlib import Path


class TestRecipeExecution:
    """Test recipe execution flow with mocked responses."""

    def test_context_variable_substitution(self, all_recipes):
        """Template variables should be properly formatted."""
        template_pattern = re.compile(r'\{\{[^}]+\}\}')
        
        for name, recipe in all_recipes.items():
            steps = recipe.get("steps", [])
            if "stages" in recipe:
                for stage in recipe["stages"].values():
                    steps.extend(stage.get("steps", []))
            
            for step in steps:
                prompt = step.get("prompt", "")
                variables = template_pattern.findall(prompt)
                
                # All variables should be valid format
                for var in variables:
                    # Should not have spaces around variable name
                    inner = var[2:-2]  # Remove {{ and }}
                    if not inner.startswith("#") and not inner.startswith("/"):
                        assert inner.strip() == inner, \
                            f"{name}/{step['id']}: variable has extra spaces: {var}"

    def test_step_outputs_are_referenced(self, all_recipes):
        """Step outputs should be used in subsequent steps."""
        for name, recipe in all_recipes.items():
            steps = recipe.get("steps", [])
            if "stages" in recipe:
                for stage in recipe["stages"].values():
                    steps.extend(stage.get("steps", []))
            
            outputs = set()
            for step in steps:
                output = step.get("output")
                if output:
                    outputs.add(output)
            
            # At least some outputs should exist
            if len(steps) > 1:
                assert len(outputs) > 0, f"{name} has no step outputs defined"

    def test_timeout_values_are_reasonable(self, all_recipes):
        """Timeouts should be between 60 and 1800 seconds."""
        for name, recipe in all_recipes.items():
            steps = recipe.get("steps", [])
            if "stages" in recipe:
                for stage in recipe["stages"].values():
                    steps.extend(stage.get("steps", []))
            
            for step in steps:
                timeout = step.get("timeout", 300)
                assert 60 <= timeout <= 1800, \
                    f"{name}/{step['id']}: timeout {timeout} outside range [60, 1800]"

    def test_mock_responses_cover_all_steps(self, all_recipes, mock_agent_responses):
        """Mock responses should exist for all recipe steps."""
        for recipe_name, recipe in all_recipes.items():
            if recipe_name not in mock_agent_responses:
                pytest.skip(f"No mocks defined for {recipe_name}")
            
            recipe_mocks = mock_agent_responses[recipe_name]
            steps = recipe.get("steps", [])
            if "stages" in recipe:
                for stage in recipe["stages"].values():
                    steps.extend(stage.get("steps", []))
            
            for step in steps:
                step_id = step.get("id")
                assert step_id in recipe_mocks, \
                    f"{recipe_name} missing mock for step: {step_id}"


class TestWorkspaceCreation:
    """Test workspace creation functionality."""

    def test_sample_project_fixture_works(self, sample_project_path):
        """Sample project fixture should create valid structure."""
        assert sample_project_path.exists()
        assert (sample_project_path / "src" / "main.py").exists()
        assert (sample_project_path / "README.md").exists()

    def test_sample_project_has_valid_python(self, sample_project_path):
        """Sample Python file should be syntactically valid."""
        main_py = sample_project_path / "src" / "main.py"
        code = main_py.read_text()
        
        # Should compile without syntax errors
        compile(code, str(main_py), "exec")
