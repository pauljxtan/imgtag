from PySide2.QtCore import Qt
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QLabel, QSizePolicy

from ..logger import get_logger

logger = get_logger(__name__)


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
