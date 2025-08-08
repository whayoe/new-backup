# app.py
from flask import Flask, render_template, redirect, url_for, flash, request, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

from config import Config
app = Flask(__name__)
app.config.from_object(Config)

# Inisialisasi
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from models import db, User, Planning
from forms import LoginForm, PlanningForm
from utils import export_to_excel


db.init_app(app)

# 🔽 Impor model setelah db siap
from models import User, Planning, Log  # ← Tambahkan Log di sini
from forms import LoginForm, PlanningForm
from datetime import datetime, timedelta

from utils import get_daily_activity

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_first_request
def create_tables():
    db.create_all()
    if not User.query.first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            nama_lengkap='Administrator BKAD',
            role='admin',
            nip='198001012006011001'
        )
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Login berhasil!")
            return redirect(url_for('dashboard'))
        flash("Username atau password salah.")
    return render_template('auth/login.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    total = Planning.query.filter_by(created_by=current_user.id).count()
    verified = Planning.query.filter_by(created_by=current_user.id, status='Diverifikasi').count()

    # Ambil data grafik (hanya untuk admin)
    if current_user.role == 'admin':
        labels, counts = get_daily_activity(days=7)
    else:
        labels, counts = [], []

    return render_template(
        'dashboard.html',
        total=total,
        verified=verified,
        labels=labels,
        counts=counts
    )

@app.route('/planning/create', methods=['GET', 'POST'])
@login_required
def create_planning():
    form = PlanningForm()
    if form.validate_on_submit():
        plan = Planning(
            nama_program=form.nama_program.data,
            pagu_anggaran=form.pagu_anggaran.data,
            realisasi=form.realisasi.data or 0.0,
            satuan_kerja=form.satuan_kerja.data,
            tahun=form.tahun.data,
            created_by=current_user.id,
            status="Draft"
        )
        db.session.add(plan)
        db.session.commit()
        flash("Perencanaan berhasil disimpan.")
        return redirect(url_for('dashboard'))
    return render_template('planning/create.html', form=form)

@app.route('/planning')
@login_required
def planning_list():
    plans = Planning.query.filter_by(created_by=current_user.id).all()
    return render_template('planning/list.html', plans=plans)

@app.route('/planning/export/excel')
@login_required
def export_planning_excel():
    plans = Planning.query.filter_by(created_by=current_user.id).all()
    filename = export_to_excel(plans)
    return send_file(filename, as_attachment=True)

@app.route('/planning/detail/<int:plan_id>')
@login_required
def detail_planning(plan_id):
    plan = Planning.query.get_or_404(plan_id)

    # Hanya pemilik atau admin yang bisa lihat
    if plan.created_by != current_user.id and current_user.role != 'admin':
        flash("Anda tidak berhak mengakses data ini.")
        return redirect(url_for('planning_list'))

    return render_template('planning/detail.html', plan=plan)
    
@app.route('/planning/edit/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def edit_planning(plan_id):
    # Ambil data perencanaan
    plan = Planning.query.get_or_404(plan_id)

    # 🔒 Cek: apakah sudah diverifikasi?
    if plan.status == 'Diverifikasi':
        flash("Data yang sudah diverifikasi tidak bisa diubah.")
        return redirect(url_for('planning_list'))
    # Cek hak akses: hanya pemilik atau admin
    if plan.created_by != current_user.id and current_user.role != 'admin':
        flash("Anda tidak berhak mengedit data ini.")
        return redirect(url_for('planning_list'))

    # Gunakan form dan isi dengan data lama
    form = PlanningForm(obj=plan)
    if form.validate_on_submit():
        # Update data
        plan.nama_program = form.nama_program.data
        plan.pagu_anggaran = form.pagu_anggaran.data
        plan.realisasi = form.realisasi.data or 0.0
        plan.satuan_kerja = form.satuan_kerja.data
        plan.tahun = form.tahun.data
        # Status bisa ditambahkan jika perlu

        db.session.commit()
        flash("Data perencanaan berhasil diperbarui.")
        return redirect(url_for('detail_planning', plan_id=plan.id))

    return render_template('planning/edit.html', form=form, plan=plan)
    
@app.route('/planning/delete/<int:plan_id>', methods=['POST'])
@login_required
def delete_planning(plan_id):
    plan = Planning.query.get_or_404(plan_id)

     # 🔒 Cek: apakah sudah diverifikasi?
    if plan.status == 'Diverifikasi':
        flash("Data yang sudah diverifikasi tidak bisa dihapus.")
        return redirect(url_for('planning_list'))
    # Cek hak akses: hanya pemilik atau admin
    if plan.created_by != current_user.id and current_user.role != 'admin':
        flash("Anda tidak berhak menghapus data ini.")
        return redirect(url_for('planning_list'))

    nama_program = plan.nama_program
    db.session.delete(plan)
    db.session.commit()
    flash(f"Perencanaan '{nama_program}' berhasil dihapus.")
    return redirect(url_for('planning_list'))
    
@app.route('/admin/delete/<int:plan_id>', methods=['POST'])
@login_required
def admin_delete_planning(plan_id):  # ✅ Nama beda
    plan = Planning.query.get_or_404(plan_id)
    if plan.created_by != current_user.id:
        flash("Tidak diizinkan.")
    else:
        db.session.delete(plan)
        db.session.commit()
        flash("Data dihapus.")
    return redirect(url_for('planning_list'))
    
@app.route('/planning/verify/<int:plan_id>')
@login_required
def verify_planning(plan_id):
    plan = Planning.query.get_or_404(plan_id)

    # Cek hak akses
    if current_user.role not in ['admin', 'verifikator']:
        flash("Anda tidak berhak melakukan verifikasi.")
        return redirect(url_for('planning_list'))

    # Cek status
    if plan.status == 'Diverifikasi':
        flash("Perencanaan ini sudah diverifikasi.")
        return redirect(url_for('planning_list'))

    # Simpan data sebelum update
    nama_program = plan.nama_program
    status_awal = plan.status

    # Update status
    plan.status = "Diverifikasi"
    db.session.commit()

    # 🔔 Catat ke log
    log = Log(
        user_id=current_user.id,
        aksi="verify",
        target=f"Planning #{plan.id}: {nama_program}",
        keterangan=f"Status diubah dari '{status_awal}' ke 'Diverifikasi'"
    )
    db.session.add(log)
    db.session.commit()

    flash(f"Perencanaan '{nama_program}' berhasil diverifikasi.")
    return redirect(url_for('planning_list'))
    
# app.py
@app.route('/log')
@login_required
def view_log():
    if current_user.role != 'admin':
        flash("Hanya admin yang bisa melihat log.")
        return redirect(url_for('dashboard'))

    # Ambil parameter filter dari URL
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    user_id = request.args.get('user_id', type=int)
    aksi = request.args.get('aksi')
    search = request.args.get('search', '')

    # Query awal
    query = Log.query.order_by(Log.timestamp.desc())

    # Filter berdasarkan tanggal
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Log.timestamp >= start)
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Log.timestamp <= end + timedelta(days=1))

    # Filter berdasarkan user
    if user_id:
        query = query.filter(Log.user_id == user_id)

    # Filter berdasarkan aksi
    if aksi:
        query = query.filter(Log.aksi == aksi)

    # Filter pencarian (target atau keterangan)
    if search:
        query = query.filter(
            (Log.target.contains(search)) |
            (Log.keterangan.contains(search))
        )

    # Eksekusi query
    logs = query.all()

    # Ambil daftar user untuk dropdown
    users = User.query.all()

    return render_template('log.html', logs=logs, users=users)
    
