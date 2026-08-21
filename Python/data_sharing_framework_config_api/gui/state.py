"""Shared GUI editor state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class EditorState:
    """State shared across selection, details, and inline editor helpers."""

    selection_guard: bool = False
    modify_panel: Optional[object] = None
    edit_item_id: Optional[str] = None
    edit_fields: dict = field(default_factory=dict)
    edit_initial_values: dict = field(default_factory=dict)
    save_changes: Optional[Callable[[], bool]] = None


def editor_state(details_text):
    """Return the editor state container attached to the details widget."""

    state = getattr(details_text, "editor_state", None)
    if state is None:
        state = EditorState()
        details_text.editor_state = state
    return state
