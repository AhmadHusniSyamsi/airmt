import calendar
import csv
import io
import os
from collections import Counter, defaultdict
from datetime import datetime
from operator import attrgetter

import plotly.graph_objs as go
import plotly.io as pio
from flask import (Flask, flash, redirect, render_template, request, send_file,
                   url_for)
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from flask_migrate import Migrate
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from extensions import db
from models import (Station, Station_dme, Station_dvor, Transmission,
                    Transmission_dme, Transmission_dvor, User)

app = Flask(__name__)
app.secret_key = 'rahasia'
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from auth_routes import auth_bp
from dme_routes import dme_bp
from dvor_routes import dvor_bp
from gc_routes import groundcheck_bp
from ils_route import ils_bp
from radar_routes import radar_bp

app.register_blueprint(groundcheck_bp)
app.register_blueprint(dvor_bp)
app.register_blueprint(dme_bp)
app.register_blueprint(radar_bp)
app.register_blueprint(ils_bp)
app.register_blueprint(auth_bp)

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main_dashboard'))
    return redirect(url_for('login'))

@app.route('/main_dashboard', methods=['GET', 'POST'])
@login_required
def main_dashboard():
    return render_template('main_dashboard.html')

@app.route('/llz/cek_status')
def cek_status():
    return render_template('llz/cek_status.html')

@app.route('/llz/lihat_data')
def lihat_data():
    return render_template('llz/lihat_data.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Username atau password salah.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/index')
def index():
    return render_template('index.html')
@app.route("/history")
def history():
    return render_template("history.html")

# === VHF===
@app.route('/station_list')
@login_required
def station_list():
    stations = Station.query.all()
    return render_template('vhf/station_list.html', stations=stations)

@app.route('/station/add', methods=['GET', 'POST'])
@login_required
def add_station():
    if request.method == 'POST':
        nama = request.form['nama_stasiun']
        frek = request.form['frekuensi']
        new_station = Station(nama_stasiun=nama, frekuensi=frek)
        db.session.add(new_station)
        db.session.commit()
        return redirect(url_for('add_transmission', nama_stasiun=new_station.nama_stasiun))
    return render_template('vhf/station_form.html')

@app.route('/transmission/add/<path:nama_stasiun>', methods=['GET', 'POST'])
@login_required
def add_transmission(nama_stasiun):
    station = Station.query.filter_by(nama_stasiun=nama_stasiun).first_or_404()
    if request.method == 'POST':
        tx = Transmission(
            station_id=station.id,
            tx1_power=float(request.form.get('tx1_power') or 0),
            tx1_swr=request.form.get('tx1_swr'),
            tx1_mod=float(request.form.get('tx1_mod') or 0),
            tx2_power=float(request.form.get('tx2_power') or 0),
            tx2_swr=request.form.get('tx2_swr'),
            tx2_mod=float(request.form.get('tx2_mod') or 0),
            tanggal=datetime.strptime(request.form['tanggal'], '%Y-%m-%d'),
            pic=request.form['pic']
        )
        db.session.add(tx)
        db.session.commit()
        flash('Data berhasil disimpan.', 'success')

        if request.form.get('action') == 'save_and_add':
            return redirect(url_for('add_transmission', nama_stasiun=station.nama_stasiun))
        return redirect(url_for('view_data'))

    return render_template('vhf/transmission_form.html', station=station, tx=None)

# === Dashboard ===
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template(
        'vhf/dashboard.html',
    )

@app.route('/data')
@login_required
def view_data():
    stations = Station.query.order_by(Station.nama_stasiun).all()
    grouped_data = []
    for station in stations:
        transmissions = Transmission.query.filter_by(station_id=station.id).all()
        if transmissions:
            per_year = defaultdict(list)
            for tx in transmissions:
                year = tx.tanggal.year
                per_year[year].append(tx)
            for year in per_year:
                per_year[year].sort(key=attrgetter('tanggal'))
            sorted_per_year = dict(sorted(per_year.items(), reverse=True))
            grouped_data.append({'station': station, 'per_year': sorted_per_year})
    return render_template('vhf/data_table.html', grouped_data=grouped_data)

@app.route('/transmission/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transmission(id):
    tx = Transmission.query.get_or_404(id)
    station = Station.query.get_or_404(tx.station_id)
    if request.method == 'POST':
        tx.tx1_power = float(request.form.get('tx1_power') or 0)
        tx.tx1_swr = request.form.get('tx1_swr')
        tx.tx1_mod = float(request.form.get('tx1_mod') or 0)
        tx.tx2_power = float(request.form.get('tx2_power') or 0)
        tx.tx2_swr = request.form.get('tx2_swr')
        tx.tx2_mod = float(request.form.get('tx2_mod') or 0)
        tx.tanggal = datetime.strptime(request.form.get('tanggal'), '%Y-%m-%d')
        tx.pic = request.form.get('pic')
        db.session.commit()
        return redirect(url_for('view_data'))
    return render_template('vhf/transmission_form.html', tx=tx, station=station)

@app.route('/transmission/delete/<int:id>', methods=['GET'])
@login_required
def delete_transmission(id):
    tx = Transmission.query.get_or_404(id)
    db.session.delete(tx)
    db.session.commit()
    return redirect(url_for('view_data'))

@app.route('/station/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_station(id):
    station = Station.query.get_or_404(id)
    if request.method == 'POST':
        station.nama_stasiun = request.form['nama_stasiun']
        station.frekuensi = request.form['frekuensi']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('vhf/station_form.html', station=station)

@app.route('/station/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_station(id):
    station = Station.query.get_or_404(id)
    Transmission.query.filter_by(station_id=station.id).delete()
    db.session.delete(station)
    db.session.commit()
    return redirect(url_for('station_list'))

# === User Profile ===
UPLOAD_FOLDER = 'static/uploads/profile'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.nama = request.form['nama']
        current_user.tanggal_lahir = datetime.strptime(request.form['tanggal_lahir'], '%Y-%m-%d')
        current_user.jabatan = request.form['jabatan']
        current_user.nip = request.form['nip']
        current_user.email = request.form['email']
        current_user.no_hp = request.form['no_hp']
        current_user.jenis_kelamin = request.form['jenis_kelamin']
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                current_user.photo = filename
        db.session.commit()
        flash('Profil berhasil diperbarui!', 'success')
        return redirect(url_for('profile'))
    return render_template('edit_profile.html', user=current_user)

# === CSV ===
@app.route('/export')
@login_required
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Stasiun', 'Frekuensi', 'TX1 Power', 'TX1 SWR', 'TX1 Mod%',
                     'TX2 Power', 'TX2 SWR', 'TX2 Mod%', 'Tanggal', 'PIC'])
    txs = Transmission.query.join(Station).add_columns(
        Station.nama_stasiun, Station.frekuensi,
        Transmission.tx1_power, Transmission.tx1_swr, Transmission.tx1_mod,
        Transmission.tx2_power, Transmission.tx2_swr, Transmission.tx2_mod,
        Transmission.tanggal, Transmission.pic
    ).all()
    for row in txs:
        writer.writerow([row.nama_stasiun, row.frekuensi,
                         row.tx1_power, row.tx1_swr, row.tx1_mod,
                         row.tx2_power, row.tx2_swr, row.tx2_mod,
                         row.tanggal, row.pic])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                     as_attachment=True, download_name='data_vhf.csv')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