@app.route('/log/export/excel')
@login_required
def export_log_to_excel():
    if current_user.role != 'admin':
        flash("Hanya admin yang bisa ekspor log.")
        return redirect(url_for('view_log'))

    # Ambil semua log
    logs = Log.query.order_by(Log.timestamp.desc()).all()

    # Export ke Excel
    filename = export_log_to_excel(logs)
    return send_file(filename, as_attachment=True)
    
@app.route('/rekap-opd/export/excel')
@login_required
def export_rekap_opd():
    if current_user.role not in ['admin', 'verifikator']:
        flash("Akses ditolak.")
        return redirect(url_for('dashboard'))

    tahun = request.args.get('tahun', type=int, default=datetime.now().year)
    plans = Planning.query.filter_by(tahun=tahun).all()

    rekap = {}
    for p in plans:
        opd = p.satuan_kerja
        if opd not in rekap:
            rekap[opd] = {'total_program': 0, 'total_pagu': 0.0, 'terverifikasi': 0}
        rekap[opd]['total_program'] += 1
        rekap[opd]['total_pagu'] += p.pagu_anggaran
        if p.status == 'Diverifikasi':
            rekap[opd]['terverifikasi'] += 1

    for opd in rekap:
        total = rekap[opd]['total_program']
        rekap[opd]['persentase'] = round((rekap[opd]['terverifikasi'] / total * 100), 1) if total > 0 else 0

    filename = export_rekap_to_excel(rekap, tahun)
    return send_file(filename, as_attachment=True)
    
@app.route('/export/<string:data_type>')
@login_required
def export_all(data_type):
    if data_type == "planning":
        if current_user.role == 'admin':
            plans = Planning.query.all()
        else:
            plans = Planning.query.filter_by(created_by=current_user.id).all()
        filepath = export_to_excel("planning", plans)
        return send_file(filepath, as_attachment=True)

    elif data_type == "rekap_opd":
        if current_user.role not in ['admin', 'verifikator']:
            flash("Akses ditolak.")
            return redirect(url_for('dashboard'))
        tahun = request.args.get('tahun', type=int, default=datetime.now().year)
        plans = Planning.query.filter_by(tahun=tahun).all()
        rekap = {}
        for p in plans:
            opd = p.satuan_kerja
            if opd not in rekap:
                rekap[opd] = {'total_program': 0, 'total_pagu': 0.0, 'terverifikasi': 0}
            rekap[opd]['total_program'] += 1
            rekap[opd]['total_pagu'] += p.pagu_anggaran
            if p.status == 'Diverifikasi':
                rekap[opd]['terverifikasi'] += 1
        for opd in rekap:
            total = rekap[opd]['total_program']
            rekap[opd]['persentase'] = round((rekap[opd]['terverifikasi'] / total * 100), 1) if total > 0 else 0
        filepath = export_to_excel("rekap_opd", rekap, tahun=tahun)
        return send_file(filepath, as_attachment=True)

    elif data_type == "log":
        if current_user.role != 'admin':
            flash("Hanya admin yang bisa ekspor log.")
            return redirect(url_for('dashboard'))
        logs = Log.query.order_by(Log.timestamp.desc()).all()
        filepath = export_to_excel("log", logs)
        return send_file(filepath, as_attachment=True)

    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Anda berhasil logout.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    os.makedirs("static/downloads", exist_ok=True)
    app.run(debug=True)