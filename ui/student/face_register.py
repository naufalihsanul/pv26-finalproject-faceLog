import os
import cv2
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
import qtawesome as qta
from api.auth import SessionManager
from api.face_engine import FaceEngine
from ui import theme


class FaceRegister(QWidget):

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.engine = FaceEngine()
        self._cam = None
        self._frame = None

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(12)

        lbl = QLabel("Registrasi Wajah")
        lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(lbl)

        self.lbl_status = QLabel("Klik 'Mulai Kamera' untuk memulai registrasi.")
        self.lbl_status.setStyleSheet(f"color:{theme.TEXT_MUTED}; font-size:13px;")
        layout.addWidget(self.lbl_status)


        self.cam_label = QLabel()
        self.cam_label.setFixedSize(480, 360)
        self.cam_label.setStyleSheet("background:black; border-radius:8px;")
        self.cam_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.cam_label, alignment=Qt.AlignCenter)


        btn_row = QVBoxLayout()
        self.btn_cam = QPushButton("  Mulai Kamera")
        self.btn_cam.setIcon(qta.icon("fa5s.camera", color="white"))
        self.btn_cam.clicked.connect(self.mulai_kamera)
        btn_row.addWidget(self.btn_cam)

        self.btn_capture = QPushButton("  Ambil & Simpan Wajah")
        self.btn_capture.setIcon(qta.icon("fa5s.check", color="white"))
        self.btn_capture.setStyleSheet(f"background:{theme.SUCCESS};color:white;")
        self.btn_capture.setEnabled(False)
        self.btn_capture.clicked.connect(self.simpan_wajah)
        btn_row.addWidget(self.btn_capture)
        layout.addLayout(btn_row)


        self._timer = QTimer()
        self._timer.timeout.connect(self.update_frame)

 
    def load_data(self):
        uid = SessionManager.get_user_id()
        profile = self.db.get_student_profile(uid)
        if profile and profile.get("fitur_wajah"):
            self.lbl_status.setText("Wajah sudah terdaftar. Anda bisa registrasi ulang jika perlu.")
            self.lbl_status.setStyleSheet(f"color:{theme.SUCCESS}; font-size:13px;")
        else:
            self.lbl_status.setText("Wajah belum terdaftar. Klik 'Mulai Kamera' untuk registrasi.")
            self.lbl_status.setStyleSheet(f"color:{theme.DANGER}; font-size:13px;")


    def mulai_kamera(self):
        self._cam = cv2.VideoCapture(0)
        self._timer.start(33)
        self.btn_cam.setEnabled(False)
        self.btn_capture.setEnabled(True)


    def update_frame(self):
        if not self._cam: return
        ret, frame = self._cam.read()
        if not ret: return
        frame = cv2.flip(frame, 1)
        self._frame = frame.copy()

        for (x, y, w, h) in self.engine.detect_faces(frame):
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 200, 100), 2)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        self.cam_label.setPixmap(
            QPixmap.fromImage(QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888))
        )


    def simpan_wajah(self):
        if self._frame is None:
            QMessageBox.warning(self, "Peringatan", "Kamera belum aktif!")
            return

        faces = self.engine.detect_faces(self._frame)
        if not len(faces):
            QMessageBox.warning(self, "Gagal", "Tidak ada wajah terdeteksi. Coba lagi!"); return

        x, y, w, h = faces[0]
        emb = self.engine.get_embedding(self._frame, x, y, w, h)
        if emb is None:
            QMessageBox.warning(self, "Gagal", "Gagal mengekstrak fitur wajah."); return


        uid = SessionManager.get_user_id()
        os.makedirs("assets/photos", exist_ok=True)
        photo_path = f"assets/photos/{uid}.jpg"
        cv2.imwrite(photo_path, self._frame[y:y + h, x:x + w])


        emb_list = emb.tolist() if hasattr(emb, "tolist") else emb
        self.db.update_student_embedding(uid, emb_list, photo_path)


        self.matikan_kamera()
        QMessageBox.information(self, "Sukses", "Data wajah berhasil disimpan!")
        self.load_data()


    def matikan_kamera(self):
        self._timer.stop()
        if self._cam: self._cam.release(); self._cam = None
        self.cam_label.clear()
        self.btn_cam.setEnabled(True)
        self.btn_capture.setEnabled(False)


    def hideEvent(self, event):
        self.matikan_kamera()
        super().hideEvent(event)
