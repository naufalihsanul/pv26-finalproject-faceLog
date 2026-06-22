from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
import qtawesome as qta
from ui import theme


class StatCard(QFrame):
    # Kartu statistik dashboard
    def __init__(self, label: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)

        # Ikon Font Awesome
        lbl_icon = QLabel()
        lbl_icon.setPixmap(
            qta.icon(icon_name, color=theme.PRIMARY).pixmap(28, 28)
        )
        layout.addWidget(lbl_icon)

        # Label judul kartu
        lbl_title = QLabel(label)
        lbl_title.setStyleSheet(
            f"color: {theme.TEXT_MUTED}; font-size: 12px; font-weight: 600;"
        )
        layout.addWidget(lbl_title)

        # Angka nilai statistik
        self.lbl_value = QLabel("0")
        self.lbl_value.setStyleSheet(
            f"color: {theme.PRIMARY}; font-size: 30px; font-weight: 800;"
        )
        layout.addWidget(self.lbl_value)

    def set_value(self, value):
        # Update angka statistik
        self.lbl_value.setText(str(value))
