import os
import random
from typing import Callable, List, Tuple

from PySide2.QtCore import QObject, QRunnable, QSize, Qt, QThreadPool, Signal, Slot
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QComboBox, QGridLayout, QLabel, QListWidget, QListWidgetItem, QWidget

from ..data import get_file_metadata, get_file_paths, get_files_with_tags
from ..logger import get_logger
from ..settings import ROOT_DIR

logger = get_logger(__name__)


class GalleryView(QWidget):
    """A gallery widget with paginated thumbnails, aligned horizontally and scrollable."""

    # Always fit to configured height
    thumbnail_width = 10000
    thumbnail_height = 100
    padding_height = 70
    images_per_page = 20

    def __init__(self, load_image_callback: Callable):
        super().__init__()

        self._load_image_callback = load_image_callback
        # For async thumbnail loading
        self._thread_pool = QThreadPool()
        # For pagination
        self._all_filenames: List[str] = []

        self.setFixedHeight(self.thumbnail_height + self.padding_height)

        (layout, self._page_select, self._query_label, self._viewing_label,
         self._gallery) = self._layout()
        self.setLayout(layout)

    def _layout(self) -> Tuple[QGridLayout, QComboBox, QLabel, QLabel, QListWidget]:
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        page_label = QLabel('Page:')
        page_label.setFixedWidth(40)
        layout.addWidget(page_label, 0, 0)

        # Page select dropdown
        page_select = QComboBox()
        page_select.currentTextChanged.connect(self._on_page_changed)
        page_select.setFixedWidth(60)
        layout.addWidget(page_select, 0, 1)

        # Query results and image label
        query_label = QLabel('Query:')
        layout.addWidget(query_label, 0, 2)
        viewing_label = QLabel('Viewing:')
        layout.addWidget(viewing_label, 0, 3)

        # Gallery
        gallery = QListWidget()
        gallery.setFlow(QListWidget.LeftToRight)
        gallery.setWrapping(False)
        gallery.setViewMode(QListWidget.IconMode)
        gallery.setIconSize(QSize(self.thumbnail_width, self.thumbnail_height))
        gallery.currentItemChanged.connect(self._on_item_changed)
        layout.addWidget(gallery, 1, 0, 1, 4)

        return layout, page_select, query_label, viewing_label, gallery

    # -- Public

    @property
    def page_count(self) -> int:
        """The total number of pages for the current search results."""
        count = len(self._all_filenames) // self.images_per_page
        if len(self._all_filenames) % self.images_per_page == 0:
            return count
        return count + 1

    def search(self, text: str, shuffle: bool):
        tags = text.split()
        filenames = get_files_with_tags([t for t in tags if not t.startswith('-')],
                                        [t[1:] for t in tags if t.startswith('-')])
        if shuffle:
            random.shuffle(filenames)
        self.populate(filenames)
        self._query_label.setText(
            f'Query: {tags} | {len(filenames)} images ({self.page_count} pages)')

    def populate(self, filenames: List[str]):
        self._all_filenames = filenames
        self._page_select.clear()
        self._page_select.addItems([str(i) for i in range(1, self.page_count + 1)])

        # NOTE: We don't need to call _populate() here since the page change handler does it
        #       (Which includes the first page)

    # -- Callbacks

    def _on_page_changed(self, val: str):
        if not val or len(self._all_filenames) == 0:
            return
        # 1-indexed on UI, 0-indexed internally
        self._change_page(int(val) - 1)

    def _on_item_changed(self, current, _previous):
        if not current:
            return
        filepath = current.data(Qt.StatusTipRole)
        self._viewing_label.setText(f'Viewing: {os.path.split(filepath)[-1]}')
        self._load_image_callback(filepath)

    # -- Helpers

    def _change_page(self, idx: int):
        start, end = self.images_per_page * idx, self.images_per_page * (idx + 1)
        filepaths = get_file_paths(ROOT_DIR, self._all_filenames[start:end])
        self._populate(filepaths)

    def _populate(self, filepaths: List[str]):
        self._gallery.clear()
        for i, filepath in enumerate(filepaths):
            if not filepath:
                continue
            # Thumbnail loads are a little slow, so push them to the background
            worker = IconWorker(i, filepath)
            worker.signal.result.connect(self._set_icon)
            self._thread_pool.start(worker)

    def _set_icon(self, result: Tuple[int, QIcon, str, str]):
        (idx, icon, filepath, label) = result
        item = QListWidgetItem(icon, label)
        # Store filepath to be retrieved by other components
        item.setData(Qt.StatusTipRole, filepath)
        self._gallery.addItem(item)


# Signals must be defined on a QObject (or descendant)
class IconWorkerSignal(QObject):
    result = Signal(tuple)


class IconWorker(QRunnable):
    """An async worker used to load thumbnails in the background."""
    def __init__(self, item_idx: int, filepath: str):
        super().__init__()
        self._item_idx = item_idx
        self._filepath = filepath
        self.signal = IconWorkerSignal()

    @Slot()
    def run(self):
        icon = QIcon(self._filepath)
        label = self._get_label()
        self.signal.result.emit((self._item_idx, icon, self._filepath, label))

    def _get_label(self):
        filename = os.path.split(self._filepath)[-1]
        meta = get_file_metadata(filename)
        return f'Tags: {meta["tag_count"]}'
