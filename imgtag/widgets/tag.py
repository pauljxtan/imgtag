import os
from typing import Callable

from PySide2.QtCore import QEvent, QModelIndex, Qt, Signal
from PySide2.QtGui import QContextMenuEvent, QStandardItem, QStandardItemModel
from PySide2.QtWidgets import (QAction, QGridLayout, QHeaderView, QLabel, QLineEdit, QMenu,
                               QTableView, QWidget)

from ..data import add_file_tag, get_file_tags, remove_file_tag
from ..logger import get_logger
from ..state import GlobalState
from ..utils import is_image_file

logger = get_logger(__name__)


class FileTagView(QWidget):
    """Combines a tag entry field and tag list table."""
    def __init__(self, global_state: GlobalState):
        super().__init__()

        self.global_state = global_state
        self._selected_filepath = ''

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Tag entry
        layout.addWidget(QLabel('Add tag:'), 0, 0)
        self._entry = MultiTagEntry()
        self._entry.returnPressed.connect(self._add_file_tag)
        self._entry.setCompleter(self.global_state.tag_completer)
        layout.addWidget(self._entry, 0, 1)

        # Tag list
        self._taglist = TagListView(self._remove_file_tag)
        layout.addWidget(self._taglist, 1, 0, 1, 2)

    # -- Public

    def load(self, filepath: str):
        self._selected_filepath = filepath
        self._taglist.load(self._selected_filename)

    # -- Properties

    @property
    def _selected_filename(self) -> str:
        return os.path.split(self._selected_filepath)[-1]

    @property
    def _selected_tag(self) -> str:
        idx = self._taglist.selectionModel().currentIndex()
        if idx.column() > 0:
            # Get tagname even if another column selected
            idx = idx.siblingAtColumn(0)
        if idx.row() == -1:
            return ''
        return self._taglist.tag_by_index(idx)

    # -- Callbacks

    def _add_file_tag(self):
        if not is_image_file(self._selected_filepath):
            return
        tagname = self._entry.text().strip().replace(' ', '_').lower()
        if tagname == '':
            return
        add_file_tag(self._selected_filename, tagname)
        self._taglist.load(self._selected_filename)
        self._entry.clear()

    def _remove_file_tag(self):
        remove_file_tag(self._selected_filename, self._selected_tag)
        self._taglist.load(self._selected_filename)


class TagListView(QTableView):
    """A tag list table with an optional context menu."""
    def __init__(self, callback_remove_tag: Callable = None):
        super().__init__()

        self._callback_remove_tag = callback_remove_tag

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['Tag', '# Files'])
        self.setModel(model)

        # FIXME: seems hacky
        if self._callback_remove_tag:
            self._remove_action = QAction('Remove tag from image')
            self._remove_action.triggered.connect(self._callback_remove_tag)

    # Override
    def contextMenuEvent(self, event: QContextMenuEvent):
        # FIXME: seems hacky
        if self._callback_remove_tag:
            menu = QMenu()
            menu.addAction(self._remove_action)
            menu.exec_(event.globalPos())

    # -- Public

    def tag_by_index(self, idx: QModelIndex) -> str:
        return self.model().itemFromIndex(idx).text()

    def load(self, filename: str):
        model = self.model()
        model.removeRows(0, model.rowCount())
        for name, file_count in get_file_tags(filename):
            model.appendRow([QStandardItem(name), QStandardItem(str(file_count))])


class MultiTagEntry(QLineEdit):
    tabPressed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabPressed.connect(self.cycle_completion)

    def cycle_completion(self):
        self.completer().popup().setCurrentIndex(self.completer().currentIndex())
        idx = self.completer().currentRow()
        if not self.completer().setCurrentRow(idx + 1):
            self.completer().setCurrentRow(0)

    def event(self, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            self.tabPressed.emit()
            return True
        return super().event(event)
