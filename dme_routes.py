from flask import Blueprint, Flask, render_template, request, redirect, url_for, send_file, flash
from flask_login import login_required
from config import Config
from models import Station_dme,  Transmission_dme, db, Station, Transmission
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
from models import Station_dme

dme_bp = Blueprint('dme', __name__)

@dme_bp.route('/station_dme/add', methods=['GET', 'POST'])
@login_required
def add_station_dme():
    if request.method == 'POST':
        nama = request.form['nama_stasiun_dme']
        frek = request.form['frekuensi_dme']
        new_station = Station_dme(nama_stasiun_dme=nama, frekuensi_dme=frek)
        db.session.add(new_station)
        db.session.commit()
        
        # Perbaikan redirect (pakai prefix 'dme.' dan param yang sesuai)
        return redirect(url_for('dme.add_transmission_dme', nama_stasiun=new_station.nama_stasiun_dme))
    
    return render_template('dme/stationform_dme.html')


@dme_bp.route('/stationlist_dme')
@login_required
def stationlist_dme():
    stations = Station_dme.query.all()
    return render_template('dme/stationlist_dme.html', stations=stations)

@dme_bp.route('/data_dme')
@login_required
def view_data_dme():
    stations = Station_dme.query.order_by(Station_dme.nama_stasiun_dme).all()


    grouped_data_dme = []
    for station in stations:
        transmissions = Transmission_dme.query.filter_by(station_dme_id=station.id).all()
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

            grouped_data_dme.append({
                'station_dme': station,
                'per_year': sorted_per_year
            })

    return render_template('dme/data_table_dme.html', grouped_data_dme=grouped_data_dme)


@dme_bp.route('/transmission_dme/add/<path:nama_stasiun>', methods=['GET', 'POST'])
@login_required
def add_transmission_dme(nama_stasiun):
    station = Station_dme.query.filter_by(nama_stasiun_dme=nama_stasiun).first_or_404()

    if request.method == 'POST':
        tx = Transmission_dme(
            station_dme_id=station.id,
            tx1_power=float(request.form.get('tx1_power') or 0),
            tx1_spacing=float(request.form.get('tx1_spacing') or 0),
            tx1_delay=float(request.form.get('tx1_delay') or 0),
            tx2_power=float(request.form.get('tx2_power') or 0),
            tx2_spacing=float(request.form.get('tx2_spacing') or 0),
            tx2_delay=float(request.form.get('tx2_delay') or 0),
            tanggal=datetime.strptime(request.form['tanggal'], '%Y-%m-%d'),
            pic=request.form['pic']
        )
        db.session.add(tx)
        db.session.commit()

        flash('Data berhasil disimpan.', 'success')

        action = request.form.get('action')
        if action == 'save_and_add':
            return redirect(url_for('dme.add_transmission_dme', nama_stasiun=station.nama_stasiun_dme))
        else:
            return redirect(url_for('dme.view_data_dme'))

    return render_template('dme/transmission_form_dme.html', station=station, tx=None)




