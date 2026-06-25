from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
import qtawesome as qta
from api.auth import SessionManager
from ui import theme


class StudentCourses(QWidget):

    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        lbl_title = QLabel("Kelas Saya & Daftar Baru")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(lbl_title)

        lbl_kelas = QLabel("Kelas Saya")
        lbl_kelas.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_kelas)


        self.tbl_kelas = QTableWidget()
        self.tbl_kelas.setColumnCount(4)
        self.tbl_kelas.setHorizontalHeaderLabels(["Kode", "Nama Matkul", "Dosen", "Status"])
        self.tbl_kelas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_kelas.verticalHeader().setDefaultSectionSize(48)
        self.tbl_kelas.setSortingEnabled(True)
        layout.addWidget(self.tbl_kelas)

        lbl_join = QLabel("Daftar Kelas Baru")
        lbl_join.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_join)


        self.tbl_all = QTableWidget()
        self.tbl_all.setColumnCount(4)
        self.tbl_all.setHorizontalHeaderLabels(["Kode", "Nama Matkul", "Dosen", "Aksi"])
        self.tbl_all.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_all.verticalHeader().setDefaultSectionSize(48)
        self.tbl_all.setSortingEnabled(True)
        layout.addWidget(self.tbl_all)


    def load_data(self):
        uid = SessionManager.get_user_id()
        if not uid: return

        profile = self.db.get_student_profile(uid)
        has_face = bool(profile and profile.get("fitur_wajah"))


        enrolled = self.db.get_student_courses(uid)
        enrolled_ids = {c["id"] for c in enrolled}
        self.tbl_kelas.setSortingEnabled(False)
        self.tbl_kelas.setRowCount(len(enrolled))
        for i, c in enumerate(enrolled):
            self.tbl_kelas.setItem(i, 0, QTableWidgetItem(c["kode"]))
            self.tbl_kelas.setItem(i, 1, QTableWidgetItem(c["nama"]))
            self.tbl_kelas.setItem(i, 2, QTableWidgetItem(c["dosen"]))
            status_item = QTableWidgetItem(c["status"].upper())
            if c["status"] == "active":
                status_item.setForeground(Qt.darkGreen)
            elif c["status"] == "pending":
                status_item.setForeground(Qt.darkYellow)
            self.tbl_kelas.setItem(i, 3, status_item)
        self.tbl_kelas.setSortingEnabled(True)


        all_courses = self.db.get_all_courses()
        available = [c for c in all_courses if c["id"] not in enrolled_ids]
        self.tbl_all.setSortingEnabled(False)
        self.tbl_all.setRowCount(len(available))
        for i, c in enumerate(available):
            self.tbl_all.setItem(i, 0, QTableWidgetItem(c["kode_matkul"]))
            self.tbl_all.setItem(i, 1, QTableWidgetItem(c["nama_matkul"]))
            self.tbl_all.setItem(i, 2, QTableWidgetItem(c.get("dosen_name", "-")))

            btn = QPushButton("  Request Bergabung")
            btn.setIcon(qta.icon("fa5s.paper-plane", color="white"))
            btn.setEnabled(has_face)  
            btn.clicked.connect(
                lambda _, cid=c["id"]: self.request_gabung(uid, cid)
            )
            w = QWidget(); hl = QHBoxLayout(w); hl.setContentsMargins(4, 0, 4, 0)
            hl.addWidget(btn)
            self.tbl_all.setCellWidget(i, 3, w)
        self.tbl_all.setSortingEnabled(True)


    def request_gabung(self, student_id, course_id):
        ok, msg = self.db.request_join_course(student_id, course_id)
        if ok:
            QMessageBox.information(self, "Berhasil", msg)
            self.load_data()
        else:
            QMessageBox.warning(self, "Gagal", msg)
