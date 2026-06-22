from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDialog,
    QLineEdit, QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
import qtawesome as qta
from ui.components.stat_card import StatCard
from ui import theme


class AdminDashboard(QWidget):
    # Inisialisasi halaman statistik admin.
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        lbl = QLabel("Dashboard Admin")
        lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(lbl)

        # Baris kartu statistik
        cards = QHBoxLayout()
        self.card_dosen   = StatCard("Total Dosen",     "fa5s.chalkboard-teacher")
        self.card_mhs     = StatCard("Total Mahasiswa", "fa5s.user-graduate")
        self.card_matkul  = StatCard("Total Matkul",    "fa5s.book")
        self.card_sesi    = StatCard("Sesi Hari Ini",   "fa5s.calendar-check")
        for c in [self.card_dosen, self.card_mhs, self.card_matkul, self.card_sesi]:
            cards.addWidget(c)
        layout.addLayout(cards)
        layout.addStretch()

    # Muat data statistik global.
    def load_data(self):
        stats = self.db.get_global_stats()
        self.card_dosen.set_value(stats["dosen_count"])
        self.card_mhs.set_value(stats["student_count"])
        self.card_matkul.set_value(stats["course_count"])
        self.card_sesi.set_value(stats["sessions_today"])


# ---------- Halaman Kelola Dosen ----------

