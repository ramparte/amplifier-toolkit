"""Mock agent responses for recipe testing.

Each recipe has a dict of step_id -> mock_response.
These simulate what agents would return without calling real LLMs.
"""

MOCK_RESPONSES = {
    "deliberate-design": {
        "decompose": """
## Problem Decomposition

### Restated Request
The user wants to add a caching layer to improve performance.

### Components
1. Cache storage mechanism
2. Cache key generation
3. Cache invalidation logic
4. Integration points

### Dependencies
- Existing data access layer
- Configuration system

### Success Criteria
- Reduced latency for repeated requests
- Cache hit rate > 80%
""",
        "explore": """
## Solution Exploration

### Option A: In-Memory Cache
- Approach: Use Python dict with TTL
- Pros: Simple, fast, no dependencies
- Cons: Lost on restart, memory pressure
- Effort: Low

### Option B: Redis Cache
- Approach: External Redis server
- Pros: Persistent, distributed
- Cons: Infrastructure dependency
- Effort: Medium

### Option C: Hybrid Cache
- Approach: In-memory with Redis fallback
- Pros: Best of both
- Cons: Complexity
- Effort: High
""",
        "generalize": """
## Generalization Analysis

This is a common pattern - caching decorator could be reused.

Recommendation: Create a reusable @cached decorator that can wrap any function.
This provides value beyond this single use case.
""",
        "specify": """
## Implementation Specification

### Overview
Implement a caching decorator with configurable backend.

### Components
1. CacheBackend protocol (interface)
2. InMemoryBackend (default)
3. @cached decorator

### Implementation Order
1. Define protocol
2. Implement in-memory backend
3. Create decorator
4. Add tests

### Definition of Done
- All components implemented
- Tests pass
- Documentation added
""",
        "implement": """
## Implementation Result

Created the following files:
- src/cache/backend.py - CacheBackend protocol
- src/cache/memory.py - InMemoryBackend
- src/cache/decorator.py - @cached decorator
- tests/test_cache.py - Unit tests

All tests pass. Cache hit rate verified at 85%.
"""
    },
    
    "feature-development": {
        "create-workspace": """
## Workspace Created

Path: ~/workspaces/test-feature
- Git initialized
- AGENTS.md created
- Ready for development
""",
        "gather-context": """
## Context Summary

Relevant files:
- src/main.py - Entry point
- src/utils.py - Helper functions

Similar patterns found in existing codebase.
""",
        "decompose": "Problem broken into 3 components.",
        "explore-solutions": "2 approaches analyzed.",
        "generalization-check": "Direct implementation recommended.",
        "create-spec": "Specification created at SPEC.md",
        "implement": "Feature implemented and validated.",
        "validate": "PASS - All criteria met.",
        "summarize": "Feature complete, ready for handoff."
    },
    
    "issue-resolution": {
        "reconnaissance": "Affected components identified.",
        "root-cause-analysis": "Root cause: missing null check at line 42.",
        "gate1-summary": "Investigation complete, ready for approval.",
        "implement-fix": "Fix applied, committed locally.",
        "define-evidence": "3 evidence requirements defined.",
        "shadow-test": "All tests PASS.",
        "gate2-summary": "Solution validated, ready for push.",
        "push-changes": "Pushed to origin/main.",
        "smoke-test": "Independent validation PASS.",
        "final-summary": "Issue resolved successfully."
    },
    
    "deliberate-review": {
        "gather-context": "PR changes summarized.",
        "structural-analysis": "PASS - Uses structural prevention.",
        "antipattern-check": "No anti-patterns detected.",
        "recommendations": "APPROVE - Code looks good."
    }
}
