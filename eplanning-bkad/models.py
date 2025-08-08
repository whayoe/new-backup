from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    nama_lengkap = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, pegawai, verifikator
    nip = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Planning(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_program = db.Column(db.String(200), nullable=False)
    pagu_anggaran = db.Column(db.Float, nullable=False)
    realisasi = db.Column(db.Float, default=0.0)
    satuan_kerja = db.Column(db.String(100), nullable=False)
    tahun = db.Column(db.Integer, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default="Draft")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔗 Tambahkan relasi ke User
    user = db.relationship('User', backref='perencanaan')
    
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    aksi = db.Column(db.String(50), nullable=False)  # "verify", "create", "edit", "delete"
    target = db.Column(db.String(200), nullable=False)  # "Planning #5: Pengadaan Laptop"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    keterangan = db.Column(db.String(200))  # Opsional: "Dari Draft ke Diverifikasi"

    user = db.relationship('User', backref='logs')