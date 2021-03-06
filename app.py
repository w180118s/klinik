import os
from dotenv import load_dotenv
from flask import Flask, json, render_template, request, redirect, sessions, url_for, session, flash, jsonify, current_app, make_response
from flask.scaffold import F
from flask_sqlalchemy import SQLAlchemy, _record_queries
from sqlalchemy import func, or_
from sqlalchemy.orm import backref, selectin_polymorphic
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from sqlalchemy.sql.functions import user
from werkzeug.wrappers import response
# from werkzeug.wrappers import request
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import InputRequired
from flask_bootstrap import Bootstrap
from functools import wraps
from flask_migrate import Config, Migrate, migrate
import pandas as pd
import datetime
import pdfkit
from flask import session as sesi

load_dotenv()
app = Flask(__name__)

SECRET_KEY = os.environ.get('SECRET_KEY')
DATABASE_URI = os.environ.get('DATABASE_URI')

app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
bootstrap = Bootstrap(app)
migrate = Migrate(app, db)

class Login(FlaskForm):
    username = StringField('', validators=[InputRequired()], render_kw={'autofocus' :True, 'placeholder' : 'Username'})
    password = PasswordField('', validators=[InputRequired()], render_kw={'autofocus' :True, 'placeholder' : 'Password'})
    level = SelectField('', validators=[InputRequired()], choices=[('Admin', 'Admin'), ('Dokter', 'Dokter'), 
                                                                    ('Administrasi', 'Administrasi'),('konsumen', 'Konsumen')])

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.Text)
    level = db.Column(db.String(100))
    usernya = db.relationship('Pasien', backref=db.backref('user', lazy=True))

    def __init__(self, username, password, level):
        self.username = username
        if password !='':
            self.password = bcrypt.generate_password_hash(password).decode('UTF-8')
        self.level = level

#Database studi kasus login multi otentikasi
class Konsumen(db.Model):
    __tablename__ = 'konsumen'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.Text)
    level = db.Column(db.String(100))
    konsumennya = db.relationship('Pembelian', backref=db.backref('konsumen', lazy=True))

    def __init__(self, username, password, level):
        self.username = username
        if password !='':
            self.password = bcrypt.generate_password_hash(password).decode('UTF-8')
        self.level = level

#Database Studi Kasus bulk insert
class Pembelian(db.Model):
    __tablename__ = 'pembelian'
    id = db.Column(db.Integer, primary_key=True)
    id_konsumen = db.Column(db.Integer, db.ForeignKey('konsumen.id'))
    id_obat = db.Column(db.Integer, db.ForeignKey('obat.id'))

    def __init__(self, id_konsumen, id_obat):
        self.id_konsumen = id_konsumen
        self.id_obat = id_obat

class Dokter(db.Model):
    __tablename__ = 'dokter'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(150))
    jadwal = db.Column(db.Text)
    
    def __init__(self, nama, jadwal):
        self.nama = nama
        self.jadwal = jadwal

#database percobaan upload csv
class Biodata(db.Model):
    __tablename__ = 'biodata'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(150))
    belakang = db.Column(db.String(150))
    
    def __init__(self, nama, belakang):
        self.nama = nama
        self.belakang = belakang

class Suplier(db.Model):
    __tablename__ = 'suplier'
    id = db.Column(db.Integer, primary_key=True)
    perusahaan = db.Column(db.String(200))
    kontak = db.Column(db.String(100))
    alamat = db.Column(db.Text)
    supliernya = db.relationship('Obat', backref=db.backref('suplier', lazy=True))

    def __init__(self, perusahaan, kontak, alamat):
        self.perusahaan = perusahaan
        self.kontak = kontak
        self.alamat = alamat

class Obat(db.Model):
    __tablename__ = 'obat'
    id = db.Column(db.Integer, primary_key=True)
    namaObat = db.Column(db.String(150))
    jenisObat = db.Column(db.String(150))
    harga_beli = db.Column(db.Integer)
    harga_jual = db.Column(db.Integer)
    kondisi = db.Column(db.String(80))
    suplier_id = db.Column(db.Integer, db.ForeignKey('suplier.id'))
    obatnya = db.relationship('Pembelian', backref=db.backref('obat', lazy=True))

    def __init__(self, namaObat, jenisObat, harga_beli, harga_jual, kondisi, suplier_id):
        self.namaObat = namaObat
        self.jenisObat = jenisObat
        self.harga_beli = harga_beli
        self.harga_jual = harga_jual
        self.kondisi = kondisi 
        self.suplier_id = suplier_id

