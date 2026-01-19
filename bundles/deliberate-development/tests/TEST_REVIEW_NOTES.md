# Test Suite Review Notes

**Reviewed**: 2026-01-19  
**Status**: Tests pass, minor improvements identified  
**Priority**: Low - cleanup when convenient

---

## Summary

The test suite is well-structured and functional. These are optional improvements for maintainability.

---

## Issues to Address

### 1. Confusing Assertion in `test_recipe_structure.py:30-35`

**Current code:**
```python
assert "provider:" not in yaml_str or "provider: " not in yaml_str.split("approval_context")[0] if "approval_context" in yaml_str else "provider:" not in yaml_str, \
    f"{name} has hardcoded provider"
```

**Problem**: Ternary-within-assertion is hard to read.

**Suggested fix:**
```python
def test_no_hardcoded_providers(self, all_recipes):
    """Recipes should not hardcode provider or model."""
    for name, recipe in all_recipes.items():
        yaml_str = yaml.dump(recipe)
        
        # Skip provider mentions inside approval_context (they're allowed there)
        if "approval_context" in yaml_str:
            check_portion = yaml_str.split("approval_context")[0]
        else:
            check_portion = yaml_str
            
        assert "provider:" not in check_portion, f"{name} has hardcoded provider"
```

---

### 2. Duplicate Fixture Logic in `conftest.py:34-50`

**Problem**: `sample_project_path` fixture creates a project structure dynamically, but `fixtures/sample-project/` already exists with similar content.

**Options:**
- A) Use the existing fixture directory instead of creating dynamically
- B) Remove the `fixtures/sample-project/` directory

**Suggested fix (Option A):**
```python
@pytest.fixture
def sample_project_path():
    """Return path to the sample project fixture."""
    return Path(__file__).parent / "fixtures" / "sample-project"
```

---

### 3. Docstring Mismatch in `test_recipe_execution.py:32-48`

**Current docstring:**
```python
def test_step_outputs_are_referenced(self, all_recipes):
    """Step outputs should be used in subsequent steps."""
```

**Problem**: Test only checks outputs *exist*, not that they're *referenced*.

**Suggested fix** (update docstring to match behavior):
```python
def test_steps_define_outputs(self, all_recipes):
    """Multi-step recipes should define step outputs."""
```

Or implement actual reference checking if that's the intent.

---

### 4. Consider Adding Negative Tests

The suite tests happy paths well but could benefit from a few negative tests:

```python
def test_invalid_yaml_raises_error(self, tmp_path):
    """Invalid YAML should fail to parse."""
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("name: [unclosed bracket")
    
    with pytest.raises(yaml.YAMLError):
        with open(bad_yaml) as f:
            yaml.safe_load(f)

def test_missing_required_field_detected(self, tmp_path):
    """Recipe missing 'name' should fail validation."""
    incomplete = tmp_path / "incomplete.yaml"
    incomplete.write_text("description: no name field\nsteps: []")
    # ... test that validation catches this
```

---

## What's Good (Keep These Patterns)

1. **`test_mock_responses_cover_all_steps`** - Enforces mock completeness. Excellent pattern.

2. **Class-based organization** - `TestRecipeStructure`, `TestRecipeExecution`, `TestWorkspaceCreation` provide clear grouping.

3. **CI compatibility** - Git user configuration in subprocess tests ensures CI works.

4. **Fixture design** - Clean separation in `conftest.py`, proper use of `tmp_path`.

5. **Integration test** - `test_full_workspace_creation_flow` tests the complete workflow.

---

## Checklist

- [ ] Refactor confusing assertion in `test_no_hardcoded_providers`
- [ ] Resolve fixture duplication (choose dynamic or static)
- [ ] Fix docstring in `test_step_outputs_are_referenced`
- [ ] Add 1-2 negative test cases
