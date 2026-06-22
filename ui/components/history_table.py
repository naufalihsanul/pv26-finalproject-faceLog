from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QCheckBox, QDateEdit, QPushButton
)
from PySide6.QtCore import Qt, QDate
import qtawesome as qta
from ui import theme
from utils.export import export_to_csv, export_to_pdf


class HistoryTable(QWidget):
    # Inisialisasi tabel riwayat absensi.
    def __init__(self, headers: list, title: str = "Riwayat Absensi",
                 show_search=True, show_date_filter=True, show_export=True,
                 parent=None):
        super().__init__(parent)
        self._title = title
        self._all_data = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Judul halaman
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(lbl)

        # Baris alat: search, filter, export
        tools = QHBoxLayout()

        if show_search:
            self.search = QLineEdit()
            self.search.setPlaceholderText("Cari NIM atau Nama...")
            self.search.textChanged.connect(self.filter_data)
            tools.addWidget(self.search)
        else:
            self.search = None

        if show_date_filter:
            self.chk_date = QCheckBox("Tanggal:")
            self.chk_date.stateChanged.connect(self.filter_data)
            self.date_edit = QDateEdit(QDate.currentDate())
            self.date_edit.setCalendarPopup(True)
            self.date_edit.dateChanged.connect(self.filter_data)
            tools.addWidget(self.chk_date)
            tools.addWidget(self.date_edit)
        else:
            self.chk_date = None
            self.date_edit = None

        if show_export:
            # Tombol export CSV
            btn_csv = QPushButton()
            btn_csv.setIcon(qta.icon("fa5s.file-csv", color="white"))
            btn_csv.setText("  Export CSV")
            btn_csv.clicked.connect(lambda: export_to_csv(self, self.table, title))
            tools.addWidget(btn_csv)

            # Tombol export PDF
            btn_pdf = QPushButton()
            btn_pdf.setIcon(qta.icon("fa5s.file-pdf", color="white"))
            btn_pdf.setText("  Export PDF")
            btn_pdf.clicked.connect(lambda: export_to_pdf(self, self.table, title, title))
            tools.addWidget(btn_pdf)

        layout.addLayout(tools)

        # Tabel data
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setAlternatingRowColors(True)
        # Sorting aktif — klik header untuk sort
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    # Isi data ke tabel.
    def isi_tabel(self, rows: list):
        self._all_data = rows
        self.tampilkan_data(rows)

    # Tampilkan baris ke tabel.
    def tampilkan_data(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))

                # Warna status hadir/tidak hadir
                if str(val).lower() == "hadir":
                    item.setForeground(Qt.darkGreen)
                elif str(val).lower() in ("tidak hadir", "pending"):
                    item.setForeground(Qt.darkRed)

                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)

    # Filter berdasarkan input pencarian.
    def filter_data(self):
        search_text = self.search.text().lower() if self.search else ""
        use_date = self.chk_date.isChecked() if self.chk_date else False
        filter_date = (
            self.date_edit.date().toString("yyyy-MM-dd")
            if use_date and self.date_edit else ""
        )

        filtered = []
        for row in self._all_data:
            # Cek teks di semua kolom
            match_search = any(search_text in str(v).lower() for v in row)

            # Cek tanggal di kolom terakhir (waktu)
            match_date = True
            if use_date and filter_date:
                last_val = str(row[-1]) if row else ""
                match_date = last_val.startswith(filter_date)

            if match_search and match_date:
                filtered.append(row)

        self.tampilkan_data(filtered)
