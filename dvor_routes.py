from flask import Blueprint, Flask, render_template, request, redirect, url_for, send_file, flash
from flask_login import login_required
from config import Config
from models import Station_dvor,  Transmission_dvor, db, Station, Transmission
from datetime import datetime
import io
import csv
import plotly.graph_objs as go
import plotly.io as pio
from flask_migrate import Migrate
from flask_login import LoginManager, current_user, login_required
from werkzeug.security import check_password_hash
from collections import Counter, defaultdict
from operator import attrgetter
from models import Station_dvor

dvor_bp = Blueprint('dvor', __name__)

@dvor_bp.route('/station_dvor/add', methods=['GET', 'POST'])
@login_required
def add_station_dvor():
    if request.method == 'POST':
        nama = request.form['nama_stasiun_dvor']
        frek = request.form['frekuensi_dvor']
        new_station = Station_dvor(nama_stasiun_dvor=nama, frekuensi_dvor=frek)
        db.session.add(new_station)
        db.session.commit()
        
        # Perbaikan redirect (pakai prefix 'dvor.' dan param yang sesuai)
        return redirect(url_for('dvor.add_transmission_dvor', nama_stasiun=new_station.nama_stasiun_dvor))
    
    return render_template('dvor/stationform_dvor.html')


@dvor_bp.route('/stationlist_dvor')
@login_required
def stationlist_dvor():
    stations = Station_dvor.query.all()
    return render_template('dvor/stationlist_dvor.html', stations=stations)

@dvor_bp.route('/data_dvor')
@login_required
def view_data_dvor():
    stations = Station_dvor.query.order_by(Station_dvor.nama_stasiun_dvor).all()


    grouped_data_dvor = []
    for station in stations:
        transmissions = Transmission_dvor.query.filter_by(station_dvor_id=station.id).all()
        if transmissions:
            # Group by year
            per_year = defaultdict(list)
            for tx in transmissions:
                year = tx.tanggal.year
                per_year[year].append(tx)

            # Urutkan berdasarkan bulan dan tanggal (ascending)
            for year in per_year:
                per_year[year].sort(key=attrgetter('tanggal'))  # ascending order

            # Urutkan tahun dari terbaru ke lama
            sorted_per_year = dict(sorted(per_year.items(), reverse=True))

            grouped_data_dvor.append({
                'station_dvor': station,
                'per_year': sorted_per_year
            })

    return render_template('dvor/data_table_dvor.html', grouped_data_dvor=grouped_data_dvor)


@dvor_bp.route('/transmission_dvor/add/<path:nama_stasiun>', methods=['GET', 'POST'])
@login_required
def add_transmission_dvor(nama_stasiun):
    station = Station_dvor.query.filter_by(nama_stasiun_dvor=nama_stasiun).first_or_404()

    if request.method == 'POST':
        tx = Transmission_dvor(
            station_dvor_id=station.id,
            tx1_power=float(request.form.get('tx1_power') or 0),
            tx1_bearing=float(request.form.get('tx1_bearing') or 0),
            tx1_modulasi=float(request.form.get('tx1_modulasi') or 0),
            tx2_power=float(request.form.get('tx2_power') or 0),
            tx2_bearing=float(request.form.get('tx2_bearing') or 0),
            tx2_modulasi=float(request.form.get('tx2_modulasi') or 0),
            tanggal=datetime.strptime(request.form['tanggal'], '%Y-%m-%d'),
            pic=request.form['pic']
        )
        db.session.add(tx)
        db.session.commit()

        flash('Data berhasil disimpan.', 'success')

        action = request.form.get('action')
        if action == 'save_and_add':
            return redirect(url_for('dvor.add_transmission_dvor', nama_stasiun=station.nama_stasiun_dvor))
        else:
            return redirect(url_for('dvor.view_data_dvor'))

    return render_template('dvor/transmission_form_dvor.html', station=station, tx=None)




