"""Tests for recipe YAML structure validation."""
import pytest
import yaml
from pathlib import Path


class TestRecipeStructure:
    """Validate recipe YAML files have correct structure."""

    def test_all_recipes_are_valid_yaml(self, recipes_dir):
        """All recipe files should be valid YAML."""
        for recipe_file in recipes_dir.glob("*.yaml"):
            with open(recipe_file) as f:
                recipe = yaml.safe_load(f)
            assert recipe is not None, f"{recipe_file.name} is empty or invalid"

    def test_recipes_have_required_fields(self, all_recipes):
        """All recipes must have name, description, and steps/stages."""
        required_fields = ["name", "description"]
        
        for name, recipe in all_recipes.items():
            for field in required_fields:
                assert field in recipe, f"{name} missing required field: {field}"
            
            # Must have either steps or stages
            has_steps = "steps" in recipe
            has_stages = "stages" in recipe
            assert has_steps or has_stages, f"{name} must have 'steps' or 'stages'"

    def test_no_hardcoded_providers(self, all_recipes):
        """Recipes should not hardcode provider or model."""
        for name, recipe in all_recipes.items():
            yaml_str = yaml.dump(recipe)
            assert "provider:" not in yaml_str or "provider: " not in yaml_str.split("approval_context")[0] if "approval_context" in yaml_str else "provider:" not in yaml_str, \
                f"{name} has hardcoded provider"

    def test_steps_have_required_fields(self, all_recipes):
        """Each step must have id, agent, and prompt."""
        step_required = ["id", "agent", "prompt"]
        
        for name, recipe in all_recipes.items():
            steps = recipe.get("steps", [])
            
            # Handle staged recipes
            if "stages" in recipe:
                for stage_name, stage in recipe["stages"].items():
                    steps.extend(stage.get("steps", []))
            
            for step in steps:
                for field in step_required:
                    assert field in step, \
                        f"{name} step '{step.get('id', 'unknown')}' missing: {field}"

    def test_step_ids_are_unique(self, all_recipes):
        """Step IDs must be unique within a recipe."""
        for name, recipe in all_recipes.items():
            step_ids = []
            steps = recipe.get("steps", [])
            
            if "stages" in recipe:
                for stage_name, stage in recipe["stages"].items():
                    steps.extend(stage.get("steps", []))
            
            for step in steps:
                step_id = step.get("id")
                assert step_id not in step_ids, \
                    f"{name} has duplicate step id: {step_id}"
                step_ids.append(step_id)

    def test_context_variables_defined(self, all_recipes):
        """Recipes should define context variables they use."""
        for name, recipe in all_recipes.items():
            if "context" not in recipe:
                continue  # Some recipes may not need context
            
            context = recipe["context"]
            assert isinstance(context, dict), f"{name} context should be a dict"


class TestSpecificRecipes:
    """Tests for specific recipe requirements."""

    def test_feature_development_has_workspace_step(self, all_recipes):
        """feature-development recipe must create a workspace."""
        recipe = all_recipes.get("feature-development")
        if recipe is None:
            pytest.skip("feature-development recipe not found")
        
        steps = recipe.get("steps", [])
        step_ids = [s.get("id") for s in steps]
        
        assert "create-workspace" in step_ids, \
            "feature-development must have create-workspace step"

    def test_issue_resolution_has_approval_gates(self, all_recipes):
        """issue-resolution recipe must have approval gates."""
        recipe = all_recipes.get("issue-resolution")
        if recipe is None:
            pytest.skip("issue-resolution recipe not found")
        
        # Check for stages with requires_approval
        stages = recipe.get("stages", {})
        approval_stages = [
            name for name, stage in stages.items()
            if stage.get("requires_approval", False)
        ]
        
        assert len(approval_stages) >= 2, \
            "issue-resolution should have at least 2 approval gates"
