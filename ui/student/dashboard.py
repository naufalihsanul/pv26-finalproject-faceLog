from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
import qtawesome as qta
from api.auth import SessionManager
from ui import theme


class StudentDashboard(QWidget):

    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignTop)

        self.lbl_title = QLabel("Beranda Mahasiswa")
        self.lbl_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(self.lbl_title)


        self.lbl_face_status = QLabel()
        self.lbl_face_status.setStyleSheet("font-size: 13px; border-radius: 6px; padding: 6px 10px;")
        layout.addWidget(self.lbl_face_status)


        stat_layout = QHBoxLayout()
        
        self.card_kelas = QFrame()
        self.card_kelas.setStyleSheet(f"background: white; border-radius: 8px; border: 1px solid {theme.BORDER};")
        v1 = QVBoxLayout(self.card_kelas)
        lbl_k = QLabel("Kelas Aktif")
        lbl_k.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-weight: bold;")
        self.val_kelas = QLabel("0")
        self.val_kelas.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {theme.PRIMARY};")
        v1.addWidget(lbl_k); v1.addWidget(self.val_kelas)
        stat_layout.addWidget(self.card_kelas)


        self.card_hadir = QFrame()
        self.card_hadir.setStyleSheet(f"background: white; border-radius: 8px; border: 1px solid {theme.BORDER};")
        v2 = QVBoxLayout(self.card_hadir)
        lbl_h = QLabel("Total Hadir")
        lbl_h.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-weight: bold;")
        self.val_hadir = QLabel("0")
        self.val_hadir.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {theme.SUCCESS};")
        v2.addWidget(lbl_h); v2.addWidget(self.val_hadir)
        stat_layout.addWidget(self.card_hadir)


        self.card_absen = QFrame()
        self.card_absen.setStyleSheet(f"background: white; border-radius: 8px; border: 1px solid {theme.BORDER};")
        v3 = QVBoxLayout(self.card_absen)
        lbl_a = QLabel("Total Alpha / Tidak Hadir")
        lbl_a.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-weight: bold;")
        self.val_absen = QLabel("0")
        self.val_absen.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {theme.DANGER};")
        v3.addWidget(lbl_a); v3.addWidget(self.val_absen)
        stat_layout.addWidget(self.card_absen)

        layout.addLayout(stat_layout)
        layout.addStretch()


    def load_data(self):
        uid = SessionManager.get_user_id()
        if not uid: return

        profile = self.db.get_student_profile(uid)
        has_face = bool(profile and profile.get("fitur_wajah"))

        self.lbl_title.setText(f"Selamat Datang, {SessionManager.get_user_name()}!")


        if has_face:
            self.lbl_face_status.setText("  Wajah sudah terdaftar")
            self.lbl_face_status.setStyleSheet(
                f"background:{theme.SUCCESS}22; color:{theme.SUCCESS}; border-radius:6px; padding:6px 10px;"
            )
        else:
            self.lbl_face_status.setText("  Wajah belum terdaftar — silakan registrasi wajah di menu Registrasi Wajah")
            self.lbl_face_status.setStyleSheet(
                f"background:{theme.DANGER}22; color:{theme.DANGER}; border-radius:6px; padding:6px 10px;"
            )

   
        courses = self.db.get_student_courses(uid)
        active_courses = sum(1 for c in courses if c["status"] == "active")
        self.val_kelas.setText(str(active_courses))

        logs = self.db.get_logs_by_student(uid)
        hadir = sum(1 for l in logs if l["status"].lower() == "hadir")
        tidak_hadir = sum(1 for l in logs if l["status"].lower() in ("tidak hadir", "pending"))

        self.val_hadir.setText(str(hadir))
        self.val_absen.setText(str(tidak_hadir))