@dvor_bp.route('/transmission_dvor/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transmission_dvor(id):
    # station
    tx = Transmission_dvor.query.get_or_404(id)
    station = Station_dvor.query.get_or_404(tx.station_dvor_id)
    if request.method == 'POST':
        # station.Stasiun = str(request.form.get('Stasiun')) if request.form.get('Statiun') else None
        # tx.station_id=strrequest.form.getstation.id,
        tx.tx1_power = float(request.form.get('tx1_power')) if request.form.get('tx1_power') else None
        tx.tx1_bearing = float(request.form.get('tx1_bearing')) if request.form.get('tx1_bearing') else None
        tx.tx1_modulasi = float(request.form.get('tx1_modulasi')) if request.form.get('tx1_modulasi') else None
        tx.tx2_power = float(request.form.get('tx2_power')) if request.form.get('tx2_power') else None
        tx.tx2_bearing = float(request.form.get('tx2_bearing')) if request.form.get('tx2_bearing') else None
        tx.tx2_modulasi = float(request.form.get('tx2_modulasi')) if request.form.get('tx2_modulasi') else None
        tx.tanggal = datetime.strptime(request.form.get('tanggal'), '%Y-%m-%d')
        tx.pic = request.form.get('pic')
        
        db.session.commit()
        return redirect(url_for('dvor.view_data_dvor'))
    return render_template('dvor/transmission_form_dvor.html', tx=tx, station=station)

@dvor_bp.route('/transmission_dvor/delete/<int:id>', methods=['GET'])
@login_required
def delete_transmission_dvor(id):
    tx = Transmission_dvor.query.get_or_404(id)
    db.session.delete(tx)
    db.session.commit()
    return redirect(url_for('dvor.view_data_dvor'))

@dvor_bp.route('/station_dvor/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_station_dvor(id):
    station = Station_dvor.query.get_or_404(id)
    if request.method == 'POST':
        station.nama_stasiun_dvor = request.form['nama_stasiun_dvor']
        station.frekuensi_dvor = request.form['frekuensi_dvor']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('dvor/stationform_dvor.html', station=station)


@dvor_bp.route('/station_dvor/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_station_dvor(id):
    station = Station_dvor.query.get_or_404(id)
    Transmission_dvor.query.filter_by(station_dvor_id=station.id).delete()

    db.session.delete(station)
    db.session.commit()
    return redirect(url_for('dvor.stationlist_dvor'))


def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def is_normal_bearing(value):
    if isinstance(value, (int, float)):
        return 1.4 <= value <= 1.6
    if isinstance(value, str):
        value = value.strip().lower()
        return any(k in value for k in ['1.5', 'normal', 'ok'])
    return False


def average(values):
    clean = [v for v in values if isinstance(v, (int, float))]
    return sum(clean) / len(clean) if clean else 0


@dvor_bp.route('/dashboard_dvor', methods=['GET', 'POST'])
@login_required
def dvor_dashboard():
    stations = Station_dvor.query.all()
    selected_station_dvor_id = request.form.get('station_id')
    selected_year = request.form.get('year', type=int)
    selected_month = request.form.get('month', type=int)
    selected_day = request.form.get('day', type=int)

    query = Transmission_dvor.query.join(Station_dvor)
    if selected_station_dvor_id:
        query = query.filter(Transmission_dvor.station_dvor_id == selected_station_dvor_id)
    if selected_year:
        query = query.filter(db.extract('year', Transmission_dvor.tanggal) == selected_year)
    if selected_month:
        query = query.filter(db.extract('month', Transmission_dvor.tanggal) == selected_month)
    if selected_day:
        query = query.filter(db.extract('day', Transmission_dvor.tanggal) == selected_day)

    data = query.add_columns(
        Station_dvor.nama_stasiun_dvor, Station_dvor.frekuensi_dvor,
        Transmission_dvor.tx1_power, Transmission_dvor.tx1_bearing, Transmission_dvor.tx1_modulasi,
        Transmission_dvor.tx2_power, Transmission_dvor.tx2_bearing, Transmission_dvor.tx2_modulasi,
        Transmission_dvor.tanggal, Transmission_dvor.pic
    ).order_by(Transmission_dvor.tanggal).all()

    dates = [row.tanggal.strftime('%Y-%m-%d') for row in data]
    tx1_power = [safe_float(row.tx1_power) for row in data]
    tx2_power = [safe_float(row.tx2_power) for row in data]
    tx1_bearing = [row.tx1_bearing for row in data]
    tx2_bearing = [row.tx2_bearing for row in data]
    tx1_modulasi = [safe_float(row.tx1_modulasi) for row in data]
    tx2_modulasi = [safe_float(row.tx2_modulasi) for row in data]

    fig_power = go.Figure()
    fig_power.add_trace(go.Scatter(x=dates, y=tx1_power, mode='lines+markers', name='TX1 Power'))
    fig_power.add_trace(go.Scatter(x=dates, y=tx2_power, mode='lines+markers', name='TX2 Power'))
    fig_power.update_layout(title='Power Output TX1 & TX2', xaxis_title='Tanggal', yaxis_title='Watt')
    chart_power = pio.to_html(fig_power, full_html=False)

    fig_modulasi = go.Figure()
    fig_modulasi.add_trace(go.Scatter(x=dates, y=tx1_modulasi, mode='lines+markers', name='TX1 Modulasi'))
    fig_modulasi.add_trace(go.Scatter(x=dates, y=tx2_modulasi, mode='lines+markers', name='TX2 Modulasi'))
    fig_modulasi.update_layout(title='Modulasi TX1 & TX2', xaxis_title='Tanggal', yaxis_title='Modulasi')
    chart_modulasi = pio.to_html(fig_modulasi, full_html=False)

    bearing_all = tx1_bearing + tx2_bearing
    bearing_normal = sum(1 for b in bearing_all if is_normal_bearing(b))
    bearing_not_normal = len(bearing_all) - bearing_normal
    fig_bearing = go.Figure(data=[go.Pie(labels=["Normal", "Tidak Normal"], values=[bearing_normal, bearing_not_normal], hole=0.4)])
    fig_bearing.update_layout(title="Bearing Normal vs Tidak Normal")
    chart_bearing = pio.to_html(fig_bearing, full_html=False)

    fig_grouped_dvor = go.Figure()
    fig_grouped_dvor.add_trace(go.Bar(x=dates, y=tx1_power, name='TX1 Power'))
    fig_grouped_dvor.add_trace(go.Bar(x=dates, y=tx2_power, name='TX2 Power'))
    fig_grouped_dvor.update_layout(barmode='group', title="Perbandingan TX1 vs TX2 per Tanggal", xaxis_title="Tanggal", yaxis_title="Watt")
    chart_grouped_dvor = pio.to_html(fig_grouped_dvor, full_html=False)

    avg_by_station = defaultdict(lambda: {'tx1_power': [], 'tx2_power': [], 'tx1_modulasi': [], 'tx2_modulasi': []})
    for row in data:
        key = row.nama_stasiun_dvor
        avg_by_station[key]['tx1_power'].append(safe_float(row.tx1_power))
        avg_by_station[key]['tx2_power'].append(safe_float(row.tx2_power))
        avg_by_station[key]['tx1_modulasi'].append(safe_float(row.tx1_modulasi))
        avg_by_station[key]['tx2_modulasi'].append(safe_float(row.tx2_modulasi))

    station_labels, avg_tx1_power, avg_tx2_power, avg_tx1_modulasi, avg_tx2_modulasi = [], [], [], [], []
    for station, values in avg_by_station.items():
        station_labels.append(station)
        avg_tx1_power.append(average(values['tx1_power']))
        avg_tx2_power.append(average(values['tx2_power']))
        avg_tx1_modulasi.append(average(values['tx1_modulasi']))
        avg_tx2_modulasi.append(average(values['tx2_modulasi']))

    fig_avg_power = go.Figure()
    fig_avg_power.add_trace(go.Bar(x=station_labels, y=avg_tx1_power, name='TX1 Power'))
    fig_avg_power.add_trace(go.Bar(x=station_labels, y=avg_tx2_power, name='TX2 Power'))
    fig_avg_power.update_layout(title='Rata-rata Power per Stasiun', barmode='group', xaxis_title='Stasiun', yaxis_title='Watt')
    chart_avg_power = pio.to_html(fig_avg_power, full_html=False)

    fig_avg_modulasi = go.Figure()
    fig_avg_modulasi.add_trace(go.Bar(x=station_labels, y=avg_tx1_modulasi, name='TX1 Modulasi'))
    fig_avg_modulasi.add_trace(go.Bar(x=station_labels, y=avg_tx2_modulasi, name='TX2 Modulasi'))
    fig_avg_modulasi.update_layout(title='Rata-rata Modulasi per Stasiun', barmode='group', xaxis_title='Stasiun', yaxis_title='Modulasi')
    chart_avg_modulasi = pio.to_html(fig_avg_modulasi, full_html=False)

    pic_counter = Counter(row.pic for row in data)
    pic_labels, pic_values = zip(*pic_counter.items()) if pic_counter else ([], [])

    fig_pic = go.Figure()
    fig_pic.add_trace(go.Bar(x=pic_labels, y=pic_values, marker_color='blue'))
    fig_pic.update_layout(title='PIC Paling Aktif', xaxis_title='PIC', yaxis_title='Jumlah Cek')
    chart_pic = pio.to_html(fig_pic, full_html=False)

    summary = {
        'power_summary': f"TX1 rata-rata {average(tx1_power):.2f} W dan TX2 rata-rata {average(tx2_power):.2f} W" if tx1_power and tx2_power else "Tidak ada data Power",
        'modulasi_summary': f"TX1 Mod% rata-rata {average(tx1_modulasi):.2f}% dan TX2 rata-rata {average(tx2_modulasi):.2f}%" if tx1_modulasi and tx2_modulasi else "Tidak ada data Mod%",
        'bearing_summary': f"{bearing_normal} Normal, {bearing_not_normal} Tidak Normal dari total {len(bearing_all)} entri",
        'pic_summary': f"PIC paling aktif: {pic_labels[pic_values.index(max(pic_values))]} dengan {max(pic_values)} kali pengecekan" if pic_labels else "Tidak ada data PIC"
    }

    years = sorted(set(row.tanggal.year for row in Transmission_dvor.query.all()))

    return render_template(
        'dvor/dashboard_dvor.html',
        data=data,
        chart_power=chart_power,
        chart_modulasi=chart_modulasi,
        chart_bearing=chart_bearing,
        chart_grouped_dvor=chart_grouped_dvor,
        chart_avg_power=chart_avg_power,
        chart_avg_modulasi=chart_avg_modulasi,
        chart_pic=chart_pic,
        stations=stations,
        selected_station_id=selected_station_dvor_id,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_day=selected_day,
        years=years,
        summary=summary
    )

@dvor_bp.route('/export_dvor')
@login_required
def export_csv_dvor():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Stasiun', 'Frekuensi', 'TX1 Power', 'TX1 Bearing', 'TX1 Modulasi', 'TX2 Power', 'TX2 Bearing', 'TX2 Modulasi', 'Tanggal', 'PIC'])

    txs = Transmission_dvor.query.join(Station_dvor).add_columns(
        Station_dvor.nama_stasiun_dvor, Station_dvor.frekuensi_dvor,
        Transmission_dvor.tx1_power, Transmission_dvor.tx1_bearing, Transmission_dvor.tx1_modulasi,
        Transmission_dvor.tx2_power, Transmission_dvor.tx2_bearing, Transmission_dvor.tx2_modulasi,
        Transmission_dvor.tanggal, Transmission_dvor.pic
    ).all()

    for row in txs:
        writer.writerow([
            row.nama_stasiun_dvor, row.frekuensi_dvor,
            row.tx1_power, row.tx1_bearing, row.tx1_modulasi,
            row.tx2_power, row.tx2_bearing, row.tx2_modulasi,
            row.tanggal, row.pic
        ])

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='data_dvor.csv')





