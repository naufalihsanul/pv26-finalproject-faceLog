import hashlib


def hash_password(password: str) -> str:
    # Hash SHA-256 untuk password
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    # Cek kecocokan password
    return hash_password(password) == hashed


class SessionManager:
    # Menyimpan data user login aktif
    current_user = None  # dict: {id, nama_pengguna, role, nama_lengkap}

    @staticmethod
    def login(user_dict):
        # Simpan sesi user
        SessionManager.current_user = user_dict

    @staticmethod
    def logout():
        # Hapus sesi user
        SessionManager.current_user = None

    @staticmethod
    def get_role():
        return SessionManager.current_user["role"] if SessionManager.current_user else None

    @staticmethod
    def get_user_id():
        return SessionManager.current_user["id"] if SessionManager.current_user else None

    @staticmethod
    def get_user_name():
        return SessionManager.current_user["nama_lengkap"] if SessionManager.current_user else None
