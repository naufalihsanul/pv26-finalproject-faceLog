import sqlite3
import json
import os
import random
from api.auth import hash_password


class DBManager:
    def __init__(self, db_path="database/facelog.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.create_tables()
        self.seed_admin()

    def generate_unique_nim(self):
        cursor = self.conn.cursor()
        while True:
            nim = f"F1D{random.randint(100000, 999999)}"
            cursor.execute("SELECT nim FROM mahasiswa WHERE nim = ?", (nim,))
            if not cursor.fetchone():
                return nim

    def generate_unique_nip(self, full_name=""):
        cursor = self.conn.cursor()
        prefix = (full_name[:3].upper() if len(full_name) >= 3 else full_name.upper()) or "DOS"
        while True:
            nip = f"{prefix}{random.randint(100000, 999999)}"
            cursor.execute("SELECT nip FROM dosen WHERE nip = ?", (nip,))
            if not cursor.fetchone():
                return nip

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                username TEXT PRIMARY KEY,
                kata_sandi TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dosen (
                nip TEXT PRIMARY KEY,
                nama_lengkap TEXT NOT NULL,
                kata_sandi TEXT NOT NULL,
                dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mahasiswa (
                nim TEXT PRIMARY KEY,
                nama_lengkap TEXT NOT NULL,
                jurusan TEXT,
                fitur_wajah TEXT,
                path_foto TEXT,
                kata_sandi TEXT,
                dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mata_kuliah (
                kode_matkul TEXT PRIMARY KEY,
                nama_matkul TEXT NOT NULL,
                nip TEXT NOT NULL,
                semester TEXT,
                tahun_ajaran TEXT,
                dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(nip) REFERENCES dosen(nip) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kelas_mahasiswa (
                id_kelas INTEGER PRIMARY KEY AUTOINCREMENT,
                kode_matkul TEXT NOT NULL,
                nim TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                mendaftar_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(kode_matkul) REFERENCES mata_kuliah(kode_matkul) ON DELETE CASCADE,
                FOREIGN KEY(nim) REFERENCES mahasiswa(nim) ON DELETE CASCADE,
                UNIQUE(kode_matkul, nim)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sesi_absensi (
                id_sesi INTEGER PRIMARY KEY AUTOINCREMENT,
                kode_matkul TEXT NOT NULL,
                nama_sesi TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'closed')),
                dibuka_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ditutup_pada TIMESTAMP,
                FOREIGN KEY(kode_matkul) REFERENCES mata_kuliah(kode_matkul) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS riwayat_absensi (
                id_riwayat INTEGER PRIMARY KEY AUTOINCREMENT,
                id_sesi INTEGER NOT NULL,
                nim TEXT NOT NULL,
                status TEXT NOT NULL,
                waktu_scan TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(id_sesi) REFERENCES sesi_absensi(id_sesi) ON DELETE CASCADE,
                FOREIGN KEY(nim) REFERENCES mahasiswa(nim) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    def seed_admin(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM admin WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO admin (username, kata_sandi) VALUES (?, ?)", ("admin", hash_password("admin123")))
            self.conn.commit()

    def authenticate_user(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username, kata_sandi FROM admin WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row and row[1] == hash_password(password):
            return {"id": row[0], "nama_pengguna": row[0], "nama_lengkap": "Administrator", "role": "super_admin"}

        cursor.execute("SELECT nip, kata_sandi, nama_lengkap FROM dosen WHERE nip = ?", (username,))
        row = cursor.fetchone()
        if row and row[1] == hash_password(password):
            return {"id": row[0], "nama_pengguna": row[0], "nama_lengkap": row[2], "role": "dosen"}

        cursor.execute("SELECT nim, kata_sandi, nama_lengkap FROM mahasiswa WHERE nim = ?", (username,))
        row = cursor.fetchone()
        if row and row[1] == hash_password(password):
            return {"id": row[0], "nama_pengguna": row[0], "nama_lengkap": row[2], "role": "mahasiswa"}
        return None

    def get_all_dosen(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT nip, nama_lengkap FROM dosen ORDER BY nama_lengkap")
        return [{"id": r[0], "nama_pengguna": r[0], "nama_lengkap": r[1]} for r in cursor.fetchall()]

    def add_dosen(self, password, full_name):
        cursor = self.conn.cursor()
        nip = self.generate_unique_nip(full_name)
        try:
            cursor.execute("INSERT INTO dosen (nip, kata_sandi, nama_lengkap) VALUES (?, ?, ?)", (nip, hash_password(password), full_name))
            self.conn.commit()
            return True, f"Dosen berhasil dibuat. NIP: {nip}"
        except sqlite3.IntegrityError:
            return False, "NIP sudah digunakan"

    def update_dosen(self, dosen_id, full_name, new_password=None):
        cursor = self.conn.cursor()
        if new_password:
            cursor.execute("UPDATE dosen SET nama_lengkap=?, kata_sandi=? WHERE nip=?", (full_name, hash_password(new_password), dosen_id))
        else:
            cursor.execute("UPDATE dosen SET nama_lengkap=? WHERE nip=?", (full_name, dosen_id))
        self.conn.commit()

    def delete_user(self, dosen_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM dosen WHERE nip=?", (dosen_id,))
        self.conn.commit()

    def get_all_courses(self, dosen_id=None):
        cursor = self.conn.cursor()
        if dosen_id:
            cursor.execute("SELECT kode_matkul, nama_matkul, semester, tahun_ajaran FROM mata_kuliah WHERE nip=? ORDER BY nama_matkul", (dosen_id,))
            return [{"id": r[0], "kode_matkul": r[0], "nama_matkul": r[1], "semester": r[2], "tahun_ajaran": r[3]} for r in cursor.fetchall()]
        else:
            cursor.execute("""
                SELECT c.kode_matkul, c.nama_matkul, c.semester, c.tahun_ajaran, d.nama_lengkap
                FROM mata_kuliah c JOIN dosen d ON c.nip=d.nip ORDER BY c.nama_matkul
            """)
            return [{"id": r[0], "kode_matkul": r[0], "nama_matkul": r[1], "semester": r[2], "tahun_ajaran": r[3], "dosen_name": r[4]} for r in cursor.fetchall()]

    def get_student_courses(self, student_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.kode_matkul, c.nama_matkul, d.nama_lengkap, cs.status
            FROM mata_kuliah c
            JOIN kelas_mahasiswa cs ON c.kode_matkul=cs.kode_matkul
            JOIN dosen d ON c.nip=d.nip
            WHERE cs.nim=?
        """, (student_id,))
        return [{"id": r[0], "kode": r[0], "nama": r[1], "dosen": r[2], "status": r[3]} for r in cursor.fetchall()]

    def add_course(self, kode, nama, dosen_id, semester, tahun):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO mata_kuliah (kode_matkul, nama_matkul, nip, semester, tahun_ajaran) VALUES (?,?,?,?,?)",
                           (kode, nama, dosen_id, semester, tahun))
            self.conn.commit(); return True, "Berhasil"
        except sqlite3.IntegrityError:
            return False, "Kode matkul sudah ada"

    def update_course(self, course_id, kode, nama, semester, tahun):
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE mata_kuliah SET kode_matkul=?, nama_matkul=?, semester=?, tahun_ajaran=? WHERE kode_matkul=?",
                           (kode, nama, semester, tahun, course_id))
            self.conn.commit(); return True, "Berhasil"
        except sqlite3.IntegrityError:
            return False, "Kode matkul sudah ada"

    def delete_course(self, course_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM mata_kuliah WHERE kode_matkul=?", (course_id,))
        self.conn.commit()

    def create_student_account(self, name, password, jurusan):
        cursor = self.conn.cursor()
        nim = self.generate_unique_nim()
        try:
            cursor.execute("INSERT INTO mahasiswa (nim, nama_lengkap, kata_sandi, jurusan) VALUES (?,?,?,?)",
                           (nim, name, hash_password(password), jurusan))
            self.conn.commit()
            return True, f"Mahasiswa dibuat. NIM: {nim}"
        except sqlite3.IntegrityError:
            return False, "Gagal membuat akun"

    def get_all_students_global(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT nim, nama_lengkap, jurusan FROM mahasiswa ORDER BY nim")
        return [{"id": r[0], "nim": r[0], "nama_lengkap": r[1], "jurusan": r[2]} for r in cursor.fetchall()]

    def get_student_profile(self, student_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT nim, nama_lengkap, jurusan, fitur_wajah, path_foto FROM mahasiswa WHERE nim=?", (student_id,))
        r = cursor.fetchone()
        return {"id": r[0], "nim": r[0], "nama_lengkap": r[1], "jurusan": r[2], "fitur_wajah": r[3], "path_foto": r[4]} if r else None

    def get_students_by_course(self, course_id, status=None):
        cursor = self.conn.cursor()
        if status:
            cursor.execute("""
                SELECT s.nim, s.nama_lengkap, s.jurusan, s.fitur_wajah, s.path_foto, cs.status
                FROM mahasiswa s JOIN kelas_mahasiswa cs ON s.nim=cs.nim
                WHERE cs.kode_matkul=? AND cs.status=? ORDER BY s.nama_lengkap
            """, (course_id, status))
        else:
            cursor.execute("""
                SELECT s.nim, s.nama_lengkap, s.jurusan, s.fitur_wajah, s.path_foto, cs.status
                FROM mahasiswa s JOIN kelas_mahasiswa cs ON s.nim=cs.nim
                WHERE cs.kode_matkul=? ORDER BY cs.status DESC, s.nama_lengkap
            """, (course_id,))
        return [{"id": r[0], "nim": r[0], "nama_lengkap": r[1], "jurusan": r[2],
                 "fitur_wajah": json.loads(r[3]) if r[3] else None, "path_foto": r[4], "status": r[5]
                 } for r in cursor.fetchall()]

    def update_student(self, student_id, nim, name, jurusan, new_password=None):
        cursor = self.conn.cursor()
        try:
            if new_password:
                cursor.execute("UPDATE mahasiswa SET nim=?, nama_lengkap=?, jurusan=?, kata_sandi=? WHERE nim=?",
                               (nim, name, jurusan, hash_password(new_password), student_id))
            else:
                cursor.execute("UPDATE mahasiswa SET nim=?, nama_lengkap=?, jurusan=? WHERE nim=?",
                               (nim, name, jurusan, student_id))
            self.conn.commit(); return True, "Berhasil"
        except sqlite3.IntegrityError:
            return False, "NIM sudah dipakai"

    def update_student_embedding(self, student_id, embedding_list, photo_path):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE mahasiswa SET fitur_wajah=?, path_foto=? WHERE nim=?",
                       (json.dumps(embedding_list), photo_path, student_id))
        self.conn.commit()

    def delete_student(self, student_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM mahasiswa WHERE nim=?", (student_id,))
        self.conn.commit()

    def delete_student_from_course(self, student_id, course_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM kelas_mahasiswa WHERE nim=? AND kode_matkul=?", (student_id, course_id))
        self.conn.commit()

    def request_join_course(self, student_id, course_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO kelas_mahasiswa (kode_matkul, nim, status) VALUES (?,?,'pending')",
                           (course_id, student_id))
            self.conn.commit()
            return True, "Permintaan bergabung terkirim"
        except sqlite3.IntegrityError:
            return False, "Sudah tergabung atau sudah request ke kelas ini"

    def update_course_student_status(self, student_id, course_id, status):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE kelas_mahasiswa SET status=? WHERE nim=? AND kode_matkul=?",
                       (status, student_id, course_id))
        self.conn.commit()

    def open_session(self, course_id, session_name):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO sesi_absensi (kode_matkul, nama_sesi, status) VALUES (?,?,'open')",
                       (course_id, session_name))
        self.conn.commit()
        return cursor.lastrowid

    def close_session(self, session_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE sesi_absensi SET status='closed', ditutup_pada=CURRENT_TIMESTAMP WHERE id_sesi=?", (session_id,))
        cursor.execute("SELECT kode_matkul FROM sesi_absensi WHERE id_sesi=?", (session_id,))
        res = cursor.fetchone()
        if res:
            course_id = res[0]
            cursor.execute("""
                SELECT nim FROM kelas_mahasiswa
                WHERE kode_matkul=? AND status='active' AND nim NOT IN (
                    SELECT nim FROM riwayat_absensi WHERE id_sesi=?
                )
            """, (course_id, session_id))
            for (sid,) in cursor.fetchall():
                cursor.execute("INSERT INTO riwayat_absensi (id_sesi, nim, status) VALUES (?,?,'Tidak Hadir')",
                               (session_id, sid))
        self.conn.commit()

    def update_session(self, session_id, session_name):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE sesi_absensi SET nama_sesi=? WHERE id_sesi=?", (session_name, session_id))
        self.conn.commit()

    def reopen_session(self, session_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE sesi_absensi SET status='open', ditutup_pada=NULL WHERE id_sesi=?", (session_id,))
        cursor.execute("DELETE FROM riwayat_absensi WHERE id_sesi=? AND status='Tidak Hadir'", (session_id,))
        self.conn.commit()

    def delete_session(self, session_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM sesi_absensi WHERE id_sesi=?", (session_id,))
        self.conn.commit()

    def get_sessions_by_course(self, course_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id_sesi, nama_sesi, status, dibuka_pada, ditutup_pada FROM sesi_absensi WHERE kode_matkul=? ORDER BY dibuka_pada DESC",
                       (course_id,))
        return [{"id": r[0], "nama_sesi": r[1], "status": r[2], "dibuka_pada": r[3], "ditutup_pada": r[4]} for r in cursor.fetchall()]

    def get_active_session(self, course_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id_sesi, nama_sesi, dibuka_pada FROM sesi_absensi WHERE kode_matkul=? AND status='open' LIMIT 1", (course_id,))
        row = cursor.fetchone()
        return {"id": row[0], "nama_sesi": row[1], "dibuka_pada": row[2]} if row else None

    def log_attendance(self, session_id, student_id, status):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id_riwayat FROM riwayat_absensi WHERE id_sesi=? AND nim=?", (session_id, student_id))
        if cursor.fetchone(): return
        cursor.execute("INSERT INTO riwayat_absensi (id_sesi, nim, status) VALUES (?,?,?)",
                       (session_id, student_id, status))
        self.conn.commit()

    def get_logs_by_session(self, session_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT l.id_riwayat, s.nim, s.nama_lengkap, l.status, l.waktu_scan
            FROM riwayat_absensi l JOIN mahasiswa s ON l.nim=s.nim
            WHERE l.id_sesi=? ORDER BY l.waktu_scan DESC
        """, (session_id,))
        return [{"id": r[0], "nim": r[1], "nama_lengkap": r[2], "status": r[3], "waktu_scan": r[4]} for r in cursor.fetchall()]

    def get_all_logs(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT l.id_riwayat, s.nim, s.nama_lengkap, l.status, l.waktu_scan, sess.nama_sesi, c.nama_matkul
            FROM riwayat_absensi l
            JOIN mahasiswa s ON l.nim=s.nim
            JOIN sesi_absensi sess ON l.id_sesi=sess.id_sesi
            JOIN mata_kuliah c ON sess.kode_matkul=c.kode_matkul
            ORDER BY l.waktu_scan DESC
        """)
        return [{"id": r[0], "nim": r[1], "nama_lengkap": r[2], "status": r[3],
                 "waktu_scan": r[4], "nama_sesi": r[5], "nama_matkul": r[6]} for r in cursor.fetchall()]

    def get_logs_by_student(self, student_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT l.id_riwayat, c.nama_matkul, sess.nama_sesi, l.status, l.waktu_scan, sess.status
            FROM riwayat_absensi l
            JOIN sesi_absensi sess ON l.id_sesi=sess.id_sesi
            JOIN mata_kuliah c ON sess.kode_matkul=c.kode_matkul
            WHERE l.nim=? ORDER BY l.waktu_scan DESC
        """, (student_id,))
        return [{"id": r[0], "matkul": r[1], "sesi": r[2], "status": r[3], "waktu": r[4], "sesi_status": r[5]} for r in cursor.fetchall()]

    def get_global_stats(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dosen")
        d = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM mahasiswa")
        s = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM mata_kuliah")
        c = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sesi_absensi WHERE date(dibuka_pada)=date('now')")
        t = cursor.fetchone()[0]
        return {"dosen_count": d, "student_count": s, "course_count": c, "sessions_today": t}

    def get_dosen_stats(self, dosen_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM mata_kuliah WHERE nip=?", (dosen_id,))
        c = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COUNT(DISTINCT cs.nim) FROM kelas_mahasiswa cs
            JOIN mata_kuliah co ON cs.kode_matkul=co.kode_matkul WHERE co.nip=? AND cs.status='active'
        """, (dosen_id,))
        s = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COUNT(*) FROM sesi_absensi se
            JOIN mata_kuliah co ON se.kode_matkul=co.kode_matkul
            WHERE co.nip=? AND date(se.dibuka_pada)=date('now')
        """, (dosen_id,))
        t = cursor.fetchone()[0]
        return {"course_count": c, "student_count": s, "sessions_today": t}
