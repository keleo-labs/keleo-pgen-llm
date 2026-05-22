"""
Practice Language Translation Utilities

This package provides utilities for the translate-methodology skill:
- Resource management (baseline/schema loading)
- Module validation (size checking, splitting)
- Practice building (incremental JSON construction)
- Integrity validation (cross-practice, schema compliance)
- Session management (checkpoints, resume)
- Citation parsing (URL extraction)
- Subagent coordination (parallel processing)
"""

__version__ = "1.0.0"

from .resource_manager import load_baseline, load_schema
from .module_validator import check_module_size, should_split_module
from .practice_builder import build_practice_from_modules
from .integrity_validator import validate_cross_practice_references

__all__ = [
    "load_baseline",
    "load_schema",
    "check_module_size",
    "should_split_module",
    "build_practice_from_modules",
    "validate_cross_practice_references",
]
