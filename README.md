# FaceLog — Sistem Absensi Berbasis Face Recognition

Aplikasi absensi mahasiswa menggunakan teknologi pengenalan wajah (Face Recognition).

## Anggota Kelompok
- Naufal Ihsanul Islam (F1D02310084)
- Didy Ardiyanto (F1D02310046)
- Apta Mahogra Bhamakerti (F1D022035)

## Cara Install & Jalankan

### 1. Install dependensi
```
pip install -r requirements.txt
```

### 2. Jalankan aplikasi
```
python main.py
```

### 3. Login default
- **Username:** `admin`
- **Password:** `admin123`

## Fitur Utama
- Login multi-role: Super Admin, Dosen, Mahasiswa
- Generate NIP (Dosen) dan NIM (Mahasiswa) otomatis
- Registrasi wajah mahasiswa via kamera
- Sistem request-approval bergabung kelas
- Absensi otomatis berbasis Face Recognition (AI/ML)
- Export laporan CSV & PDF
- Riwayat absensi per mata kuliah

## Struktur Folder
```
clone/
├── main.py
├── requirements.txt
├── README.md
├── api/          # Auth & Face Recognition engine
├── database/     # SQLite DB manager
├── models/       # Data entities (dataclass)
├── utils/        # Export helper (CSV, PDF)
├── ui/           # Semua tampilan (QSS, theme, halaman)
└── assets/       # Foto profil mahasiswa
```
