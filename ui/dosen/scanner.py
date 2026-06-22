import time
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDialog,
    QLineEdit, QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
import qtawesome as qta
from api.auth import SessionManager
from api.face_engine import FaceEngine
from ui import theme


class ScannerSession(QWidget):
    # Inisialisasi halaman scanner absensi.
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.engine = FaceEngine()
        self._session_id = None
        self._course_id = None
        self._registered = []
        self._last_id = None
        self._last_time = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Stacked: 0=matkul, 1=daftar sesi, 2=scanner
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        self.halaman_matkul()
        self.halaman_sesi()
        self.halaman_scanner()

        # Timer kamera & pencocokan wajah
        self._cam = None
        self._timer_cam = QTimer()
        self._timer_cam.timeout.connect(self.update_frame)
        self._timer_match = QTimer()
        self._timer_match.setInterval(2000)  # Cocokkan setiap 2 detik
        self._timer_match.timeout.connect(self.cocokkan_wajah)

    # Buat UI pilih kelas.
    def halaman_matkul(self):
        pg = QWidget(); vl = QVBoxLayout(pg)
        lbl = QLabel("Pilih Kelas untuk Sesi Absensi")
        lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
        vl.addWidget(lbl)
        self.tbl_courses = QTableWidget()
        self.tbl_courses.setColumnCount(3)
        self.tbl_courses.setHorizontalHeaderLabels(["Kode", "Nama Matkul", "Aksi"])
        self.tbl_courses.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_courses.verticalHeader().setDefaultSectionSize(48)
        self.tbl_courses.setSortingEnabled(True)
        vl.addWidget(self.tbl_courses)
        self.stack.addWidget(pg)

    # Buat UI daftar pertemuan.
    def halaman_sesi(self):
        pg = QWidget(); vl = QVBoxLayout(pg)

        header = QHBoxLayout()
        btn_back = QPushButton("  Kembali")
        btn_back.setIcon(qta.icon("fa5s.arrow-left", color="white"))
        btn_back.setFixedWidth(120)
        btn_back.clicked.connect(lambda: (self.stack.setCurrentIndex(0), self.load_data()))
        header.addWidget(btn_back)
        self.lbl_sesi_title = QLabel("Daftar Pertemuan")
        self.lbl_sesi_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(self.lbl_sesi_title); header.addStretch()
        vl.addLayout(header)

        btn_add_session = QPushButton("  Tambah Pertemuan")
        btn_add_session.setIcon(qta.icon("fa5s.plus", color="white"))
        btn_add_session.setFixedWidth(180)
        btn_add_session.clicked.connect(self.dialog_tambah)
        vl.addWidget(btn_add_session)

        self.tbl_sessions = QTableWidget()
        self.tbl_sessions.setColumnCount(4)
        self.tbl_sessions.setHorizontalHeaderLabels(
            ["ID", "Nama Pertemuan", "Status", "Aksi"]
        )
        self.tbl_sessions.setColumnWidth(0, 60)
        self.tbl_sessions.setColumnWidth(2, 100)
        self.tbl_sessions.setColumnWidth(3, 240)
        self.tbl_sessions.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_sessions.verticalHeader().setDefaultSectionSize(48)
        self.tbl_sessions.setSortingEnabled(True)
        vl.addWidget(self.tbl_sessions)
        self.stack.addWidget(pg)

    # Buat UI scanner kamera.
    def halaman_scanner(self):
        pg = QWidget(); vl = QVBoxLayout(pg)

        header = QHBoxLayout()
        btn_stop = QPushButton("  Tutup & Akhiri Sesi")
        btn_stop.setIcon(qta.icon("fa5s.stop-circle", color="white"))
        btn_stop.setStyleSheet(f"background:{theme.DANGER};color:white;")
        btn_stop.clicked.connect(self.tutup_sesi)
        header.addWidget(btn_stop); header.addStretch()
        vl.addLayout(header)

        # Label preview kamera
        self.cam_label = QLabel()
        self.cam_label.setFixedSize(640, 480)
        self.cam_label.setStyleSheet("background:black; border-radius:8px;")
        self.cam_label.setAlignment(Qt.AlignCenter)
        vl.addWidget(self.cam_label, alignment=Qt.AlignCenter)

        # Status pencocokan wajah
        self.lbl_scan_status = QLabel("Arahkan wajah ke kamera...")
        self.lbl_scan_status.setAlignment(Qt.AlignCenter)
        self.lbl_scan_status.setStyleSheet("font-size: 16px; font-weight: bold;")
        vl.addWidget(self.lbl_scan_status)
        self.stack.addWidget(pg)

    # Muat daftar matkul dosen.
    def load_data(self):
        uid = SessionManager.get_user_id()
        courses = self.db.get_all_courses(dosen_id=uid)
        self.tbl_courses.setSortingEnabled(False)
        self.tbl_courses.setRowCount(len(courses))
        for i, c in enumerate(courses):
            self.tbl_courses.setItem(i, 0, QTableWidgetItem(c["kode_matkul"]))
            self.tbl_courses.setItem(i, 1, QTableWidgetItem(c["nama_matkul"]))
            btn = QPushButton("  Kelola Pertemuan")
            btn.setIcon(qta.icon("fa5s.calendar-alt", color="white"))
            btn.clicked.connect(
                lambda _, cid=c["id"], cn=c["nama_matkul"]: self.masuk_kelas(cid, cn)
            )
            w = QWidget(); hl = QHBoxLayout(w); hl.setContentsMargins(4, 0, 4, 0)
            hl.addWidget(btn)
            self.tbl_courses.setCellWidget(i, 2, w)
        self.tbl_courses.setSortingEnabled(True)

    # Buka halaman sesi kelas.
    def masuk_kelas(self, course_id, course_name):
        self._course_id = course_id
        self.lbl_sesi_title.setText(f"Pertemuan: {course_name}")
        self.muat_sesi()
        self.stack.setCurrentIndex(1)

    # Muat daftar pertemuan kelas.
    def muat_sesi(self):
        sessions = self.db.get_sessions_by_course(self._course_id)
        self.tbl_sessions.setSortingEnabled(False)
        self.tbl_sessions.setRowCount(len(sessions))
        for i, s in enumerate(sessions):
            self.tbl_sessions.setItem(i, 0, QTableWidgetItem(str(s["id"])))
            self.tbl_sessions.setItem(i, 1, QTableWidgetItem(s["nama_sesi"]))
            status_text = "Terbuka" if s["status"] == "open" else "Tertutup"
            self.tbl_sessions.setItem(i, 2, QTableWidgetItem(status_text))

            w = QWidget(); hl = QHBoxLayout(w); hl.setContentsMargins(4, 0, 4, 0); hl.setSpacing(8); hl.setAlignment(Qt.AlignCenter)
            if s["status"] == "open":
                # Tombol nyalakan scanner
                btn_scan = QPushButton("  Scan Absen")
                btn_scan.setIcon(qta.icon("fa5s.camera", color="white"))
                btn_scan.setStyleSheet(f"background:{theme.SUCCESS};color:white;")
                btn_scan.clicked.connect(
                    lambda _, sid=s["id"], sn=s["nama_sesi"]: self.mulai_scanner(sid, sn)
                )
                hl.addWidget(btn_scan)

            btn_edit = QPushButton(); btn_edit.setIcon(qta.icon("fa5s.edit", color="white"))
            btn_edit.setFixedWidth(36)
            btn_edit.clicked.connect(
                lambda _, sid=s["id"], sn=s["nama_sesi"], st=s["status"]: self.dialog_edit(sid, sn, st)
            )
            btn_del = QPushButton(); btn_del.setIcon(qta.icon("fa5s.trash", color="white"))
            btn_del.setFixedWidth(36)
            btn_del.setStyleSheet(f"background:{theme.DANGER};")
            btn_del.clicked.connect(lambda _, sid=s["id"], sn=s["nama_sesi"]: self.hapus_sesi(sid, sn))
            hl.addWidget(btn_edit); hl.addWidget(btn_del)
            self.tbl_sessions.setCellWidget(i, 3, w)
        self.tbl_sessions.setSortingEnabled(True)

    # Tampilkan form tambah pertemuan.
    def dialog_tambah(self):
        dlg = QDialog(self); dlg.setWindowTitle("Tambah Pertemuan"); dlg.setFixedSize(360, 180)
        vl = QVBoxLayout(dlg)
        inp = QLineEdit(); inp.setPlaceholderText("Nama pertemuan (mis. Pertemuan 1)")
        vl.addWidget(inp)
        btn = QPushButton("Simpan")
        btn.clicked.connect(lambda: self.simpan_sesi(inp.text(), dlg))
        vl.addWidget(btn); dlg.exec()

    # Simpan data pertemuan baru.
    def simpan_sesi(self, nama, dlg):
        if not nama:
            QMessageBox.warning(self, "Peringatan", "Nama pertemuan wajib diisi!"); return
        self.db.open_session(self._course_id, nama)
        dlg.accept(); self.muat_sesi()

    # Tampilkan form edit pertemuan.
    def dialog_edit(self, sid, sname, status):
        dlg = QDialog(self); dlg.setWindowTitle("Edit Pertemuan"); dlg.setFixedSize(360, 220)
        vl = QVBoxLayout(dlg)
        inp = QLineEdit(sname)
        vl.addWidget(QLabel("Nama:")); vl.addWidget(inp)
        btn = QPushButton("Simpan")
        btn.clicked.connect(lambda: (self.db.update_session(sid, inp.text()), dlg.accept(), self.muat_sesi()))
        vl.addWidget(btn)
        if status == "closed":
            btn_open = QPushButton("Buka Kembali")
            btn_open.setStyleSheet(f"background:{theme.SUCCESS};color:white;")
            btn_open.clicked.connect(lambda: (self.db.reopen_session(sid), dlg.accept(), self.muat_sesi()))
            vl.addWidget(btn_open)
        dlg.exec()

    # Hapus data pertemuan kelas.
    def hapus_sesi(self, sid, sname):
        ans = QMessageBox.question(self, "Hapus", f"Hapus pertemuan '{sname}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ans == QMessageBox.Yes:
            self.db.delete_session(sid); self.muat_sesi()

    # Nyalakan scanner absensi wajah.
    def mulai_scanner(self, session_id, session_name):
        self._session_id = session_id
        self._registered = self.db.get_students_by_course(self._course_id, status="active")
        self._cam = cv2.VideoCapture(0)
        self._timer_cam.start(30)
        self._timer_match.start()
        self.stack.setCurrentIndex(2)

    # Matikan scanner tutup sesi.
    def tutup_sesi(self):
        self._timer_cam.stop(); self._timer_match.stop()
        if self._cam: self._cam.release()
        self.cam_label.clear()
        if self._session_id:
            self.db.close_session(self._session_id)
        self._session_id = None
        self.stack.setCurrentIndex(1); self.muat_sesi()

    # Perbarui frame dari kamera.
    def update_frame(self):
        if not self._cam: return
        ret, frame = self._cam.read()
        if not ret: return
        frame = cv2.flip(frame, 1)
        self._frame = frame.copy()
        # Gambar kotak deteksi wajah
        for (x, y, w, h) in self.engine.detect_faces(frame):
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 200, 100), 2)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        self.cam_label.setPixmap(
            QPixmap.fromImage(QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888))
        )

    # Cocokkan wajah dengan mahasiswa.
    def cocokkan_wajah(self):
        if not hasattr(self, "_frame"): return
        faces = self.engine.detect_faces(self._frame)
        if not len(faces): return
        x, y, w, h = faces[0]
        emb = self.engine.get_embedding(self._frame, x, y, w, h)
        student, score = self.engine.match_face(emb, self._registered)
        now = time.time()
        if student:
            if self._last_id != student["id"] or (now - self._last_time) > 10:
                self.db.log_attendance(self._session_id, student["id"], "Hadir")
                self.lbl_scan_status.setText(f"Hadir: {student['nama_lengkap']} ({student['nim']})")
                self.lbl_scan_status.setStyleSheet(f"font-size:16px;font-weight:bold;color:{theme.SUCCESS};")
                self._last_id = student["id"]; self._last_time = now
        else:
            if self._last_id != -1 or (now - self._last_time) > 10:
                self.lbl_scan_status.setText("Wajah tidak dikenali")
                self.lbl_scan_status.setStyleSheet(f"font-size:16px;font-weight:bold;color:{theme.DANGER};")
                self._last_id = -1; self._last_time = now