@dme_bp.route('/transmission_dme/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transmission_dme(id):
    # station
    tx = Transmission_dme.query.get_or_404(id)
    station = Station_dme.query.get_or_404(tx.station_dme_id)
    if request.method == 'POST':
        # station.Stasiun = str(request.form.get('Stasiun')) if request.form.get('Statiun') else None
        # tx.station_id=strrequest.form.getstation.id,
        tx.tx1_power = float(request.form.get('tx1_power')) if request.form.get('tx1_power') else None
        tx.tx1_spacing = float(request.form.get('tx1_spacing')) if request.form.get('tx1_spacing') else None
        tx.tx1_delay = float(request.form.get('tx1_delay')) if request.form.get('tx1_delay') else None
        tx.tx2_power = float(request.form.get('tx2_power')) if request.form.get('tx2_power') else None
        tx.tx2_spacing = float(request.form.get('tx2_spacing')) if request.form.get('tx2_spacing') else None
        tx.tx2_delay = float(request.form.get('tx2_delay')) if request.form.get('tx2_delay') else None
        tx.tanggal = datetime.strptime(request.form.get('tanggal'), '%Y-%m-%d')
        tx.pic = request.form.get('pic')
        
        db.session.commit()
        return redirect(url_for('dme.view_data_dme'))
    return render_template('dme/transmission_form_dme.html', tx=tx, station=station)

@dme_bp.route('/transmission_dme/delete/<int:id>', methods=['GET'])
@login_required
def delete_transmission_dme(id):
    tx = Transmission_dme.query.get_or_404(id)
    db.session.delete(tx)
    db.session.commit()
    return redirect(url_for('dme.view_data_dme'))

@dme_bp.route('/station_dme/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_station_dme(id):
    station = Station_dme.query.get_or_404(id)
    if request.method == 'POST':
        station.nama_stasiun_dme = request.form['nama_stasiun_dme']
        station.frekuensi_dme = request.form['frekuensi_dme']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('dme/stationform_dme.html', station=station)


@dme_bp.route('/station_dme/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_station_dme(id):
    station = Station_dme.query.get_or_404(id)
    Transmission_dme.query.filter_by(station_dme_id=station.id).delete()

    db.session.delete(station)
    db.session.commit()
    return redirect(url_for('dme.stationlist_dme'))


def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def is_normal_spacing(value):
    if isinstance(value, (int, float)):
        return 1.4 <= value <= 1.6
    if isinstance(value, str):
        value = value.strip().lower()
        return any(k in value for k in ['1.5', 'normal', 'ok'])
    return False


def average(values):
    clean = [v for v in values if isinstance(v, (int, float))]
    return sum(clean) / len(clean) if clean else 0


@dme_bp.route('/dashboard_dme', methods=['GET', 'POST'])
@login_required
def dme_dashboard():
    stations = Station_dme.query.all()
    selected_station_dme_id = request.form.get('station_id')
    selected_year = request.form.get('year', type=int)
    selected_month = request.form.get('month', type=int)
    selected_day = request.form.get('day', type=int)

    query = Transmission_dme.query.join(Station_dme)
    if selected_station_dme_id:
        query = query.filter(Transmission_dme.station_dme_id == selected_station_dme_id)
    if selected_year:
        query = query.filter(db.extract('year', Transmission_dme.tanggal) == selected_year)
    if selected_month:
        query = query.filter(db.extract('month', Transmission_dme.tanggal) == selected_month)
    if selected_day:
        query = query.filter(db.extract('day', Transmission_dme.tanggal) == selected_day)

    data = query.add_columns(
        Station_dme.nama_stasiun_dme, Station_dme.frekuensi_dme,
        Transmission_dme.tx1_power, Transmission_dme.tx1_spacing, Transmission_dme.tx1_delay,
        Transmission_dme.tx2_power, Transmission_dme.tx2_spacing, Transmission_dme.tx2_delay,
        Transmission_dme.tanggal, Transmission_dme.pic
    ).order_by(Transmission_dme.tanggal).all()

    dates = [row.tanggal.strftime('%Y-%m-%d') for row in data]
    tx1_power = [safe_float(row.tx1_power) for row in data]
    tx2_power = [safe_float(row.tx2_power) for row in data]
    tx1_spacing = [row.tx1_spacing for row in data]
    tx2_spacing = [row.tx2_spacing for row in data]
    tx1_delay = [safe_float(row.tx1_delay) for row in data]
    tx2_delay = [safe_float(row.tx2_delay) for row in data]

    fig_power = go.Figure()
    fig_power.add_trace(go.Scatter(x=dates, y=tx1_power, mode='lines+markers', name='TX1 Power'))
    fig_power.add_trace(go.Scatter(x=dates, y=tx2_power, mode='lines+markers', name='TX2 Power'))
    fig_power.update_layout(title='Power Output TX1 & TX2', xaxis_title='Tanggal', yaxis_title='Watt')
    chart_power = pio.to_html(fig_power, full_html=False)

    fig_delay = go.Figure()
    fig_delay.add_trace(go.Scatter(x=dates, y=tx1_delay, mode='lines+markers', name='TX1 delay'))
    fig_delay.add_trace(go.Scatter(x=dates, y=tx2_delay, mode='lines+markers', name='TX2 delay'))
    fig_delay.update_layout(title='delay TX1 & TX2', xaxis_title='Tanggal', yaxis_title='delay')
    chart_delay = pio.to_html(fig_delay, full_html=False)

    spacing_all = tx1_spacing + tx2_spacing
    spacing_normal = sum(1 for b in spacing_all if is_normal_spacing(b))
    spacing_not_normal = len(spacing_all) - spacing_normal
    fig_spacing = go.Figure(data=[go.Pie(labels=["Normal", "Tidak Normal"], values=[spacing_normal, spacing_not_normal], hole=0.4)])
    fig_spacing.update_layout(title="spacing Normal vs Tidak Normal")
    chart_spacing = pio.to_html(fig_spacing, full_html=False)

    fig_grouped_dme = go.Figure()
    fig_grouped_dme.add_trace(go.Bar(x=dates, y=tx1_power, name='TX1 Power'))
    fig_grouped_dme.add_trace(go.Bar(x=dates, y=tx2_power, name='TX2 Power'))
    fig_grouped_dme.update_layout(barmode='group', title="Perbandingan TX1 vs TX2 per Tanggal", xaxis_title="Tanggal", yaxis_title="Watt")
    chart_grouped_dme = pio.to_html(fig_grouped_dme, full_html=False)

    avg_by_station = defaultdict(lambda: {'tx1_power': [], 'tx2_power': [], 'tx1_delay': [], 'tx2_delay': []})
    for row in data:
        key = row.nama_stasiun_dme
        avg_by_station[key]['tx1_power'].append(safe_float(row.tx1_power))
        avg_by_station[key]['tx2_power'].append(safe_float(row.tx2_power))
        avg_by_station[key]['tx1_delay'].append(safe_float(row.tx1_delay))
        avg_by_station[key]['tx2_delay'].append(safe_float(row.tx2_delay))

    station_labels, avg_tx1_power, avg_tx2_power, avg_tx1_delay, avg_tx2_delay = [], [], [], [], []
    for station, values in avg_by_station.items():
        station_labels.append(station)
        avg_tx1_power.append(average(values['tx1_power']))
        avg_tx2_power.append(average(values['tx2_power']))
        avg_tx1_delay.append(average(values['tx1_delay']))
        avg_tx2_delay.append(average(values['tx2_delay']))

    fig_avg_power = go.Figure()
    fig_avg_power.add_trace(go.Bar(x=station_labels, y=avg_tx1_power, name='TX1 Power'))
    fig_avg_power.add_trace(go.Bar(x=station_labels, y=avg_tx2_power, name='TX2 Power'))
    fig_avg_power.update_layout(title='Rata-rata Power per Stasiun', barmode='group', xaxis_title='Stasiun', yaxis_title='Watt')
    chart_avg_power = pio.to_html(fig_avg_power, full_html=False)

    fig_avg_delay = go.Figure()
    fig_avg_delay.add_trace(go.Bar(x=station_labels, y=avg_tx1_delay, name='TX1 delay'))
    fig_avg_delay.add_trace(go.Bar(x=station_labels, y=avg_tx2_delay, name='TX2 delay'))
    fig_avg_delay.update_layout(title='Rata-rata delay per Stasiun', barmode='group', xaxis_title='Stasiun', yaxis_title='delay')
    chart_avg_delay = pio.to_html(fig_avg_delay, full_html=False)

    pic_counter = Counter(row.pic for row in data)
    pic_labels, pic_values = zip(*pic_counter.items()) if pic_counter else ([], [])

    fig_pic = go.Figure()
    fig_pic.add_trace(go.Bar(x=pic_labels, y=pic_values, marker_color='blue'))
    fig_pic.update_layout(title='PIC Paling Aktif', xaxis_title='PIC', yaxis_title='Jumlah Cek')
    chart_pic = pio.to_html(fig_pic, full_html=False)

    summary = {
        'power_summary': f"TX1 rata-rata {average(tx1_power):.2f} W dan TX2 rata-rata {average(tx2_power):.2f} W" if tx1_power and tx2_power else "Tidak ada data Power",
        'delay_summary': f"TX1 Mod% rata-rata {average(tx1_delay):.2f}% dan TX2 rata-rata {average(tx2_delay):.2f}%" if tx1_delay and tx2_delay else "Tidak ada data Mod%",
        'spacing_summary': f"{spacing_normal} Normal, {spacing_not_normal} Tidak Normal dari total {len(spacing_all)} entri",
        'pic_summary': f"PIC paling aktif: {pic_labels[pic_values.index(max(pic_values))]} dengan {max(pic_values)} kali pengecekan" if pic_labels else "Tidak ada data PIC"
    }

    years = sorted(set(row.tanggal.year for row in Transmission_dme.query.all()))

    return render_template(
        'dme/dashboard_dme.html',
        data=data,
        chart_power=chart_power,
        chart_delay=chart_delay,
        chart_spacing=chart_spacing,
        chart_grouped_dme=chart_grouped_dme,
        chart_avg_power=chart_avg_power,
        chart_avg_delay=chart_avg_delay,
        chart_pic=chart_pic,
        stations=stations,
        selected_station_id=selected_station_dme_id,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_day=selected_day,
        years=years,
        summary=summary
    )

@dme_bp.route('/export_dme')
@login_required
def export_csv_dme():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Stasiun', 'Frekuensi', 'TX1 Power', 'TX1 spacing', 'TX1 delay', 'TX2 Power', 'TX2 spacing', 'TX2 delay', 'Tanggal', 'PIC'])

    txs = Transmission_dme.query.join(Station_dme).add_columns(
        Station_dme.nama_stasiun_dme, Station_dme.frekuensi_dme,
        Transmission_dme.tx1_power, Transmission_dme.tx1_spacing, Transmission_dme.tx1_delay,
        Transmission_dme.tx2_power, Transmission_dme.tx2_spacing, Transmission_dme.tx2_delay,
        Transmission_dme.tanggal, Transmission_dme.pic
    ).all()

    for row in txs:
        writer.writerow([
            row.nama_stasiun_dme, row.frekuensi_dme,
            row.tx1_power, row.tx1_spacing, row.tx1_delay,
            row.tx2_power, row.tx2_spacing, row.tx2_delay,
            row.tanggal, row.pic
        ])

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='data_dme.csv')





