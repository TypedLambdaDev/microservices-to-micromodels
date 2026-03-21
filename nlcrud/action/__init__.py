"""Action module for NLCRUD.

Provides domain-level abstractions for CRUD operations.
"""
from nlcrud.action.action import Action
from nlcrud.action.builder import ActionBuilder, build_action, get_builder, set_builder

__all__ = [
    "Action",
    "ActionBuilder",
    "build_action",
    "get_builder",
    "set_builder",
]
