from typing import Tuple

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QGridLayout, QSplitter, QWidget

from ..state import GlobalState
from ..utils import is_image_file
from ..widgets import FileTagView, FileTreeView, ImageView, wrap_image


class FileTab(QWidget):
    """Combines a filesystem view, tag adding entry, tag list, and image display."""
    title = 'Filesystem'

    def __init__(self, global_state: GlobalState):
        super().__init__()

        self.global_state = global_state

        layout, self._file_tree, self._tagging, self._image = self._layout()
        self.setLayout(layout)

    # -- Initialization

    def _layout(self) -> Tuple[QGridLayout, FileTreeView, FileTagView, ImageView]:
        layout = QGridLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        splitter = QSplitter()
        layout.addWidget(splitter, 0, 0, 0, 0)

        left_splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(left_splitter)

        # Top left
        file_tree = FileTreeView(self._on_file_tree_selection_changed)
        left_splitter.addWidget(file_tree)

        # Bottom left
        tagging = FileTagView(self.global_state)
        left_splitter.addWidget(tagging)

        # Right
        image = ImageView()
        splitter.addWidget(wrap_image(image))

        # Initialize equal widths (needs to be set at the end)
        splitter.setSizes([1000000, 1000000])

        return layout, file_tree, tagging, image

    def _on_file_tree_selection_changed(self, new_selection, _old_selection):
        indices = new_selection.indexes()
        if len(indices) == 0:
            return
        filepath = self._file_tree.model().filePath(indices[0])
        if filepath and is_image_file(filepath):
            self._tagging.load(filepath)
            self._image.load(filepath)