class Pendaftaran(db.Model):
    __tablename__ = 'pendaftaran'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(150))
    tl = db.Column(db.String(150))
    tgl_lahir = db.Column(db.String(150))
    jk = db.Column(db.String(150))
    status = db.Column(db.String(150))
    profesi = db.Column(db.String(100))
    alamat = db.Column(db.Text)
    keterangan = db.Column(db.String(100))
    db.relationship('pasien', backref=db.backref('pendaftaran', lazy=True))

    def __init__(self, nama, tl, tlg_lahir, jk, status, profesi, alamat, keterangan):
        self.nama = nama
        self.tl = tl
        self.tgl_lahir = tlg_lahir
        self.jk = jk
        self.status = status
        self.profesi = profesi 
        self.alamat = alamat
        self.keterangan = keterangan

class Pasien(db.Model):
    __tablename__ = 'pasien'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(150))
    keluhan = db.Column(db.Text)
    diagnosa = db.Column(db.String(150))
    resep = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pendaftaran_id = db.Column(db.Integer, db.ForeignKey('pendaftaran.id'))
    tanggal = db.Column(db.String(100))

    def __init__(self, nama, keluhan, diagnosa, resep, user_id, pendaftaran_id, tanggal):
        self.nama = nama
        self.keluhan = keluhan
        self.diagnosa = diagnosa
        self.resep = resep
        self.user_id = user_id
        self.pendaftaran_id = pendaftaran_id
        self.tanggal = tanggal

db.create_all()

def login_dulu(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'login' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap

@app.route('/')
def index():
    if session.get('login') == True:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('login') == True:
        return redirect(url_for('dashboard'))
    form = Login()
    if form.validate_on_submit():
        if form.level.data == 'konsumen': #validasi User Konsumen
            user = Konsumen.query.filter_by(username=form.username.data).first()
        else:
            user = User.query.filter_by(username=form.username.data).first() #Validasi admin, dokter dan administrasi
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data) and user.level == form.level.data:
                session['login'] = True
                session['id'] = user.id
                session['username'] = user.username
                session['level'] = user.level
                return redirect(url_for('dashboard'))
        pesan = "Username atau Password anda salah"
        return render_template("login.html", pesan=pesan, form=form)
    return render_template('login.html', form=form)

@app.route('/dashboard')
@login_dulu
def dashboard():
    data1 = db.session.query(Dokter).count()
    data2 = db.session.query(Pendaftaran).count()
    data3 = db.session.query(User).count()
    data4 = db.session.query(func.sum(Obat.harga_jual)).filter(Obat.kondisi == "rusak").scalar()
    data5 = db.session.query(func.sum(Obat.harga_jual)).filter(Obat.kondisi == "baik").scalar()
    return render_template('dashboard.html', data1=data1, data2=data2, data3=data3, data4=data4, data5=data5)

@app.route('/kelola_user')
@login_dulu
def kelola_user():
    data=User.query.all()
    return render_template('user.html', data=data)

@app.route('/tambahuser', methods=['GET','POST'])
@login_dulu
def tambahuser():
    if request.method == "POST":
        username = request.form['username']
        data = User.query.filter_by(username=username).first()
        if data:
            flash("Username sudah ada") 
            return redirect(request.referrer)
        password = request.form['password']
        level = request.form['level']
        db.session.add(User(username, password, level))
        db.session.commit()
        return redirect(url_for('kelola_user'))

@app.route('/edituser/<id>', methods=['GET', 'POST'])
@login_dulu
def edituser(id):
    data = User.query.filter_by(id=id).first()
    if request.method == 'POST':
        try:
            data.username = request.form['username']
            if data.password !='':
                data.password = bcrypt.generate_password_hash(request.form['password']).decode('UTF-8')
            data.level = request.form['level']
            db.session.add(data)
            db.session.commit()
            return redirect(url_for('kelola_user'))
        except:
            flash("Ada Trouble")
            return redirect(request.referrer)

@app.route('/hapususer/<id>', methods=['GET', 'POST'])
@login_dulu
def hapususer(id):
    data = User.query.filter_by(id=id).first()
    db.session.delete(data)
    db.session.commit()
    return redirect(url_for('kelola_user'))

@app.route('/pendaftaran')
@login_dulu
def pendaftaran():
    data = Pendaftaran.query.all()
    return render_template('/pendaftaran.html', data=data)

@app.route('/tambahdaftar', methods=['GET', 'POST'])
@login_dulu
def tambahdaftar():
    if request.method == "POST":
        nama = request.form['nama']
        tl = request.form['tl']
        tgl_lahir = request.form['tgl_lahir']
        jk = request.form['jk']
        status = request.form['status']
        profesi = request.form['profesi']
        alamat = request.form['alamat']
        keterangan = request.form['keterangan']
        db.session.add(Pendaftaran(nama, tl, tgl_lahir, jk, status, profesi, alamat, keterangan))
        db.session.commit()
        return  jsonify({'success' :True})
    else:
        return redirect(request.referrer)

