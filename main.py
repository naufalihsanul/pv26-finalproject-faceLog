import sys
import os

# Tambah root ke path agar semua import berjalan
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QFrame, QLabel, QPushButton, QStackedWidget,
    QMenuBar, QStatusBar, QMenu
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
import qtawesome as qta

from api.auth import SessionManager
from database.db_manager import DBManager
from ui.theme import load_stylesheet

# ---- Import semua halaman ----
from ui.login.login_page import LoginPage

from ui.admin.dashboard import AdminDashboard, ManageDosen, AllCourses
from ui.admin.manage_students import GlobalStudents
from ui.admin.history import GlobalHistory

from ui.dosen.dashboard import DosenDashboard, ManageCourses
from ui.dosen.students import ManageStudents
from ui.dosen.scanner import ScannerSession
from ui.dosen.history import DosenHistory

from ui.student.dashboard import StudentDashboard
from ui.student.face_register import FaceRegister
from ui.student.history import StudentHistory
from ui.student.courses import StudentCourses


# ======================================================
#  Main Application Window — shell utama aplikasi
# ======================================================
class MainWindow(QMainWindow):
    def __init__(self, db: DBManager):
        super().__init__()
        self.db = db
        self.setWindowTitle("FaceLog — Sistem Absensi Face Recognition")
        self.setMinimumSize(1100, 700)
        self._build_menu()
        self._build_status_bar()
        self._show_login()

    # ---- Menu Bar ----
    def _build_menu(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        # Menu File
        file_menu = QMenu("File", self)
        act_logout = QAction("Logout", self)
        act_logout.triggered.connect(self._logout)
        act_exit = QAction("Keluar", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_logout)
        file_menu.addSeparator()
        file_menu.addAction(act_exit)

        # Menu Help
        help_menu = QMenu("Help", self)
        act_about = QAction("Tentang Aplikasi", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(help_menu)

    # ---- Status Bar: nama & NIM anggota kelompok ----
    def _build_status_bar(self):
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        # Status bar wajib isi nama & NIM semua anggota (tidak dapat diedit)
        anggota = (
            "Anggota: "
            "Naufal Ihsanul Islam (F1D02310084)  |  "
            "Didy Ardiyanto (F1D02310046)  |  "
            "Apta Mahogra Bhamakerti (F1D022035)"
        )
        status_bar.showMessage(anggota)

    def _show_about(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, "Tentang FaceLog",
            "FaceLog v2.0\nSistem Absensi Berbasis Face Recognition\n\nDibuat untuk tugas Pemrograman Visual."
        )

    # ---- Halaman Login ----
    def _show_login(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        self.login_page = LoginPage(self.db)
        self.login_page.login_successful.connect(self._on_login)
        layout.addWidget(self.login_page)
        self.setCentralWidget(container)

    def _on_login(self, role: str):
        # Bangun main app sesuai role
        self._build_main_app(role)

    # ---- Main App Shell (Sidebar + Content) ----
    def _build_main_app(self, role: str):
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 16, 0, 16)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setAlignment(Qt.AlignTop)

        lbl_app = QLabel("FaceLog")
        lbl_app.setStyleSheet("color: white; font-size: 18px; font-weight: bold; padding: 8px 20px 20px 20px;")
        sidebar_layout.addWidget(lbl_app)

        # Area konten halaman
        self.content = QStackedWidget()
        self.content.setObjectName("mainContent")

        # Tentukan menu & halaman berdasarkan role
        menus, pages = self._get_role_config(role)

        self._menu_buttons = []
        for i, (label, icon_name) in enumerate(menus):
            btn = QPushButton(f"  {label}")
            btn.setIcon(qta.icon(icon_name, color="#adb5bd"))
            btn.setObjectName("sidebarMenu")
            btn.clicked.connect(lambda _, idx=i: self._navigate(idx))
            sidebar_layout.addWidget(btn)
            self._menu_buttons.append(btn)

        for page in pages:
            self.content.addWidget(page)

        self._pages = pages
        sidebar_layout.addStretch()

        # Tombol logout di sidebar bawah
        btn_logout = QPushButton("  Logout")
        btn_logout.setIcon(qta.icon("fa5s.sign-out-alt", color="#adb5bd"))
        btn_logout.setObjectName("sidebarMenu")
        btn_logout.clicked.connect(self._logout)
        sidebar_layout.addWidget(btn_logout)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.content)
        self.setCentralWidget(root)

        # Navigasi ke halaman pertama
        self._navigate(0)

    def _get_role_config(self, role: str):
        # Mapping role -> (menu label, icon, page widget)
        if role == "super_admin":
            menus = [
                ("Dashboard",           "fa5s.tachometer-alt"),
                ("Data Dosen",          "fa5s.chalkboard-teacher"),
                ("Data Mata Kuliah",    "fa5s.book"),
                ("Data Mahasiswa",      "fa5s.user-graduate"),
                ("Riwayat Absensi",     "fa5s.history"),
            ]
            pages = [
                AdminDashboard(self.db),
                ManageDosen(self.db),
                AllCourses(self.db),
                GlobalStudents(self.db),
                GlobalHistory(self.db),
            ]

        elif role == "dosen":
            menus = [
                ("Dashboard",           "fa5s.tachometer-alt"),
                ("Mata Kuliah",         "fa5s.book"),
                ("Mahasiswa Kelas",     "fa5s.users"),
                ("Sesi Absensi",        "fa5s.camera"),
                ("Riwayat Absensi",     "fa5s.history"),
            ]
            pages = [
                DosenDashboard(self.db),
                ManageCourses(self.db),
                ManageStudents(self.db),
                ScannerSession(self.db),
                DosenHistory(self.db),
            ]

        else:  # mahasiswa
            menus = [
                ("Dashboard",           "fa5s.tachometer-alt"),
                ("Kelas Saya",          "fa5s.chalkboard"),
                ("Registrasi Wajah",    "fa5s.camera"),
                ("Riwayat Absensi",     "fa5s.history"),
            ]
            pages = [
                StudentDashboard(self.db),
                StudentCourses(self.db),
                FaceRegister(self.db),
                StudentHistory(self.db),
            ]

        return menus, pages

    def _navigate(self, index: int):
        # Pindah ke halaman, set tombol aktif, refresh data
        self.content.setCurrentIndex(index)

        for i, btn in enumerate(self._menu_buttons):
            btn.setObjectName("sidebarMenuActive" if i == index else "sidebarMenu")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Panggil load_data jika ada
        page = self._pages[index]
        if hasattr(page, "load_data"):
            page.load_data()

    def _logout(self):
        # Hapus sesi dan kembali ke login
        SessionManager.logout()
        self._show_login()


# ======================================================
#  Entry Point
# ======================================================
def main():
    app = QApplication(sys.argv)

    # Muat database
    db = DBManager()

    # Muat & terapkan stylesheet global
    qss_path = os.path.join(os.path.dirname(__file__), "ui", "styles.qss")
    app.setStyleSheet(load_stylesheet(qss_path))

    window = MainWindow(db)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
