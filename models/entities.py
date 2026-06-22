from dataclasses import dataclass
from typing import Optional, List


@dataclass
class User:
    # Entitas dosen / super admin
    id: int
    nama_pengguna: str
    nama_lengkap: str
    role: str


@dataclass
class Student:
    # Entitas mahasiswa
    id: int
    nim: str
    nama_lengkap: str
    jurusan: str
    fitur_wajah: Optional[List] = None
    path_foto: Optional[str] = None
    status: Optional[str] = None  # Status di kelas: active/pending


@dataclass
class Course:
    # Entitas mata kuliah
    id: int
    kode_matkul: str
    nama_matkul: str
    semester: str
    tahun_ajaran: str
    dosen_name: Optional[str] = None


@dataclass
class AttendanceLog:
    # Entitas log kehadiran
    id: int
    nim: str
    nama_lengkap: str
    status: str
    waktu_scan: str
    nama_sesi: str
    nama_matkul: str
    skor_kecocokan: Optional[float] = None
