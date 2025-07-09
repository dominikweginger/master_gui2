from PySide6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel
)

class MasterWindow(QMainWindow):
    """
    Hauptfenster der Anwendung mit QStackedWidget und Paginierungssteuerung.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Master GUI")
        self.resize(800, 600)

        # Zentrales Widget und vertikales Layout
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # QStackedWidget für Seiten
        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages)

        # Beispiel: 3 Platzhalter-Seiten
        for _ in range(3):
            page = QWidget()
            self.pages.addWidget(page)

        # Paginierungs-Leiste unterhalb der Seiten
        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("← Vor")
        self.page_label = QLabel(self._label_text())
        self.next_btn = QPushButton("Nächste →")

        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        main_layout.addLayout(pagination_layout)

        # Setze das zentrale Widget
        self.setCentralWidget(central)

        # Signale verbinden
        self.prev_btn.clicked.connect(self.go_previous)
        self.next_btn.clicked.connect(self.go_next)
        self.pages.currentChanged.connect(self.on_page_changed)

        # Initiale Button-Zustände
        self.update_buttons()

    def _label_text(self) -> str:
        """Hilfsfunktion für das Seiten-Label (Seite X / Y)."""
        return f"Seite {self.pages.currentIndex()+1} / {self.pages.count()}"

    def on_page_changed(self, index: int):
        """Wird bei Seitenwechsel gerufen, um Label und Buttons zu aktualisieren."""
        self.page_label.setText(self._label_text())
        self.update_buttons()

    def update_buttons(self):
        """Aktiviert oder deaktiviert die Vor-/Nächste-Buttons je nach aktuellem Index."""
        idx = self.pages.currentIndex()
        cnt = self.pages.count()
        self.prev_btn.setEnabled(idx > 0)
        self.next_btn.setEnabled(idx < cnt - 1)

    def go_previous(self):
        """Wechselt zur vorherigen Seite, falls möglich."""
        idx = self.pages.currentIndex()
        if idx > 0:
            self.pages.setCurrentIndex(idx - 1)

    def go_next(self):
        """Wechselt zur nächsten Seite, falls möglich."""
        idx = self.pages.currentIndex()
        if idx < self.pages.count() - 1:
            self.pages.setCurrentIndex(idx + 1)