@app.route('/editdaftar/<id>', methods=['GET', 'POST'])
@login_dulu
def editdaftar(id):
    data = Pendaftaran.query.filter_by(id=id).first()
    if request.method == 'POST':
        data.nama = request.form['nama']
        data.tl = request.form['tl']
        data.tgl_lahir = request.form['tgl_lahir']
        data.jk = request.form['jk']
        data.status = request.form['status']
        data.profesi = request.form['profesi']
        data.alamat = request.form['alamat']
        data.keterangan = request.form['keterangan']
        db.session.add(data)
        db.session.commit()
        return jsonify({'success' :True})
    else:
        return redirect(request.referrer)

@app.route('/hapusdaftar/<id>', methods=['GET', 'POST'])
@login_dulu
def hapusdaftar(id):
    data = Pendaftaran.query.filter_by(id=id).first()
    db.session.delete(data)
    db.session.commit()
    return redirect(request.referrer)

@app.route('/dokter')
@login_dulu
def dokter():
    data = Dokter.query.all()
    return render_template('/dokter.html', data=data)

@app.route('/tambahdokter', methods = ['GET', 'POST'])
@login_dulu
def tambahdokter():
    if request.method == 'POST':
        nama = request.form['nama']
        jadwal = request.form['jadwal']
        db.session.add(Dokter(nama, jadwal))
        db.session.commit()
        return jsonify({'success' :True})
    else:
        return redirect(request.referrer)

@app.route('/editdokter/<id>', methods = ['GET', 'POST'])
@login_dulu
def editdokter(id):
    data = Dokter.query.filter_by(id=id).first()
    if request.method == 'POST':
        data.nama = request.form['nama']
        data.jadwal = request.form['jadwal']
        db.session.add(data)
        db.session.commit()
        return jsonify({'success' :True})
    else:
        return redirect(request.referrer)

@app.route('/hapusdokter/<id>', methods=['GET', 'POST'])
@login_dulu
def hapusdokter(id):
    data = Dokter.query.filter_by(id=id).first()
    db.session.delete(data)
    db.session.commit()
    return redirect(request.referrer)

@app.route('/apotek')
@login_dulu
def apotek():
    data = Obat.query.all()
    data1 = Suplier.query.all()
    return render_template('/apotek.html', data=data, data1=data1)

@app.route('/tambahobat', methods=['GET', 'POST'])
@login_dulu
def tambahobat():
    if request.method == 'POST':
        namaObat = request.form['namaObat']
        jenisObat = request.form['jenisObat']
        harga_beli = request.form['harga_beli']
        harga_jual = request.form['harga_jual']
        kondisi = request.form['kondisi']
        suplier_id = request.form['suplier_id']
        db.session.add(Obat(namaObat, jenisObat, harga_beli, harga_jual, kondisi, suplier_id))
        db.session.commit()
        return  jsonify({'success' :True})
    else:
        return redirect(request.referrer)

@app.route('/editobat/<id>', methods=['GET', 'POST'])
@login_dulu
def editobat(id):
    data = Obat.query.filter_by(id=id).first()
    if request.method == 'POST':
        data.namaObat = request.form['namaObat']
        data.jenisObat = request.form['jenisObat']
        data.harga_beli = request.form['harga_beli']
        data.harga_jual = request.form['harga_jual']
        data.kondisi = request.form['kondisi']
        data.suplier_id = request.form['suplier_id']
        db.session.add(data)
        db.session.commit()
        return  jsonify({'success' :True})
    else:
        return redirect(request.referrer)

@app.route('/hapusobat/<id>', methods=['GET', 'POST'])
@login_dulu
def hapusobat(id):
    data = Obat.query.filter_by(id=id).first()
    db.session.delete(data)
    db.session.commit()
    return redirect(request.referrer)

@app.route('/suplier')
@login_dulu
def suplier():
    data = Suplier.query.all()
    return render_template('/suplier.html', data=data)

@app.route('/tambahsuplier', methods=['GET', 'POST'])
@login_dulu
def tambahsuplier():
    if request.method == "POST":
        perusahaan = request.form['perusahaan']
        kontak = request.form['kontak']
        if type(kontak) is not str:
            return jsonify({'success':False})
        alamat = request.form['alamat']
        db.session.add(Suplier(perusahaan, kontak, alamat,))
        db.session.commit()
        return  jsonify({'success' :True})
    else:
        return redirect(request.referrer)

@app.route('/editsuplier/<id>', methods = ['GET', 'POST'])
@login_dulu
def editsuplier(id):
    data = Suplier.query.filter_by(id=id).first()
    if request.method == 'POST':
        data.perusahaan = request.form['perusahaan']
        data.kontak = request.form['kontak']
        data.alamat = request.form['alamat']
        db.session.add(data)
        db.session.commit()
        return jsonify({'success' :True})
    else:
        return redirect(request.referrer)

