from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QStackedWidget, QMessageBox
)
from PySide6.QtCore import Qt
import qtawesome as qta
from api.auth import SessionManager
from ui import theme


class ManageStudents(QWidget):
    # Inisialisasi halaman mahasiswa kelas.
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._active_course_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Stacked: halaman 0 = daftar matkul, 1 = daftar mahasiswa
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # --- Halaman 0: Pilih matkul ---
        pg0 = QWidget()
        vl0 = QVBoxLayout(pg0)
        lbl0 = QLabel("Pilih Kelas untuk Kelola Mahasiswa")
        lbl0.setStyleSheet("font-size: 22px; font-weight: bold;")
        vl0.addWidget(lbl0)

        self.tbl_courses = QTableWidget()
        self.tbl_courses.setColumnCount(3)
        self.tbl_courses.setHorizontalHeaderLabels(["Kode", "Nama Matkul", "Aksi"])
        self.tbl_courses.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_courses.verticalHeader().setDefaultSectionSize(48)
        self.tbl_courses.setSortingEnabled(True)
        vl0.addWidget(self.tbl_courses)
        self.stack.addWidget(pg0)

        # --- Halaman 1: Daftar mahasiswa ---
        pg1 = QWidget()
        vl1 = QVBoxLayout(pg1)

        header = QHBoxLayout()
        btn_back = QPushButton("  Kembali")
        btn_back.setIcon(qta.icon("fa5s.arrow-left", color="white"))
        btn_back.setFixedWidth(120)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        header.addWidget(btn_back)
        self.lbl_kelas = QLabel("Mahasiswa Kelas")
        self.lbl_kelas.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(self.lbl_kelas)
        header.addStretch()
        vl1.addLayout(header)

        # Tabel mahasiswa (termasuk pending)
        self.tbl_students = QTableWidget()
        self.tbl_students.setColumnCount(5)
        self.tbl_students.setHorizontalHeaderLabels(
            ["NIM", "Nama", "Jurusan", "Status", "Aksi"]
        )
        self.tbl_students.setColumnWidth(0, 100)
        self.tbl_students.setColumnWidth(2, 140)
        self.tbl_students.setColumnWidth(3, 100)
        self.tbl_students.setColumnWidth(4, 180)
        self.tbl_students.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_students.verticalHeader().setDefaultSectionSize(48)
        self.tbl_students.setSortingEnabled(True)
        vl1.addWidget(self.tbl_students)
        self.stack.addWidget(pg1)

    # Muat daftar mata kuliah dosen.
    def load_data(self):
        uid = SessionManager.get_user_id()
        courses = self.db.get_all_courses(dosen_id=uid)
        self.tbl_courses.setSortingEnabled(False)
        self.tbl_courses.setRowCount(len(courses))
        for i, c in enumerate(courses):
            self.tbl_courses.setItem(i, 0, QTableWidgetItem(c["kode_matkul"]))
            self.tbl_courses.setItem(i, 1, QTableWidgetItem(c["nama_matkul"]))

            btn = QPushButton("  Kelola")
            btn.setIcon(qta.icon("fa5s.users-cog", color="white"))
            btn.clicked.connect(
                lambda _, cid=c["id"], cn=c["nama_matkul"]: self._masuk_kelas(cid, cn)
            )
            w = QWidget(); hl = QHBoxLayout(w); hl.setContentsMargins(4, 0, 4, 0); hl.setSpacing(8); hl.setAlignment(Qt.AlignCenter)
            hl.addWidget(btn)
            self.tbl_courses.setCellWidget(i, 2, w)
        self.tbl_courses.setSortingEnabled(True)

    # Masuk ke daftar mahasiswa kelas.
    def _masuk_kelas(self, course_id, course_name):
        self._active_course_id = course_id
        self.lbl_kelas.setText(f"Mahasiswa: {course_name}")
        self._muat_mhs()
        self.stack.setCurrentIndex(1)

    # Muat data mahasiswa aktif pending.
    def _muat_mhs(self):
        students = self.db.get_students_by_course(self._active_course_id, status=None)
        self.tbl_students.setSortingEnabled(False)
        self.tbl_students.setRowCount(len(students))

        for i, s in enumerate(students):
            self.tbl_students.setItem(i, 0, QTableWidgetItem(s["nim"]))
            self.tbl_students.setItem(i, 1, QTableWidgetItem(s["nama_lengkap"]))
            self.tbl_students.setItem(i, 2, QTableWidgetItem(s.get("jurusan", "-")))

            # Item status dengan warna
            status_item = QTableWidgetItem(s.get("status", "").upper())
            if s.get("status") == "pending":
                status_item.setForeground(Qt.darkYellow)
            elif s.get("status") == "active":
                status_item.setForeground(Qt.darkGreen)
            self.tbl_students.setItem(i, 3, status_item)

            # Tombol aksi: terima/tolak untuk pending, hapus untuk active
            w = QWidget(); hl = QHBoxLayout(w); hl.setContentsMargins(4, 0, 4, 0); hl.setSpacing(8); hl.setAlignment(Qt.AlignCenter)
            if s.get("status") == "pending":
                btn_ok = QPushButton("Terima")
                btn_ok.setStyleSheet(f"background:{theme.SUCCESS};color:white;")
                btn_ok.clicked.connect(lambda _, sid=s["id"]: self._terima_mhs(sid))
                btn_no = QPushButton("Tolak")
                btn_no.setStyleSheet(f"background:{theme.DANGER};color:white;")
                btn_no.clicked.connect(lambda _, sid=s["id"]: self._tolak_mhs(sid))
                hl.addWidget(btn_ok); hl.addWidget(btn_no)
            else:
                btn_del = QPushButton()
                btn_del.setIcon(qta.icon("fa5s.trash", color="white"))
                btn_del.setFixedWidth(36)
                btn_del.setStyleSheet(f"background:{theme.DANGER};")
                btn_del.clicked.connect(lambda _, sid=s["id"], nm=s["nama_lengkap"]: self._hapus_mhs(sid, nm))
                hl.addWidget(btn_del)
            self.tbl_students.setCellWidget(i, 4, w)
        self.tbl_students.setSortingEnabled(True)

    # Setujui gabung kelas mahasiswa.
    def _terima_mhs(self, student_id):
        self.db.update_course_student_status(student_id, self._active_course_id, "active")
        self._muat_mhs()

    # Tolak gabung kelas mahasiswa.
    def _tolak_mhs(self, student_id):
        self.db.delete_student_from_course(student_id, self._active_course_id)
        self._muat_mhs()

    # Keluarkan mahasiswa dari kelas.
    def _hapus_mhs(self, student_id, nama):
        ans = QMessageBox.question(
            self, "Konfirmasi", f"Keluarkan '{nama}' dari kelas ini?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            self.db.delete_student_from_course(student_id, self._active_course_id)
            self._muat_mhs()
