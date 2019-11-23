"""Provides tab widgets for the high-level views."""

import os
from typing import Tuple

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QGridLayout, QLabel, QLineEdit, QScrollArea, QSplitter, QWidget

from .state import GlobalState
from .utils import is_image_file
from .widgets import FileTagView, FileTreeView, GalleryView, ImageView, TagListView


class FileTab(QWidget):
    """Combines a filesystem view, tag adding entry, tag list, and image display."""
    title = 'Filesystem'

    def __init__(self, global_state: GlobalState):
        super().__init__()

        self.global_state = global_state

        layout, self._file_tree, self._tagging, self._image = self._layout()
        self.setLayout(layout)

    # -- Initialization

    def _layout(self) -> QGridLayout:
        layout = QGridLayout()

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


class GalleryTab(QWidget):
    """Combines a thumbnail galery, tag searching entry, tag list, and image display."""
    title = 'Gallery'

    def __init__(self, global_state: GlobalState):
        super().__init__()

        self.global_state = global_state

        layout, self._gallery, self._entry, self._taglist, self._image = self._layout()
        self.setLayout(layout)

    # -- Initialization

    def _layout(self) -> Tuple[QGridLayout, GalleryView, QLineEdit, TagListView, ImageView]:
        layout = QGridLayout()

        # Gallery
        gallery = GalleryView(self._load_image)
        layout.addWidget(gallery, 0, 0)

        splitter = QSplitter()
        layout.addWidget(splitter, 1, 0)

        left = QWidget()
        splitter.addWidget(left)

        left_layout = QGridLayout()
        left.setLayout(left_layout)

        # Tag search
        left_layout.addWidget(QLabel('Search:'), 0, 0)
        entry = QLineEdit()
        entry.returnPressed.connect(self._search)
        entry.setCompleter(self.global_state.tag_completer)
        left_layout.addWidget(entry, 0, 1)

        # Tag list
        taglist = TagListView()
        left_layout.addWidget(taglist, 1, 0, 1, 2)

        # Image
        image = ImageView()
        splitter.addWidget(wrap_image(image))

        # Initialize equal widths (needs to be set at the end)
        splitter.setSizes([1000000, 1000000])

        return layout, gallery, entry, taglist, image

    # -- Callbacks

    def _load_image(self, filepath: str):
        self._taglist.load(os.path.split(filepath)[-1])
        self._image.load(filepath)

    def _search(self):
        text = self._entry.text().strip().lower()
        self._gallery.search(text)


def wrap_image(image: ImageView) -> QScrollArea:
    """Wraps an image in a scrollable and resizable container."""
    area = QScrollArea()
    area.setWidget(image)
    area.setWidgetResizable(True)
    area.setAlignment(Qt.AlignCenter)
    return area
