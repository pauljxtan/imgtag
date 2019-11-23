"""Provides the top-level window widget."""

from PySide2.QtWidgets import QAction, QApplication, QMainWindow, QTabWidget

from .state import GlobalState
from .tabs import FileTab, GalleryTab


class MainWindow(QMainWindow):
    """The top-level window."""
    title = 'ImgTag'

    def __init__(self):
        super().__init__()

        self.global_state = GlobalState()

        self.setWindowTitle(self.title)
        self._make_menubar()
        self.setCentralWidget(self._central_widget())

    def _make_menubar(self):
        menubar = self.menuBar()

        quit_action = QAction('&Quit', self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.triggered.connect(QApplication.quit)
        menubar.addAction(quit_action)

    def _central_widget(self) -> QTabWidget:
        tabs = QTabWidget()

        self._file_tab = FileTab(self.global_state)
        tabs.addTab(self._file_tab, self._file_tab.title)

        self._gallery_tab = GalleryTab(self.global_state)
        tabs.addTab(self._gallery_tab, self._gallery_tab.title)

        return tabs
