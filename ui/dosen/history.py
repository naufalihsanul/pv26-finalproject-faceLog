from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QStackedWidget
)
import qtawesome as qta
from api.auth import SessionManager
from ui.components.history_table import HistoryTable


class DosenHistory(QWidget):
    # Inisialisasi riwayat kelas dosen.
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # --- Halaman 0: Daftar matkul ---
        pg0 = QWidget()
        vl0 = QVBoxLayout(pg0)
        lbl = QLabel("Riwayat — Pilih Mata Kuliah")
        lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
        vl0.addWidget(lbl)

        self.tbl_courses = QTableWidget()
        self.tbl_courses.setColumnCount(3)
        self.tbl_courses.setHorizontalHeaderLabels(["Kode", "Nama Matkul", "Aksi"])
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

        # Komponen tabel riwayat bersama (include search, filter, export)
        self.history = HistoryTable(
            headers=["Sesi", "NIM", "Nama", "Status", "Waktu"],
            title="Riwayat Kehadiran Mahasiswa",
            show_date_filter=True
        )
        vl1.addWidget(self.history)
        self.stack.addWidget(pg1)

    # Muat matkul dosen.
    def load_data(self):
        uid = SessionManager.get_user_id()
        courses = self.db.get_all_courses(dosen_id=uid)
        self.tbl_courses.setSortingEnabled(False)
        self.tbl_courses.setRowCount(len(courses))
        for i, c in enumerate(courses):
            self.tbl_courses.setItem(i, 0, QTableWidgetItem(c["kode_matkul"]))
            self.tbl_courses.setItem(i, 1, QTableWidgetItem(c["nama_matkul"]))
            btn = QPushButton("  Buka Riwayat")
            btn.setIcon(qta.icon("fa5s.folder-open", color="white"))
            btn.clicked.connect(
                lambda _, cn=c["nama_matkul"]: self.buka_riwayat(cn)
            )
            w = QWidget(); hl = QHBoxLayout(w); hl.setContentsMargins(4, 0, 4, 0)
            hl.addWidget(btn)
            self.tbl_courses.setCellWidget(i, 2, w)
        self.tbl_courses.setSortingEnabled(True)

    # Tampilkan riwayat absensi matkul.
    def buka_riwayat(self, course_name):
        logs = self.db.get_all_logs()
        rows = [
            [l["nama_sesi"], l["nim"], l["nama_lengkap"], l["status"], str(l["waktu_scan"])]
            for l in logs if l["nama_matkul"] == course_name
        ]
        self.history.isi_tabel(rows)
        self.stack.setCurrentIndex(1)
