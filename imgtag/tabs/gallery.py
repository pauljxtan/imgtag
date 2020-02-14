import os
from typing import Tuple

from PySide2.QtWidgets import QCheckBox, QGridLayout, QLabel, QSplitter, QWidget

from ..state import GlobalState
from ..widgets import GalleryView, ImageView, MultiTagEntry, TagListView, wrap_image


class GalleryTab(QWidget):
    """Combines a thumbnail galery, tag searching entry, tag list, and image display."""
    title = 'Gallery'

    def __init__(self, global_state: GlobalState):
        super().__init__()

        self.global_state = global_state

        (layout, self._gallery, self._entry, self._shuffle, self._taglist,
         self._image) = self._layout()
        self.setLayout(layout)

    # -- Initialization

    def _layout(self) -> Tuple:
        layout = QGridLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Gallery
        gallery = GalleryView(self._load_image)
        layout.addWidget(gallery, 0, 0)

        splitter = QSplitter()
        layout.addWidget(splitter, 1, 0)

        left = QWidget()
        splitter.addWidget(left)

        left_layout = QGridLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left.setLayout(left_layout)

        # Tag search
        left_layout.addWidget(QLabel('Search:'), 0, 0)
        entry = MultiTagEntry()
        entry.returnPressed.connect(self._search)
        entry.setCompleter(self.global_state.tag_completer)
        left_layout.addWidget(entry, 0, 1)

        # Shuffle toggle
        shuffle = QCheckBox('Shuffle?')
        left_layout.addWidget(shuffle, 0, 2)

        # Tag list
        taglist = TagListView()
        left_layout.addWidget(taglist, 1, 0, 1, 3)

        # Image
        image = ImageView()
        splitter.addWidget(wrap_image(image))

        # Initialize equal widths (needs to be set at the end)
        splitter.setSizes([1000000, 1000000])

        return layout, gallery, entry, shuffle, taglist, image

    # -- Callbacks

    def _load_image(self, filepath: str):
        self._taglist.load(os.path.split(filepath)[-1])
        self._image.load(filepath)

    def _search(self):
        text = self._entry.text().strip().lower()
        shuffle = self._shuffle.isChecked()
        self._gallery.search(text, shuffle=shuffle)
