from PySide2.QtCore import Qt
from PySide2.QtWidgets import QScrollArea

from .file import FileTreeView
from .gallery import GalleryView
from .image import ImageView
from .tag import FileTagView, MultiTagEntry, TagListView


def wrap_image(image: ImageView) -> QScrollArea:
    """Wraps an image in a scrollable and resizable container."""
    area = QScrollArea()
    area.setWidget(image)
    area.setWidgetResizable(True)
    area.setAlignment(Qt.AlignCenter)
    return area
