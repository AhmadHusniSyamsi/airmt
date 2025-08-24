from collections import defaultdict
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import Transmission_Gp, Transmission_Localizer, Transmission_Tdme, Station_ils, Transmission_Gp, Transmission_Localizer, db, Transmission_Tdme
from datetime import datetime
import plotly.graph_objs as go
import plotly.io as pio

ils_bp = Blueprint('ils', __name__, url_prefix='/ils')

# @ils_bp.route('/<lokasi>')
# def dashboard_ils(lokasi):
#     gp_data = Transmission_Gp.query.filter_by(lokasi=lokasi).all()
#     localizer_data = Transmission_Localizer.query.filter_by(lokasi=lokasi).all()
#     tdme_data = Transmission_Tdme.query.filter_by(lokasi=lokasi).all()
#     return render_template('dashboard_ils.html', lokasi=lokasi, gp_data=gp_data, localizer_data=localizer_data, tdme_data=tdme_data)

@ils_bp.route('/data_table_ils')
@login_required
def data_table_ils():
    ils_data = Station_ils.query.all()
    return render_template('data_table_ils.html', ils_data=ils_data)

@ils_bp.route('/data_table')
@login_required
def view_data_ils():
    # Ambil semua data Station_ils
    stations = Station_ils.query.all()

    combined_data = []
    for station in stations:
        gp = station.gp
        loc = station.localizer
        tdme = station.tdme

        data = {
            'id': station.id,
            'lokasi': station.lokasi_stasiun_ils,
            'tanggal': station.tanggal.strftime('%Y-%m-%d'),
            'pic': station.pic,

            # Data G/P
            'gp_csb_power': gp.csb_power if gp else None,
            'gp_sbo_power': gp.sbo_power if gp else None,
            'gp_sdm_80': gp.sdm_80 if gp else None,
            'gp_course_ddm': gp.course_ddm if gp else None,
            'gp_ds_ddm': gp.ds_ddm if gp else None,
            'gp_clr_ddm': gp.clr_ddm if gp else None,

            # Data Localizer
            'loc_csb_power': loc.csb_power if loc else None,
            'loc_sbo_power': loc.sbo_power if loc else None,
            'loc_sdm_40': loc.sdm_40 if loc else None,
            'loc_course_ddm': loc.course_ddm if loc else None,
            'loc_ds_ddm': loc.ds_ddm if loc else None,
            'loc_clr_ddm': loc.clr_ddm if loc else None,

            # Data TDME
            'tdme_tx1_power': tdme.tx1_power if tdme else None,
            'tdme_spacing1': tdme.spacing1 if tdme else None,
            'tdme_delay1': tdme.delay1 if tdme else None,
            'tdme_tx2_power': tdme.tx2_power if tdme else None,
            'tdme_spacing2': tdme.spacing2 if tdme else None,
            'tdme_delay2': tdme.delay2 if tdme else None,
        }

        combined_data.append(data)

    return render_template('ils/data_table.html', combined_data=combined_data)


@ils_bp.route('/dashboard_ils')
@login_required
def dashboard_ils():
    lokasi = request.args.get('lokasi')
    tanggal = request.args.get('tanggal')

    query = Station_ils.query

    if lokasi:
        query = query.filter_by(lokasi_stasiun_ils=lokasi)
    if tanggal:
        try:
            tanggal_obj = datetime.strptime(tanggal, '%Y-%m-%d').date()
            query = query.filter_by(tanggal=tanggal_obj)
        except ValueError:
            flash("Format tanggal tidak valid.", "danger")

    stations = query.all()

    # Ambil semua transmission dari relasi
    gp_data = [s.gp for s in stations if s.gp]
    localizer_data = [s.localizer for s in stations if s.localizer]
    tdme_data = [s.tdme for s in stations if s.tdme]

    # Contoh visualisasi: CSB Power G/P
    chart_gp = go.Figure()
    chart_gp.add_trace(go.Scatter(
        x=[s.ils.tanggal.strftime('%Y-%m-%d') for s in gp_data],
        y=[s.csb_power for s in gp_data],
        mode='lines+markers',
        name='CSB Power (G/P)'
    ))
    chart_gp.update_layout(title='Grafik CSB Power G/P', xaxis_title='Tanggal', yaxis_title='CSB Power')
    chart_gp = pio.to_html(chart_gp, full_html=False)

    # Localizer
    chart_localizer = go.Figure()
    chart_localizer.add_trace(go.Bar(
        x=[s.ils.tanggal.strftime('%Y-%m-%d') for s in localizer_data],
        y=[s.csb_power for s in localizer_data],
        name='CSB Power (Localizer)'
    ))
    chart_localizer.update_layout(title='Grafik CSB Power Localizer', xaxis_title='Tanggal', yaxis_title='CSB Power')
    chart_localizer = pio.to_html(chart_localizer, full_html=False)

    # TDME
    chart_tdme = go.Figure()
    chart_tdme.add_trace(go.Scatter(
        x=[s.ils.tanggal.strftime('%Y-%m-%d') for s in tdme_data],
        y=[s.tx1_power for s in tdme_data],
        mode='lines+markers',
        name='TX1 Power (TDME)'
    ))
    chart_tdme.update_layout(title='Grafik TX1 Power TDME', xaxis_title='Tanggal', yaxis_title='TX1 Power')
    chart_tdme = pio.to_html(chart_tdme, full_html=False)

    return render_template(
        'dashboard_ils.html',
        chart_gp=chart_gp,
        chart_localizer=chart_localizer,
        chart_tdme=chart_tdme,
        count_gp=len(gp_data),
        count_localizer=len(localizer_data),
        count_tdme=len(tdme_data)
    )

