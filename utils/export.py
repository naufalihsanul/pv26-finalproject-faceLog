import csv
from PySide6.QtWidgets import QTableWidget, QFileDialog, QMessageBox


def export_to_csv(parent, table: QTableWidget, default_name: str = "export"):
    # Dialog simpan file CSV
    path, _ = QFileDialog.getSaveFileName(
        parent, "Simpan CSV", default_name, "CSV Files (*.csv)"
    )
    if not path:
        return

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Tulis header kolom
        headers = [
            table.horizontalHeaderItem(i).text()
            for i in range(table.columnCount())
        ]
        writer.writerow(headers)

        # Tulis setiap baris data
        for row in range(table.rowCount()):
            data = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                data.append(item.text() if item else "")
            writer.writerow(data)

    QMessageBox.information(parent, "Sukses", f"Data berhasil diekspor:\n{path}")


def export_to_pdf(parent, table: QTableWidget, title: str = "Laporan", default_name: str = "export"):
    # Dialog simpan file PDF
    path, _ = QFileDialog.getSaveFileName(
        parent, "Simpan PDF", default_name, "PDF Files (*.pdf)"
    )
    if not path:
        return

    try:
        from PySide6.QtGui import QPdfWriter, QTextDocument
        writer = QPdfWriter(path)
        writer.setPageSize(QPdfWriter.A4)
        writer.setResolution(300)

        # Bangun tabel sebagai teks terstruktur (tanpa HTML)
        doc = QTextDocument()
        lines = [title, "=" * 60]

        # Header kolom
        col_headers = [
            table.horizontalHeaderItem(i).text()
            for i in range(table.columnCount())
        ]
        lines.append(" | ".join(col_headers))
        lines.append("-" * 60)

        # Baris data
        for row in range(table.rowCount()):
            row_data = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                row_data.append(item.text() if item else "")
            lines.append(" | ".join(row_data))

        doc.setPlainText("\n".join(lines))
        doc.print_(writer)

        QMessageBox.information(parent, "Sukses", f"PDF berhasil diekspor:\n{path}")
    except Exception as e:
        QMessageBox.warning(parent, "Gagal", f"Export PDF gagal:\n{str(e)}")
