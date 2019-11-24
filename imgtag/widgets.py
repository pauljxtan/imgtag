"""Provides all widgets below the "tab" level."""

import itertools
import os
from typing import Callable, List, Tuple

from PySide2.QtCore import QModelIndex, QObject, QRunnable, QSize, Qt, QThreadPool, Signal, Slot
from PySide2.QtGui import QContextMenuEvent, QIcon, QPixmap, QStandardItem, QStandardItemModel
from PySide2.QtWidgets import (QAction, QComboBox, QFileSystemModel, QGridLayout, QHeaderView,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QSizePolicy,
                               QTableView, QTreeView, QWidget)

from .data import add_file_tag, get_file_paths, get_file_tags, get_files_with_tags, remove_file_tag
from .logger import get_logger
from .settings import IMAGE_EXTS, ROOT_DIR
from .state import GlobalState
from .utils import is_image_file

logger = get_logger(__name__)


class FileTreeView(QTreeView):
    """A slimmed down and slightly customized filesystem tree."""
    def __init__(self, callback_selection_changed: Callable):
        super().__init__()

        model = FileTreeModel()

        # Make non-image files (as configured) unselectable
        model.setNameFilters(
            list(itertools.chain(*[[f'*.{ext.lower()}', f'*.{ext.upper()}']
                                   for ext in IMAGE_EXTS])))

        model.setRootPath(ROOT_DIR)
        self.setModel(model)
        self.setRootIndex(model.index(ROOT_DIR))

        # Hide size, type, date modified
        header = self.header()
        header.hideSection(1)
        header.hideSection(2)
        header.hideSection(3)

        selection_model = self.selectionModel()
        selection_model.selectionChanged.connect(callback_selection_changed)

        # Set fixed width for filename column
        self.setColumnWidth(0, 350)
        for i in range(1, self.model().columnCount() + 1):
            self.resizeColumnToContents(i)


class FileTreeModel(QFileSystemModel):
    """A filesystem tree model that can be extended with custom columns."""
    def __init__(self):
        super().__init__()

    # Override
    def columnCount(self, parent=QModelIndex()):
        return super().columnCount() + 1

    # Override
    def data(self, index, role):
        if index.column() < self.columnCount() - 1:
            return super().data(index, role)

        if role == Qt.DisplayRole:
            filename = self.fileName(index.siblingAtColumn(0))
            if not is_image_file(filename):
                return '-'
            if index.column() == self.columnCount() - 1:
                return str(len(get_file_tags(filename)))

    # Override
    def headerData(self, section, orientation, role):
        if section < self.columnCount() - 1:
            return super().headerData(section, orientation, role)

        if role == Qt.DisplayRole:
            if section == self.columnCount() - 1:
                return '# Tags'
        if role == Qt.TextAlignmentRole:
            return Qt.AlignHCenter


class FileTagView(QWidget):
    """Combines a tag entry field and tag list table."""
    def __init__(self, global_state: GlobalState):
        super().__init__()

        self.global_state = global_state
        self._selected_filepath = ''

        layout = QGridLayout()
        self.setLayout(layout)

        # Tag entry
        layout.addWidget(QLabel('Add tag:'), 0, 0)
        self._entry = QLineEdit()
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


class ImageView(QLabel):
    """A simple image display."""
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        # Set a null pixmap as a placeholder
        self._pixmap = QPixmap()
        self._pixmap.fill()
        self._has_image = False

    def load(self, filepath: str):
        self._has_image = True
        self._pixmap = QPixmap(filepath)
        self.setPixmap(
            self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def clear(self):
        self._has_image = False
        pixmap = QPixmap()
        pixmap.fill()
        self.setPixmap(pixmap)

    # Override
    def resizeEvent(self, _event):
        if self._has_image:
            self.setPixmap(
                self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))


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

    def search(self, text: str):
        tags = text.split()
        filenames = get_files_with_tags(tags)
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
            worker = IconWorker(i, filepath, label='')
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
    def __init__(self, item_idx: int, filepath: str, label: str):
        super().__init__()
        self._item_idx = item_idx
        self._filepath = filepath
        self._label = label
        self.signal = IconWorkerSignal()

    @Slot()
    def run(self):
        icon = QIcon(self._filepath)
        self.signal.result.emit((self._item_idx, icon, self._filepath, self._label))
