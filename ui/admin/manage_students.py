from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDialog,
    QLineEdit, QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
import qtawesome as qta
from ui import theme


class GlobalStudents(QWidget):
    # Inisialisasi antarmuka database mahasiswa.
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)

        lbl = QLabel("Database Mahasiswa")
        lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(lbl)

        # Toolbar: search + tombol tambah
        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Cari NIM atau nama...")
        self.search.textChanged.connect(self.filter_data)
        toolbar.addWidget(self.search)

        btn_add = QPushButton("  Tambah Mahasiswa")
        btn_add.setIcon(qta.icon("fa5s.user-plus", color="white"))
        btn_add.clicked.connect(self.dialog_tambah)
        toolbar.addWidget(btn_add)
        layout.addLayout(toolbar)

        # Tabel daftar mahasiswa
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["NIM", "Nama", "Jurusan", "Aksi"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    # Muat daftar semua mahasiswa.
    def load_data(self):
        self._data = self.db.get_all_students_global()
        self.tampilkan_data(self._data)

    # Filter mahasiswa sesuai pencarian.
    def filter_data(self):
        q = self.search.text().lower()
        self.tampilkan_data([
            s for s in self._data
            if q in s["nim"].lower() or q in s["nama_lengkap"].lower()
        ])

    # Tampilkan data ke dalam tabel.
    def tampilkan_data(self, data):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(data))
        for i, s in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(s["nim"]))
            self.table.setItem(i, 1, QTableWidgetItem(s["nama_lengkap"]))
            self.table.setItem(i, 2, QTableWidgetItem(s.get("jurusan", "-")))

            # Widget aksi per baris
            w = QWidget()
            hl = QHBoxLayout(w)
            hl.setContentsMargins(4, 0, 4, 0)
            hl.setSpacing(8)
            hl.setAlignment(Qt.AlignCenter)

            btn_edit = QPushButton()
            btn_edit.setIcon(qta.icon("fa5s.edit", color="white"))
            btn_edit.setFixedWidth(36)
            btn_edit.clicked.connect(
                lambda _, sid=s["id"], curr=s: self.dialog_edit(sid, curr)
            )

            btn_del = QPushButton()
            btn_del.setIcon(qta.icon("fa5s.trash", color="white"))
            btn_del.setFixedWidth(36)
            btn_del.setStyleSheet(f"background-color: {theme.DANGER};")
            btn_del.clicked.connect(
                lambda _, sid=s["id"], nm=s["nama_lengkap"]: self.hapus_mahasiswa(sid, nm)
            )

            hl.addWidget(btn_edit)
            hl.addWidget(btn_del)
            self.table.setCellWidget(i, 3, w)
        self.table.setSortingEnabled(True)

    # Tampilkan form tambah mahasiswa.
    def dialog_tambah(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Tambah Mahasiswa")
        dlg.setFixedSize(360, 320)
        vl = QVBoxLayout(dlg)

        inp_nama = QLineEdit(); inp_nama.setPlaceholderText("Nama lengkap")
        inp_jur  = QLineEdit(); inp_jur.setPlaceholderText("Jurusan")
        inp_pass = QLineEdit(); inp_pass.setPlaceholderText("Password")
        inp_pass.setEchoMode(QLineEdit.Password)

        vl.addWidget(QLabel("Nama:"));    vl.addWidget(inp_nama)
        vl.addWidget(QLabel("Jurusan:")); vl.addWidget(inp_jur)
        vl.addWidget(QLabel("Password:")); vl.addWidget(inp_pass)

        btn = QPushButton("Simpan")
        btn.clicked.connect(
            lambda: self.simpan_mahasiswa(inp_nama.text(), inp_pass.text(), inp_jur.text(), dlg)
        )
        vl.addWidget(btn)
        dlg.exec()

    # Validasi dan simpan mahasiswa.
    def simpan_mahasiswa(self, nama, pwd, jur, dlg):
        if not nama or not pwd:
            QMessageBox.warning(self, "Peringatan", "Nama dan password wajib diisi!")
            return
        ok, msg = self.db.create_student_account(nama, pwd, jur)
        if ok:
            QMessageBox.information(self, "Sukses", msg)
            dlg.accept()
            self.load_data()
        else:
            QMessageBox.warning(self, "Gagal", msg)

    # Tampilkan form edit mahasiswa.
    def dialog_edit(self, sid, curr):
        dlg = QDialog(self)
        dlg.setWindowTitle("Edit Mahasiswa")
        dlg.setFixedSize(360, 400)
        vl = QVBoxLayout(dlg)

        inp_nim  = QLineEdit(curr["nim"])
        inp_nama = QLineEdit(curr["nama_lengkap"])
        inp_jur  = QLineEdit(curr.get("jurusan", ""))
        inp_pass = QLineEdit(); inp_pass.setPlaceholderText("Password baru (opsional)")
        inp_pass.setEchoMode(QLineEdit.Password)

        vl.addWidget(QLabel("NIM:"));    vl.addWidget(inp_nim)
        vl.addWidget(QLabel("Nama:"));   vl.addWidget(inp_nama)
        vl.addWidget(QLabel("Jurusan:")); vl.addWidget(inp_jur)
        vl.addWidget(QLabel("Password:")); vl.addWidget(inp_pass)

        btn = QPushButton("Simpan")
        btn.clicked.connect(
            lambda: self.update_mahasiswa(sid, inp_nim.text(), inp_nama.text(),
                                 inp_jur.text(), inp_pass.text() or None, dlg)
        )
        vl.addWidget(btn)
        dlg.exec()

    # Perbarui data akun mahasiswa.
    def update_mahasiswa(self, sid, nim, nama, jur, pwd, dlg):
        if not nim or not nama:
            QMessageBox.warning(self, "Peringatan", "NIM dan nama wajib diisi!")
            return
        ok, msg = self.db.update_student(sid, nim, nama, jur, pwd)
        if ok:
            dlg.accept()
            self.load_data()
        else:
            QMessageBox.warning(self, "Gagal", msg)

    # Hapus data mahasiswa permanen.
    def hapus_mahasiswa(self, sid, nama):
        ans = QMessageBox.question(
            self, "Konfirmasi Hapus",
            f"Hapus mahasiswa '{nama}'?\nSemua data absensinya akan hilang.",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            self.db.delete_student(sid)
            self.load_data()
