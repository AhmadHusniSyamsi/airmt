

from collections import defaultdict
from typing import Counter
from flask import Blueprint, render_template, request, redirect, url_for, send_file, flash
from flask_login import login_required
from numpy import extract
from models import Station_radar, Transmission_radar, db
from datetime import datetime
import plotly.graph_objs as go
import plotly.io as pio
import io
import csv

radar_bp = Blueprint('radar', __name__)

@radar_bp.route('/station_radar/add', methods=['GET', 'POST'])
@login_required
def add_station_radar():
    if request.method == 'POST':
        nama = request.form['nama_stasiun_radar']
        frek = request.form['frekuensi_radar']
        new_station = Station_radar(nama_stasiun_radar=nama, frekuensi_radar=frek)
        db.session.add(new_station)
        db.session.commit()
        return redirect(url_for('radar.add_transmission_radar', nama_stasiun=nama))
    return render_template('radar/stationform_radar.html')

@radar_bp.route('/stationlist_radar')
@login_required
def stationlist_radar():
    stations = Station_radar.query.all()
    return render_template('radar/stationlist_radar.html', stations=stations)

@radar_bp.route('/transmission_radar/add/<path:nama_stasiun>', methods=['GET', 'POST'])
@login_required
def add_transmission_radar(nama_stasiun):
    station = Station_radar.query.filter_by(nama_stasiun_radar=nama_stasiun).first_or_404()
    if request.method == 'POST':
        tx = Transmission_radar(
            station_radar_id=station.id,
            power_forward=float(request.form.get('power_forward') or 0),
            azimuth_ilan=float(request.form.get('azimuth_ilan') or 0),
            power_reflected=float(request.form.get('power_reflected') or 0),
            integration_mod_a=float(request.form.get('integration_mod_a') or 0),
            integration_mod_c=float(request.form.get('integration_mod_c') or 0),
            mod_s_p1=float(request.form.get('mod_s_p1') or 0),
            mod_s_p2=float(request.form.get('mod_s_p2') or 0),
            mod_s_pg=float(request.form.get('mod_s_pg') or 0),
            tanggal=datetime.strptime(request.form.get('tanggal', ''), '%Y-%m-%d'),
            pic=request.form['pic']
        )
        db.session.add(tx)
        db.session.commit()

        flash('Data berhasil disimpan.', 'success')
        if request.form.get('action') == 'save_and_add':
            return redirect(url_for('radar.add_transmission_radar', nama_stasiun=station.nama_stasiun_radar))
        else:
            return redirect(url_for('radar.view_data_radar'))
    return render_template('radar/transmission_form_radar.html', station=station, tx=None)

@radar_bp.route('/data_radar')
@login_required
def view_data_radar():
    stations = Station_radar.query.order_by(Station_radar.nama_stasiun_radar).all()
    grouped_data_radar = []
    for station in stations:
        transmissions = Transmission_radar.query.filter_by(station_radar_id=station.id).all()
        if transmissions:
            per_year = defaultdict(list)
            for tx in transmissions:
                year = tx.tanggal.year
                per_year[year].append(tx)
            grouped_data_radar.append({
                'station_radar': station,
                'per_year': per_year
            })
    return render_template('radar/data_table_radar.html', grouped_data_radar=grouped_data_radar)

