# utils.py
import os
from openpyxl import Workbook
from datetime import datetime
from datetime import datetime, timedelta

def export_to_excel(plans):
    """
    Export data perencanaan ke Excel
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Perencanaan Anggaran"

    # Header
    headers = ["No", "Program", "Pagu", "Realisasi", "Satuan Kerja", "Tahun", "Status"]
    ws.append(headers)

    # Isi data
    for i, p in enumerate(plans, 1):
        ws.append([
            i,
            p.nama_program,
            p.pagu_anggaran,
            p.realisasi,
            p.satuan_kerja,
            p.tahun,
            p.status
        ])

    # Format angka
    for row in ws.iter_rows(min_row=2, min_col=3, max_col=4):
        for cell in row:
            if cell.value:
                cell.number_format = '#,##0.00'

    # Simpan
    os.makedirs("static/downloads", exist_ok=True)
    filename = f"static/downloads/perencanaan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(filename)
    return filename
    
def get_daily_activity(days=7):
    """
    Ambil jumlah log per hari selama X hari terakhir
    Digunakan untuk grafik aktivitas harian di dashboard
    """
    # Hindari circular import
    from app import Log, db

    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=days-1)

    # Query jumlah log per hari
    results = db.session.query(
        db.func.date(Log.timestamp).label('date'),
        db.func.count(Log.id).label('count')
    ).filter(
        Log.timestamp >= week_ago
    ).group_by(
        db.func.date(Log.timestamp)
    ).order_by(
        db.func.date(Log.timestamp)
    ).all()

    # Siapkan data untuk Chart.js
    dates = []
    counts = []

    # Generate semua tanggal dalam rentang
    for i in range(days):
        date = (week_ago + timedelta(days=i)).strftime('%Y-%m-%d')
        dates.append(date)
        counts.append(0)  # Default 0

    # Konversi hasil query ke dict
    result_dict = {str(r.date): r.count for r in results}

    # Isi data yang ada
    for i, date in enumerate(dates):
        if date in result_dict:
            counts[i] = result_dict[date]

    # Format label: "01 Agu"
    labels = [datetime.strptime(d, '%Y-%m-%d').strftime('%d %b') for d in dates]

    return labels, counts