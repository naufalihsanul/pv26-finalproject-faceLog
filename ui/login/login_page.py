from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal
import qtawesome as qta
from api.auth import SessionManager
from ui import theme


class LoginPage(QWidget):

    login_successful = Signal(str)


    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setWindowTitle("FaceLog — Login")
        self.setFixedSize(420, 500)
        self.bangun_ui()


    def bangun_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 60, 50, 40)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignTop)


        lbl_icon = QLabel()
        lbl_icon.setPixmap(
            qta.icon("fa5s.id-badge", color=theme.PRIMARY).pixmap(48, 48)
        )
        lbl_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_icon)

        lbl_title = QLabel("FaceLog")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(
            f"font-size: 26px; font-weight: 800; color: {theme.PRIMARY};"
        )
        layout.addWidget(lbl_title)

        lbl_sub = QLabel("Sistem Absensi Face Recognition")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(lbl_sub)

        layout.addSpacing(20)


        lbl_u = QLabel("Username / NIM / NIP")
        lbl_u.setStyleSheet("font-weight: 600;")
        layout.addWidget(lbl_u)
        self.inp_user = QLineEdit()
        self.inp_user.setPlaceholderText("Masukkan username...")
        self.inp_user.setMinimumHeight(38)
        layout.addWidget(self.inp_user)

        
        lbl_p = QLabel("Password")
        lbl_p.setStyleSheet("font-weight: 600;")
        layout.addWidget(lbl_p)
        self.inp_pass = QLineEdit()
        self.inp_pass.setPlaceholderText("Masukkan password...")
        self.inp_pass.setEchoMode(QLineEdit.Password)
        self.inp_pass.setMinimumHeight(38)
        self.inp_pass.returnPressed.connect(self.proses_login)
        layout.addWidget(self.inp_pass)


        self.lbl_err = QLabel("")
        self.lbl_err.setStyleSheet(f"color: {theme.DANGER}; font-size: 12px;")
        self.lbl_err.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_err)


        btn_login = QPushButton("  Masuk")
        btn_login.setIcon(qta.icon("fa5s.sign-in-alt", color="white"))
        btn_login.setMinimumHeight(40)
        btn_login.clicked.connect(self.proses_login)
        layout.addWidget(btn_login)


    def proses_login(self):
        username = self.inp_user.text().strip()
        password = self.inp_pass.text()

        if not username or not password:
            self.lbl_err.setText("Username dan password wajib diisi.")
            return

        user = self.db.authenticate_user(username, password)
        if not user:
            self.lbl_err.setText("Username atau password salah.")
            return

        SessionManager.login(user)
        self.login_successful.emit(user["role"])
