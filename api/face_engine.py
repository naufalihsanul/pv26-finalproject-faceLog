import cv2
import numpy as np

# Coba import DeepFace (opsional)
DEEPFACE_AVAILABLE = False
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except Exception:
    pass


class FaceEngine:
    def __init__(self):
        # Load Haar Cascade untuk deteksi wajah
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(path)

    def detect_faces(self, frame):
        # Deteksi wajah dari frame kamera
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return self.face_cascade.detectMultiScale(gray, 1.1, 4)

    def get_embedding(self, frame, x, y, w, h):
        # Ekstrak vektor wajah dari ROI
        face_img = frame[y:y + h, x:x + w]

        if DEEPFACE_AVAILABLE:
            try:
                objs = DeepFace.represent(
                    img_path=face_img,
                    model_name="FaceNet",
                    enforce_detection=False,
                    detector_backend="opencv"
                )
                if objs:
                    return objs[0]["embedding"]
            except Exception:
                pass

        # Fallback: vektor piksel grayscale 16x16
        try:
            gray_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray_face, (16, 16), interpolation=cv2.INTER_AREA)
            vector = resized.astype(np.float32).flatten()
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            return vector.tolist()
        except Exception:
            return list(np.random.randn(256))

    def match_face(self, current_emb, registered_users):
        # Cocokkan embedding ke database mahasiswa
        if not registered_users:
            return None, 0.0

        best_match = None
        highest_sim = 0.0
        c_vec = np.array(current_emb, dtype=np.float64)

        for user in registered_users:
            try:
                u_vec = np.array(user["fitur_wajah"], dtype=np.float64)

                # Samakan dimensi jika berbeda
                if c_vec.shape[0] != u_vec.shape[0]:
                    max_dim = max(c_vec.shape[0], u_vec.shape[0])
                    c_pad = np.zeros(max_dim)
                    u_pad = np.zeros(max_dim)
                    c_pad[:c_vec.shape[0]] = c_vec
                    u_pad[:u_vec.shape[0]] = u_vec
                    c_vec_cmp, u_vec_cmp = c_pad, u_pad
                else:
                    c_vec_cmp, u_vec_cmp = c_vec, u_vec

                # Cosine similarity
                dot = np.dot(c_vec_cmp, u_vec_cmp)
                norm_c = np.linalg.norm(c_vec_cmp)
                norm_u = np.linalg.norm(u_vec_cmp)
                sim = dot / (norm_c * norm_u) if (norm_c > 0 and norm_u > 0) else 0.0

                if sim > highest_sim:
                    highest_sim = sim
                    best_match = user
            except Exception:
                continue

        # Threshold kecocokan wajah 60%
        if highest_sim >= 0.60:
            return best_match, highest_sim
        return None, highest_sim