class ManageDosen(QWidget):
    # Inisialisasi antarmuka kelola dosen.
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)

        lbl = QLabel("Kelola Dosen")
        lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(lbl)

        # Toolbar: search + tombol tambah
        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Cari nama dosen...")
        self.search.textChanged.connect(self.filter_data)
        toolbar.addWidget(self.search)

        btn_add = QPushButton("  Tambah Dosen")
        btn_add.setIcon(qta.icon("fa5s.user-plus", color="white"))
        btn_add.clicked.connect(self.dialog_tambah)
        toolbar.addWidget(btn_add)
        layout.addLayout(toolbar)

        # Tabel daftar dosen
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["NIP", "Nama", "Aksi"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    # Muat daftar semua dosen.
    def load_data(self):
        self._data = self.db.get_all_dosen()
        self.tampilkan_data(self._data)

    # Saring dosen berdasarkan nama.
    def filter_data(self):
        q = self.search.text().lower()
        self.tampilkan_data([d for d in self._data if q in d["nama_lengkap"].lower()])

    # Tampilkan dosen di tabel.
    def tampilkan_data(self, data):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(data))
        for i, d in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(d["nama_pengguna"]))
            self.table.setItem(i, 1, QTableWidgetItem(d["nama_lengkap"]))

            # Widget aksi: edit & hapus
            w = QWidget()
            hl = QHBoxLayout(w)
            hl.setContentsMargins(4, 0, 4, 0)
            hl.setSpacing(8)
            hl.setAlignment(Qt.AlignCenter)

            btn_edit = QPushButton()
            btn_edit.setIcon(qta.icon("fa5s.edit", color="white"))
            btn_edit.setToolTip("Edit dosen")
            btn_edit.setFixedWidth(36)
            btn_edit.clicked.connect(lambda _, did=d["id"], dn=d["nama_lengkap"]: self.dialog_edit(did, dn))

            btn_del = QPushButton()
            btn_del.setIcon(qta.icon("fa5s.trash", color="white"))
            btn_del.setToolTip("Hapus dosen")
            btn_del.setFixedWidth(36)
            btn_del.setStyleSheet(f"background-color: {theme.DANGER};")
            btn_del.clicked.connect(lambda _, did=d["id"], dn=d["nama_lengkap"]: self.hapus_dosen(did, dn))

            hl.addWidget(btn_edit)
            hl.addWidget(btn_del)
            self.table.setCellWidget(i, 2, w)
        self.table.setSortingEnabled(True)

    # Tampilkan form tambah dosen.
    def dialog_tambah(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Tambah Dosen")
        dlg.setFixedSize(360, 240)
        vl = QVBoxLayout(dlg)

        inp_nama = QLineEdit(); inp_nama.setPlaceholderText("Nama lengkap dosen")
        inp_pass = QLineEdit(); inp_pass.setPlaceholderText("Password")
        inp_pass.setEchoMode(QLineEdit.Password)
        vl.addWidget(QLabel("Nama:")); vl.addWidget(inp_nama)
        vl.addWidget(QLabel("Password:")); vl.addWidget(inp_pass)

        btn_save = QPushButton("Simpan")
        btn_save.clicked.connect(lambda: self.simpan_dosen(inp_nama.text(), inp_pass.text(), dlg))
        vl.addWidget(btn_save)
        dlg.exec()

    # Validasi dan simpan dosen.
    def simpan_dosen(self, nama, pwd, dlg):
        if not nama or not pwd:
            QMessageBox.warning(self, "Peringatan", "Nama dan password wajib diisi!")
            return
        ok, msg = self.db.add_dosen(pwd, nama)
        if ok:
            QMessageBox.information(self, "Sukses", msg)
            dlg.accept()
            self.load_data()
        else:
            QMessageBox.warning(self, "Gagal", msg)

    # Tampilkan form edit dosen.
    def dialog_edit(self, did, nama):
        dlg = QDialog(self)
        dlg.setWindowTitle("Edit Dosen")
        dlg.setFixedSize(360, 240)
        vl = QVBoxLayout(dlg)

        inp_nama = QLineEdit(nama)
        inp_pass = QLineEdit(); inp_pass.setPlaceholderText("Password baru (opsional)")
        inp_pass.setEchoMode(QLineEdit.Password)
        vl.addWidget(QLabel("Nama:")); vl.addWidget(inp_nama)
        vl.addWidget(QLabel("Password:")); vl.addWidget(inp_pass)

        btn_save = QPushButton("Simpan")
        btn_save.clicked.connect(
            lambda: self.update_dosen(did, inp_nama.text(), inp_pass.text() or None, dlg)
        )
        vl.addWidget(btn_save)
        dlg.exec()

    # Perbarui data akun dosen.
    def update_dosen(self, did, nama, pwd, dlg):
        if not nama:
            QMessageBox.warning(self, "Peringatan", "Nama tidak boleh kosong!")
            return
        self.db.update_dosen(did, nama, pwd)
        dlg.accept()
        self.load_data()

    # Hapus data dosen permanen.
    def hapus_dosen(self, did, nama):
        ans = QMessageBox.question(
            self, "Konfirmasi Hapus",
            f"Hapus dosen '{nama}'? Semua matkul-nya ikut terhapus.",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            self.db.delete_user(did)
            self.load_data()


# ---------- Halaman Semua Matkul ----------

class AllCourses(QWidget):
    # Inisialisasi daftar semua matkul.
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)

        lbl = QLabel("Semua Mata Kuliah")
        lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(lbl)

        # Search bar
        self.search = QLineEdit()
        self.search.setPlaceholderText("Cari nama matkul atau dosen...")
        self.search.textChanged.connect(self.filter_data)
        layout.addWidget(self.search)

        # Tabel matkul
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Kode", "Nama Matkul", "Dosen", "Semester", "Tahun Ajaran"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    # Muat daftar mata kuliah.
    def load_data(self):
        self._data = self.db.get_all_courses()
        self.tampilkan_data(self._data)

    # Saring matkul berdasarkan nama.
    def filter_data(self):
        q = self.search.text().lower()
        self.tampilkan_data([
            c for c in self._data
            if q in c["nama_matkul"].lower() or q in c.get("dosen_name", "").lower()
        ])

    # Tampilkan matkul di tabel.
    def tampilkan_data(self, data):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(data))
        for i, c in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(c["kode_matkul"]))
            self.table.setItem(i, 1, QTableWidgetItem(c["nama_matkul"]))
            self.table.setItem(i, 2, QTableWidgetItem(c.get("dosen_name", "-")))
            self.table.setItem(i, 3, QTableWidgetItem(c["semester"]))
            self.table.setItem(i, 4, QTableWidgetItem(c["tahun_ajaran"]))
        self.table.setSortingEnabled(True)