@ils_bp.route('/ils/add', methods=['GET', 'POST'])
@login_required
def add_transmission_ils():
    if request.method == 'POST':
        # Station ILS
        lokasi = request.form['lokasi']
        tanggal = datetime.strptime(request.form['tanggal'], '%Y-%m-%d')
        pic = request.form['pic']
        station = Station_ils(lokasi_stasiun_ils=lokasi, tanggal=tanggal, pic=pic)
        db.session.add(station)
        db.session.flush()

        # G/P
        gp = Transmission_Gp(
            csb_power=request.form['gp_csb_power'],
            sbo_power=request.form['gp_sbo_power'],
            sdm_80=request.form['gp_sdm_80'],
            course_ddm=request.form['gp_course_ddm'],
            ds_ddm=request.form['gp_ds_ddm'],
            clr_ddm=request.form['gp_clr_ddm'],
            station_ils_id=station.id
        )
        db.session.add(gp)

        # Localizer
        loc = Transmission_Localizer(
            csb_power=request.form['loc_csb_power'],
            sbo_power=request.form['loc_sbo_power'],
            sdm_40=request.form['loc_sdm_40'],
            course_ddm=request.form['loc_course_ddm'],
            ds_ddm=request.form['loc_ds_ddm'],
            clr_ddm=request.form['loc_clr_ddm'],
            station_ils_id=station.id
        )
        db.session.add(loc)

        # TDME
        tdme = Transmission_Tdme(
            tx1_power=request.form['tdme_tx1_power'],
            spacing1=request.form['tdme_spacing1'],
            delay1=request.form['tdme_delay1'],
            tx2_power=request.form['tdme_tx2_power'],
            spacing2=request.form['tdme_spacing2'],
            delay2=request.form['tdme_delay2'],
            station_ils_id=station.id
        )
        db.session.add(tdme)

        db.session.commit()
        flash('Data berhasil disimpan.', 'success')
        return redirect(url_for('ils.view_data_ils'))

    return render_template('ils/transmission_form_ils.html', form_title='Tambah Data ILS', data=None)

@ils_bp.route('/ils/transmission/<int:station_id>', methods=['GET', 'POST'])
@login_required
def edit_transmission_ils(station_id):
    station = Station_ils.query.get_or_404(station_id)

    gp = station.gp or Transmission_Gp(station_ils_id=station.id)
    loc = station.localizer or Transmission_Localizer(station_ils_id=station.id)
    tdme = station.tdme or Transmission_Tdme(station_ils_id=station.id)

    if request.method == 'POST':
        # G/P
        gp.csb_power = request.form.get('gp_csb_power')
        gp.sbo_power = request.form.get('gp_sbo_power')
        gp.sdm_80 = request.form.get('gp_sdm_80')
        gp.course_ddm = request.form.get('gp_course_ddm')
        gp.ds_ddm = request.form.get('gp_ds_ddm')
        gp.clr_ddm = request.form.get('gp_clr_ddm')

        # Localizer
        loc.csb_power = request.form.get('loc_csb_power')
        loc.sbo_power = request.form.get('loc_sbo_power')
        loc.sdm_40 = request.form.get('loc_sdm_40')
        loc.course_ddm = request.form.get('loc_course_ddm')
        loc.ds_ddm = request.form.get('loc_ds_ddm')
        loc.clr_ddm = request.form.get('loc_clr_ddm')

        # TDME
        tdme.tx1_power = request.form.get('tdme_tx1_power')
        tdme.spacing1 = request.form.get('tdme_spacing1')
        tdme.delay1 = request.form.get('tdme_delay1')
        tdme.tx2_power = request.form.get('tdme_tx2_power')
        tdme.spacing2 = request.form.get('tdme_spacing2')
        tdme.delay2 = request.form.get('tdme_delay2')

        db.session.add_all([gp, loc, tdme])
        db.session.commit()

        flash('Data transmisi ILS berhasil disimpan', 'success')
        return redirect(url_for('ils.view_data_ils'))

    transmission = {
        'gp_csb_power': gp.csb_power,
        'gp_sbo_power': gp.sbo_power,
        'gp_sdm_80': gp.sdm_80,
        'gp_course_ddm': gp.course_ddm,
        'gp_ds_ddm': gp.ds_ddm,
        'gp_clr_ddm': gp.clr_ddm,
        'loc_csb_power': loc.csb_power,
        'loc_sbo_power': loc.sbo_power,
        'loc_sdm_40': loc.sdm_40,
        'loc_course_ddm': loc.course_ddm,
        'loc_ds_ddm': loc.ds_ddm,
        'loc_clr_ddm': loc.clr_ddm,
        'tdme_tx1_power': tdme.tx1_power,
        'tdme_spacing1': tdme.spacing1,
        'tdme_delay1': tdme.delay1,
        'tdme_tx2_power': tdme.tx2_power,
        'tdme_spacing2': tdme.spacing2,
        'tdme_delay2': tdme.delay2
    }

    return render_template('ils/transmission_form_ils.html', transmission=transmission, form_title="Edit Data Transmisi")