@app.route('/hapussuplier/<id>', methods=['GET', 'POST'])
@login_dulu
def hapussuplier(id):
    data = Suplier.query.filter_by(id=id).first()
    db.session.delete(data)
    db.session.commit()
    return redirect(request.referrer)

@app.route('/tangani_pasien')
@login_dulu
def tangani_pasien():
    data = Pendaftaran.query.filter_by(keterangan='diproses').all()
    return render_template('/tangani.html', data=data)

@app.route('/diagnosis/<id>', methods=['GET', 'POST'])
@login_dulu
def diagnosis(id):
    data = Pendaftaran.query.filter_by(id=id).first()
    if request.method == "POST":
        nama = request.form['nama']
        keluhan = request.form['keluhan']
        diagnosa = request.form['diagnosa']
        resep = request.form['resep']
        user_id = request.form['user_id']
        pendaftaran_id = request.form['pendaftaran_id']
        tanggal = datetime.datetime.now().strftime("%d %B %Y jam %H:%M:%Y")
        data.keterangan = "Selesai" #Merubah field keterangan pada database pendaftaran
        db.session.add((data))
        db.session.commit()
        db.session.add(Pasien(nama, keluhan, diagnosa, resep, user_id, pendaftaran_id, tanggal))
        db.session.commit()
        return redirect(request.referrer)

@app.route('/pencarian')
@login_dulu
def pencarian():
    return render_template('/pencarian.html')
    
@app.route('/cari_data', methods=['GET', 'POST'])
@login_dulu
def cari_data():
    acuan = sesi.get('id')
    if request.method == 'POST':
        keyword = request.form['q']
        formt = "%{0}%".format(keyword)
        datanya = Pasien.query.join(User, Pasien.user_id == User.id).filter(or_(Pasien.tanggal.like(formt)), (Pasien.user_id.like(acuan))).all()
        if datanya:
            flash("Data Berhasil di temukan")
            tombol = "tombolcetak"
        elif not datanya:
            pesan = "Tidak ada Pasien yang diproses pada waktu tersebut"
            return render_template('/pencarian.html', datanya=datanya, pesan=pesan)
        return render_template('/pencarian.html', datanya=datanya, tombol=tombol, keyword=keyword)

@app.route('/daftarpasien', methods=['GET'])
@login_dulu
def daftarpasien():
    # buat variable tipe data list(array)
    pendaftaranList = []
    # cari data di table pasien dimana 'user_id' sama dengan 'userid'
    acuan = Pasien.query.all()
    # pengandaian, jika data acuan ditemukan, maka
    if acuan:
        # pengulangan untuk memasukan id kedalam variable 'pendaftaranList' dari data acuan
        for item in acuan:
            pendaftaranList.append(item.pendaftaran_id)
    # cari data di table pendaftaran dimana id pendafaftaran TIDAK SAMA DENGAN YANG ADA DI 'pendaftaranList'
    data = Pendaftaran.query.filter(Pendaftaran.id.notin_(pendaftaranList)).all()
    return render_template('test.html' , data=data)

@app.route('/cetak_pdf/<keyword>', methods=['GET', 'POST'])
@login_dulu
def cetak_pdf(keyword):
    formt = "%{0}%".format(keyword)
    datanya = Pasien.query.join(User, Pasien.user_id == User.id).filter(or_(Pasien.tanggal.like(formt))).all()
    html = render_template("pdf.html", datanya=datanya)
    Config = pdfkit.configuration(wkhtmltopdf= "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    pdf = pdfkit.from_string(html, False, configuration=Config)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=laporan.pdf'
    return response

@app.route('/logout')
@login_dulu
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/pembelian')
@login_dulu
def pembelian():
    data = Obat.query.all()
    return render_template('/pembelian.html', data=data)

#Bulk Insert 
@app.route('/tambah_pembelian', methods = ['GET', 'POST'])
@login_dulu
def tambah_pembelian():
    if request.method == 'POST':
        id_konsumen = request.form['id_konsumen']
        for key in request.form.getlist('id_obat'):
            db.session.add(Pembelian(id_konsumen, key))
        
        db.session.commit()
        return redirect(request.referrer)

@app.route('/import_csv',  methods=['GET', 'POST'])
def import_csv():
    if request.method == 'GET':
        return render_template('/import.html')
    else:
        try:
            file = request.files['file']
            read = pd.read_csv(file,delimiter=";",header=0)
            data = read.to_numpy()
            
            for row in data:
                nama = row[1]
                belakang = row[2]
                # disini
                db.session.add(Biodata(nama, belakang))

            db.session.commit()
            response = 'berhasil'
        except:
            response = 'gagal'
        return response

if __name__ == '__main__':
    app.run(debug=True)
 
