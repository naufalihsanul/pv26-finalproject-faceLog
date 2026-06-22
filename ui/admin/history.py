from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QStackedWidget, QMessageBox
)
from PySide6.QtCore import Qt
import qtawesome as qta
from ui.components.history_table import HistoryTable


class GlobalHistory(QWidget):
    # Inisialisasi riwayat absensi global.
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Stacked: halaman 0 = daftar matkul, halaman 1 = riwayat
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # --- Halaman 0: Pilih mata kuliah ---
        pg0 = QWidget()
        vl0 = QVBoxLayout(pg0)

        lbl0 = QLabel("Riwayat Absensi Global — Pilih Mata Kuliah")
        lbl0.setStyleSheet("font-size: 22px; font-weight: bold;")
        vl0.addWidget(lbl0)

        self.tbl_courses = QTableWidget()
        self.tbl_courses.setColumnCount(4)
        self.tbl_courses.setHorizontalHeaderLabels(
            ["Kode", "Nama Matkul", "Dosen", "Aksi"]
        )
        self.tbl_courses.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_courses.verticalHeader().setDefaultSectionSize(48)
        self.tbl_courses.setSortingEnabled(True)
        vl0.addWidget(self.tbl_courses)
        self.stack.addWidget(pg0)

        # --- Halaman 1: Tabel riwayat ---
        pg1 = QWidget()
        vl1 = QVBoxLayout(pg1)

        btn_back = QPushButton("  Kembali")
        btn_back.setIcon(qta.icon("fa5s.arrow-left", color="white"))
        btn_back.setFixedWidth(120)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        vl1.addWidget(btn_back)

        # Komponen tabel riwayat — dipakai bersama
        self.history = HistoryTable(
            headers=["ID Log", "Sesi", "NIM", "Nama", "Status", "Waktu"],
            title="Riwayat Absensi",
            show_date_filter=True
        )
        vl1.addWidget(self.history)
        self.stack.addWidget(pg1)

    # Muat semua matkul.
    def load_data(self):
        self._courses = self.db.get_all_courses()
        self.tampilkan_matkul(self._courses)

    # Tampilkan matkul di tabel.
    def tampilkan_matkul(self, data):
        self.tbl_courses.setSortingEnabled(False)
        self.tbl_courses.setRowCount(len(data))
        for i, c in enumerate(data):
            self.tbl_courses.setItem(i, 0, QTableWidgetItem(c["kode_matkul"]))
            self.tbl_courses.setItem(i, 1, QTableWidgetItem(c["nama_matkul"]))
            self.tbl_courses.setItem(i, 2, QTableWidgetItem(c.get("dosen_name", "-")))

            btn = QPushButton("  Buka Riwayat")
            btn.setIcon(qta.icon("fa5s.folder-open", color="white"))
            btn.clicked.connect(
                lambda _, cn=c["nama_matkul"]: self.buka_riwayat(cn)
            )
            w = QWidget()
            hl = QHBoxLayout(w)
            hl.setContentsMargins(4, 0, 4, 0)
            hl.addWidget(btn)
            self.tbl_courses.setCellWidget(i, 3, w)
        self.tbl_courses.setSortingEnabled(True)

    # Tampilkan riwayat absensi matkul.
    def buka_riwayat(self, course_name):
        logs = self.db.get_all_logs()
        rows = [
            [str(l["id"]), l["nama_sesi"], l["nim"], l["nama_lengkap"],
             l["status"], str(l["waktu_scan"])]
            for l in logs if l["nama_matkul"] == course_name
        ]
        self.history.isi_tabel(rows)
        self.stack.setCurrentIndex(1)