@radar_bp.route('/transmission_radar/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transmission_radar(id):
    tx = Transmission_radar.query.get_or_404(id)
    station = Station_radar.query.get_or_404(tx.station_radar_id)
    if request.method == 'POST':
        tx.power_forward = float(request.form.get('power_forward') or 0)
        tx.azimuth_ilan = float(request.form.get('azimuth_ilan') or 0)
        tx.power_reflected = float(request.form.get('power_reflected') or 0)
        tx.integration_mod_a = float(request.form.get('integration_mod_a') or 0)
        tx.integration_mod_c = float(request.form.get('integration_mod_c') or 0)
        tx.mod_s_p1 = float(request.form.get('mod_s_p1') or 0)
        tx.mod_s_p2 = float(request.form.get('mod_s_p2') or 0)
        tx.mod_s_pg = float(request.form.get('mod_s_pg') or 0)
        tx.tanggal = datetime.strptime(request.form['tanggal'], '%Y-%m-%d')
        tx.pic = request.form['pic']
        db.session.commit()
        return redirect(url_for('radar.view_data_radar'))
    return render_template('radar/transmission_form_radar.html', tx=tx, station=station)

@radar_bp.route('/transmission_radar/delete/<int:id>')
@login_required
def delete_transmission_radar(id):
    tx = Transmission_radar.query.get_or_404(id)
    db.session.delete(tx)
    db.session.commit()
    return redirect(url_for('radar.view_data_radar'))

@radar_bp.route('/station_radar/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_station_radar(id):
    station = Station_radar.query.get_or_404(id)
    if request.method == 'POST':
        station.nama_stasiun_radar = request.form['nama_stasiun_radar']
        station.frekuensi_radar = request.form['frekuensi_radar']
        db.session.commit()
        return redirect(url_for('radar.stationlist_radar'))
    return render_template('radar/stationform_radar.html', station=station)

@radar_bp.route('/station_radar/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_station_radar(id):
    station = Station_radar.query.get_or_404(id)
    Transmission_radar.query.filter_by(station_radar_id=station.id).delete()
    db.session.delete(station)
    db.session.commit()
    return redirect(url_for('radar.stationlist_radar'))

@radar_bp.route('/dashboard_radar', methods=['GET', 'POST'])
@login_required
def radar_dashboard():
    selected_station = request.form.get('station_radar_id')
    selected_month = request.form.get('month')
    selected_year = request.form.get('year')

    query = Transmission_radar.query
    if selected_station:
        query = query.join(Station_radar).filter(Station_radar.nama_stasiun_radar == selected_station)
    if selected_month:
        query = query.filter(extract('month', Transmission_radar.tanggal) == int(selected_month))
    if selected_year:
        query = query.filter(extract('year', Transmission_radar.tanggal) == int(selected_year))


    transmissions = query.order_by(Transmission_radar.tanggal.asc()).all()

    # data = query.add_columns(
    #     Station_radar.nama_stasiun_radar, Station_radar.frekuensi_radar, Transmission_radar.power_forward, Transmission_radar.azimuth_ilan, Transmission_radar.power_reflected, Transmission_radar.integration_mod_a, Transmission_radar.integration_mod_c, Transmission_radar.mod_s_p1, Transmission_radar.mod_s_p2, Transmission_radar.mod_s_pg, Transmission_radar.tanggal, Transmission_radar.pic).order_by(Transmission_radar.tanggal).all()
    

    dates = [t.tanggal for t in transmissions]
    power_forward = [t.power_forward for t in transmissions]
    azimuth_ilan = [t.azimuth_ilan for t in transmissions]
    power_reflected = [t.power_reflected for t in transmissions]
    mod_a = [t.integration_mod_a for t in transmissions]
    mod_c = [t.integration_mod_c for t in transmissions]
    mod_s_p1 = [t.mod_s_p1 for t in transmissions]
    mod_s_p2 = [t.mod_s_p2 for t in transmissions]
    mod_s_pg = [t.mod_s_pg for t in transmissions]

    def create_chart(y_data, title, y_label):
        return go.Figure(data=[
            go.Scatter(x=dates, y=y_data, mode='lines+markers')
        ], layout=go.Layout(
            title=title,
            xaxis=dict(title='Tanggal'),
            yaxis=dict(title=y_label)
        ))

    chart_pf = create_chart(power_forward, 'Power Forward', 'dB')
    chart_azimuth = create_chart(azimuth_ilan, 'Azimuth ILAN', '°')
    chart_reflected = create_chart(power_reflected, 'Power Reflected', 'dB')
    chart_mod_a = create_chart(mod_a, 'Integration MOD A', 'ms')
    chart_mod_c = create_chart(mod_c, 'Integration MOD C', 'ms')
    chart_mod_s_p1 = create_chart(mod_s_p1, 'MOD S P1', 'ms')
    chart_mod_s_p2 = create_chart(mod_s_p2, 'MOD S P2', 'ms')
    chart_mod_s_pg = create_chart(mod_s_pg, 'MOD S PG', 'ms')

    def safe_avg(data):
        filtered = [v for v in data if v is not None]
        return round(sum(filtered) / max(len(filtered), 1), 2)

    avg_pf = safe_avg(power_forward)
    avg_azimuth = safe_avg(azimuth_ilan)
    avg_reflected = safe_avg(power_reflected)
    avg_mod_a = safe_avg(mod_a)
    avg_mod_c = safe_avg(mod_c)
    avg_mod_s_p1 = safe_avg(mod_s_p1)
    avg_mod_s_p2 = safe_avg(mod_s_p2)
    avg_mod_s_pg = safe_avg(mod_s_pg)


    # Summary Teks
    summary_text = f"""
    Rata-rata Power Forward sebesar {avg_pf} dB menunjukkan daya keluaran dari pemancar radar. 
    Nilai Azimuth ILAN rata-rata adalah {avg_azimuth}°, mencerminkan arah pergerakan antena. 
    Rata-rata Power reflected sebesar {avg_reflected} dB menunjukkan daya pantulan sinyal radar yang diterima kembali. 
    Integrasi waktu modulasi menunjukkan rata-rata {avg_mod_a} ms untuk MOD A, {avg_mod_c} ms untuk MOD C, 
    dan {avg_mod_s_p1} ms untuk MOD S, yang menunjukkan kestabilan dan durasi respon radar terhadap sinyal masing-masing mode.
    """

    stations = Station_radar.query.all()

    return render_template ('radar/dashboard_radar.html',
        transmissions=transmissions,                    
        chart_pf=chart_pf.to_html(full_html=False),
        chart_azimuth=chart_azimuth.to_html(full_html=False),
        chart_reflected=chart_reflected.to_html(full_html=False),
        chart_mod_a=chart_mod_a.to_html(full_html=False),
        chart_mod_c=chart_mod_c.to_html(full_html=False),
        chart_mod_s_p1=chart_mod_s_p1.to_html(full_html=False),
        chart_mod_s_p2=chart_mod_s_p2.to_html(full_html=False),
        chart_mod_s_pg=chart_mod_s_pg.to_html(full_html=False),
        avg_pf=avg_pf,
        avg_azimuth=avg_azimuth,
        avg_reflected=avg_reflected,
        avg_mod_a=avg_mod_a,
        avg_mod_c=avg_mod_c,
        avg_mod_s_p1 = avg_mod_s_p1,
        avg_mod_s_p2 = avg_mod_s_p2,
        avg_mod_s_pg = avg_mod_s_pg,
        summary_text=summary_text,
        stations=stations,
        selected_station_radar_id=selected_station,
        selected_month=selected_month,
        selected_year=selected_year
    )




@radar_bp.route('/export_radar')
@login_required
def export_csv_radar():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Stasiun', 'Frekuensi', 'Power Forward', 'Azimuth ILAN', 'Power Reflected',
        'Integration MOD A', 'Integration MOD C', 'Mod S P1', 'Mod S P2', 'Mod S PG', 'Tanggal', 'PIC'
    ])

    txs = Transmission_radar.query.join(Station_radar).add_columns(
        Station_radar.nama_stasiun_radar, Station_radar.frekuensi_radar,
        Transmission_radar.power_forward, Transmission_radar.azimuth_ilan, Transmission_radar.power_reflected,
        Transmission_radar.integration_mod_a, Transmission_radar.integration_mod_c,
        Transmission_radar.mod_s_p1, Transmission_radar.mod_s_p2, Transmission_radar.mod_s_pg,
        Transmission_radar.tanggal, Transmission_radar.pic
    ).all()

    for row in txs:
        writer.writerow([
            row.nama_stasiun_radar, row.frekuensi_radar,
            row.power_forward, row.azimuth_ilan, row.power_reflected,
            row.integration_mod_a, row.integration_mod_c,
            row.mod_s_p1, row.mod_s_p2, row.mod_s_pg,
            row.tanggal, row.pic
        ])

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='data_radar.csv')
