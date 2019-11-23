"""Provides a class for storing and passing around globally shared state.

There should ideally be as little in this module as possible.
"""

from PySide2.QtCore import QStringListModel
from PySide2.QtWidgets import QCompleter

from .data import get_all_tags


class GlobalState(object):
    """Stores all global state not handled by Qt."""

    # TODO: Refactor settings into here
    def __init__(self):
        self._tag_completer = QCompleter()
        # Sort by descending file count
        tagnames = [tag[0] for tag in sorted(get_all_tags(), key=lambda t: -t[1])]
        self._tag_completer.setModel(QStringListModel(tagnames))

    @property
    def tag_completer(self) -> QCompleter:
        """A dropdown completer used for any tag entry widget."""
        return self._tag_completer
