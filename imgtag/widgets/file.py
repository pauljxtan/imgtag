import itertools
from typing import Callable

from PySide2.QtCore import QModelIndex, Qt
from PySide2.QtWidgets import QFileSystemModel, QTreeView

from ..data import get_file_tags
from ..logger import get_logger
from ..settings import IMAGE_EXTS, ROOT_DIR
from ..utils import is_image_file

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
