from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class PlanningForm(FlaskForm):
    nama_program = StringField('Nama Program', validators=[DataRequired()])
    pagu_anggaran = FloatField('Pagu Anggaran', validators=[DataRequired()])
    realisasi = FloatField('Realisasi')
    satuan_kerja = StringField('Satuan Kerja', validators=[DataRequired()])
    tahun = IntegerField('Tahun', validators=[DataRequired()])
    submit = SubmitField('Simpan')