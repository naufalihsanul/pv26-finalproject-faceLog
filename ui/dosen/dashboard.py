from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDialog,
    QLineEdit, QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
import qtawesome as qta
from api.auth import SessionManager
from ui.components.stat_card import StatCard
from ui import theme


class DosenDashboard(QWidget):
    # Inisialisasi halaman statistik dosen.
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        self.lbl_title = QLabel("Dashboard Dosen")
        self.lbl_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(self.lbl_title)

        cards = QHBoxLayout()
        self.card_matkul  = StatCard("Matkul Saya",     "fa5s.book")
        self.card_mhs     = StatCard("Mahasiswa Aktif",  "fa5s.users")
        self.card_sesi    = StatCard("Sesi Hari Ini",    "fa5s.calendar-check")
        for c in [self.card_matkul, self.card_mhs, self.card_sesi]:
            cards.addWidget(c)
        layout.addLayout(cards)
        layout.addStretch()

    # Muat data statistik dosen.
    def load_data(self):
        uid = SessionManager.get_user_id()
        if not uid: return
        self.lbl_title.setText(f"Dashboard — {SessionManager.get_user_name()}")
        stats = self.db.get_dosen_stats(uid)
        self.card_matkul.set_value(stats["course_count"])
        self.card_mhs.set_value(stats["student_count"])
        self.card_sesi.set_value(stats["sessions_today"])


# ---------- Kelola Mata Kuliah ----------

class ManageCourses(QWidget):
    # Inisialisasi antarmuka kelola matkul.
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)

        lbl = QLabel("Mata Kuliah Saya")
        lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(lbl)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Cari nama matkul...")
        self.search.textChanged.connect(self.filter_data)
        toolbar.addWidget(self.search)

        btn_add = QPushButton("  Buat Matkul")
        btn_add.setIcon(qta.icon("fa5s.plus", color="white"))
        btn_add.clicked.connect(self.dialog_tambah)
        toolbar.addWidget(btn_add)
        layout.addLayout(toolbar)

        # Tabel matkul
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Kode", "Nama Matkul", "Semester", "Tahun Ajaran", "Aksi"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    # Muat daftar matkul dosen.
    def load_data(self):
        uid = SessionManager.get_user_id()
        if not uid: return
        self._data = self.db.get_all_courses(dosen_id=uid)
        self.tampilkan_data(self._data)

    # Filter matkul sesuai pencarian.
    def filter_data(self):
        q = self.search.text().lower()
        self.tampilkan_data([c for c in self._data if q in c["nama_matkul"].lower()])

    # Tampilkan matkul di tabel.
    def tampilkan_data(self, data):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(data))
        for i, c in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(c["kode_matkul"]))
            self.table.setItem(i, 1, QTableWidgetItem(c["nama_matkul"]))
            self.table.setItem(i, 2, QTableWidgetItem(c["semester"]))
            self.table.setItem(i, 3, QTableWidgetItem(c["tahun_ajaran"]))

            w = QWidget()
            hl = QHBoxLayout(w); hl.setContentsMargins(4, 0, 4, 0)

            btn_e = QPushButton(); btn_e.setIcon(qta.icon("fa5s.edit", color="white"))
            btn_e.setFixedWidth(36)
            btn_e.clicked.connect(lambda _, cid=c["id"], curr=c: self.dialog_edit(cid, curr))

            btn_d = QPushButton(); btn_d.setIcon(qta.icon("fa5s.trash", color="white"))
            btn_d.setFixedWidth(36)
            btn_d.setStyleSheet(f"background:{theme.DANGER};")
            btn_d.clicked.connect(lambda _, cid=c["id"], cn=c["nama_matkul"]: self.hapus_matkul(cid, cn))

            hl.addWidget(btn_e); hl.addWidget(btn_d)
            self.table.setCellWidget(i, 4, w)
        self.table.setSortingEnabled(True)

    # Form tambah mata kuliah.
    def dialog_tambah(self):
        dlg = QDialog(self); dlg.setWindowTitle("Buat Matkul"); dlg.setFixedSize(360, 300)
        vl = QVBoxLayout(dlg)
        inp_kode = QLineEdit(); inp_kode.setPlaceholderText("Kode (mis. IF101)")
        inp_nama = QLineEdit(); inp_nama.setPlaceholderText("Nama mata kuliah")
        inp_sem  = QLineEdit(); inp_sem.setPlaceholderText("Semester (mis. Ganjil 2025)")
        inp_thn  = QLineEdit(); inp_thn.setPlaceholderText("Tahun ajaran (mis. 2025/2026)")
        for w in [inp_kode, inp_nama, inp_sem, inp_thn]: vl.addWidget(w)
        btn = QPushButton("Simpan")
        btn.clicked.connect(lambda: self.simpan_matkul(inp_kode.text(), inp_nama.text(),
                                                  inp_sem.text(), inp_thn.text(), dlg))
        vl.addWidget(btn); dlg.exec()

    # Validasi dan simpan matkul.
    def simpan_matkul(self, kode, nama, sem, thn, dlg):
        if not kode or not nama:
            QMessageBox.warning(self, "Peringatan", "Kode dan nama wajib diisi!"); return
        ok, msg = self.db.add_course(kode, nama, SessionManager.get_user_id(), sem, thn)
        if ok: dlg.accept(); self.load_data()
        else: QMessageBox.warning(self, "Gagal", msg)

    # Form edit mata kuliah.
    def dialog_edit(self, cid, c):
        dlg = QDialog(self); dlg.setWindowTitle("Edit Matkul"); dlg.setFixedSize(360, 300)
        vl = QVBoxLayout(dlg)
        inp_kode = QLineEdit(c["kode_matkul"])
        inp_nama = QLineEdit(c["nama_matkul"])
        inp_sem  = QLineEdit(c["semester"])
        inp_thn  = QLineEdit(c["tahun_ajaran"])
        for w in [inp_kode, inp_nama, inp_sem, inp_thn]: vl.addWidget(w)
        btn = QPushButton("Simpan")
        btn.clicked.connect(lambda: self.update_matkul(cid, inp_kode.text(), inp_nama.text(),
                                                  inp_sem.text(), inp_thn.text(), dlg))
        vl.addWidget(btn); dlg.exec()

    # Perbarui data mata kuliah.
    def update_matkul(self, cid, kode, nama, sem, thn, dlg):
        if not kode or not nama:
            QMessageBox.warning(self, "Peringatan", "Kode dan nama wajib diisi!"); return
        ok, msg = self.db.update_course(cid, kode, nama, sem, thn)
        if ok: dlg.accept(); self.load_data()
        else: QMessageBox.warning(self, "Gagal", msg)

    # Hapus matkul secara permanen.
    def hapus_matkul(self, cid, nama):
        ans = QMessageBox.question(self, "Konfirmasi Hapus",
                                   f"Hapus matkul '{nama}'?", QMessageBox.Yes | QMessageBox.No)
        if ans == QMessageBox.Yes:
            self.db.delete_course(cid); self.load_data()
