from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import GroundCheck, GroundCheckRow

groundcheck_bp = Blueprint("groundcheck", __name__)

# ============================
# Helper
# ============================
def to_float(val):
    """Convert string ke float atau None kalau kosong."""
    if not val or val.strip() == "":
        return None
    try:
        return float(val)
    except ValueError:
        return None


# ============================
# Input Ground Check
# ============================
@groundcheck_bp.route("/llz/ground_check", methods=["GET", "POST"])
@login_required
def ground_check():
    if request.method == "POST":
        lokasi = request.form.get("lokasi")
        tanggal = datetime.strptime(request.form.get("tanggal"), "%Y-%m-%d")
        teknisi = ", ".join(request.form.getlist("teknisi[]"))
        catatan = request.form.get("catatan")
        manager_tujuan = request.form.get("manager_tujuan")
        # Simpan data utama
        gc = GroundCheck(lokasi=lokasi, tanggal=tanggal, teknisi=teknisi, catatan=catatan, manager_tujuan=manager_tujuan, )
        db.session.add(gc)
        db.session.commit()  # commit dulu supaya gc.id terbentuk

        # ==== DATA TABEL ====
        freq_list = ["90 Hz"] * 8 + ["Center"] + ["150 Hz"] * 8
        jarak_list = [
            "210.1","173.2","139.9","109.2","80.4","52.9","26.2","9.7",
            "0",
            "9.7","26.2","52.9","80.4","109.2","139.9","173.2","210.1"
        ]
        degree_list = [
            "35","30","25","20","15","10","5","1.85",
            "0",
            "1.85","5","10","15","20","25","30","35"
        ]


        for idx, (freq, jarak, degree) in enumerate(zip(freq_list, jarak_list, degree_list)):
            row_data = {}
            for col in range(12):
                
                if freq == "90 Hz":
                    field_name = f"hz90_{idx}_{col}"
                elif freq == "Center":
                    field_name = f"center_{idx}_{col}"
                else:  
                    field_name = f"hz150_{idx}_{col}"

                value = request.form.get(field_name)
                row_data[col] = value if value not in [None, ""] else None


            row = GroundCheckRow(
                groundcheck_id=gc.id,
                freq=freq,
                jarak=jarak,
                degree=degree,
                tx1_ddm_persen=row_data[0],
                tx1_ddm_ua=row_data[1],
                tx1_sum=row_data[2],
                tx1_mod90=row_data[3],
                tx1_mod150=row_data[4],
                tx1_rf=row_data[5],
                tx2_ddm_persen=row_data[6],
                tx2_ddm_ua=row_data[7],
                tx2_sum=row_data[8],
                tx2_mod90=row_data[9],
                tx2_mod150=row_data[10],
                tx2_rf=row_data[11],
            )
            db.session.add(row)

        db.session.commit()
        return redirect(url_for("groundcheck.detail_data", id=gc.id))

    return render_template("llz/ground_check.html")


# ============================
# Lihat Semua Data
# ============================
@groundcheck_bp.route("/lihat_data")
@login_required
def lihat_data():
    # Mapping manager (username -> format manager teknik di database)
    manager_mapping = {
        "agus dermawan m": "Manager Teknik 1 Agus Dermawan M",
        "andi wibowo": "Manager Teknik 2 Andi Wibowo",
        "efried n.p": "Manager Teknik 3 Efried N.P",
        "moch ichsan": "Manager Teknik 4 Moch Ichsan",
        "netty septa c": "Manager Teknik 5 Netty Septa C",
    }

    username = current_user.username.lower()

    if username in manager_mapping:
        # Manager hanya bisa lihat data yang ditujukan padanya
        ground_check = GroundCheck.query.filter_by(manager_tujuan=manager_mapping[username]).all()
    else:
        # User lain (teknisi) bisa lihat semua data
        ground_check = GroundCheck.query.all()

    return render_template("llz/lihat_data.html", ground_check=ground_check)

# ============================
# ACC Data (pakai username)
# ============================
@groundcheck_bp.route("/acc/<int:id>", methods=["POST"])
@login_required
def acc(id):
    record = GroundCheck.query.get_or_404(id)

    # Daftar username manager yang boleh ACC
    allowed_usernames = ["andi wibowo", "agus dermawan m", "efried n.p", "netty septa c"]

    if current_user.username.lower() not in allowed_usernames:
        flash("Anda tidak punya izin untuk ACC!", "danger")
        return redirect(url_for("groundcheck.cek_status"))

    record.status = "Selesai"
    record.manager = current_user.username  # simpan nama manager sesuai login
    db.session.commit()

    flash(f"Ground Check berhasil di-ACC oleh {current_user.username}", "success")
    return redirect(url_for("groundcheck.cek_status"))


# ============================
# Cek Status
# ============================
@groundcheck_bp.route("/llz/cek_status")
@login_required
def cek_status():
    records = GroundCheck.query.all()  # Ambil semua data
    return render_template("llz/cek_status.html", ground_check=records)


# ============================
# Edit Ground Check
# ============================
@groundcheck_bp.route("/llz/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_ground_check(id):
    gc = GroundCheck.query.get_or_404(id)

    if request.method == "POST":
        gc.lokasi = request.form.get("lokasi")
        gc.tanggal = datetime.strptime(request.form.get("tanggal"), "%Y-%m-%d")
        gc.teknisi = ", ".join(request.form.getlist("teknisi[]"))
        gc.catatan = request.form.get("catatan")

        # Hapus semua row lama
        GroundCheckRow.query.filter_by(groundcheck_id=gc.id).delete()

        freq_list = ["90 Hz"] * 8 + ["Center"] + ["150 Hz"] * 8
        jarak_list = [
            "210.1","173.2","139.9","109.2","80.4","52.9","26.2","9.7",
            "0",
            "9.7","26.2","52.9","80.4","109.2","139.9","173.2","210.1"
        ]
        degree_list = [
            "35","30","25","20","15","10","5","1.85",
            "0",
            "1.85","5","10","15","20","25","30","35"
        ]

        for row_idx, (freq, jarak, degree) in enumerate(zip(freq_list, jarak_list, degree_list)):

            if freq == "90 Hz":
                prefix = f"hz90_{row_idx}_"
            elif freq == "150 Hz":
                prefix = f"hz150_{row_idx}_"
            else:  # Center
                prefix = "center_0_"

            values = [to_float(request.form.get(prefix + str(i))) for i in range(12)]

            row = GroundCheckRow(
                groundcheck_id=gc.id,
                freq=freq,
                jarak=jarak,
                degree=degree,
                tx1_ddm_persen=values[0],
                tx1_ddm_ua=values[1],
                tx1_sum=values[2],
                tx1_mod90=values[3],
                tx1_mod150=values[4],
                tx1_rf=values[5],
                tx2_ddm_persen=values[6],
                tx2_ddm_ua=values[7],
                tx2_sum=values[8],
                tx2_mod90=values[9],
                tx2_mod150=values[10],
                tx2_rf=values[11],
            )
            db.session.add(row)

        db.session.commit()
        return redirect(url_for("groundcheck.lihat_data"))

    return render_template("llz/edit_ground_check.html", gc=gc)


# ============================
# Delete Ground Check
# ============================
@groundcheck_bp.route("/llz/delete/<int:id>")
@login_required
def delete_ground_check(id):
    gc = GroundCheck.query.get_or_404(id)
    db.session.delete(gc)
    db.session.commit()
    return redirect(url_for("groundcheck.lihat_data"))


# ============================
# Detail Ground Check
# ============================
@groundcheck_bp.route("/llz/detail/<int:id>")
@login_required
def detail_data(id):
    record = GroundCheck.query.get_or_404(id)
    rows = GroundCheckRow.query.filter_by(groundcheck_id=id).all()
    return render_template("llz/detail_data.html", record=record, rows=rows)


# ============================
# Cetak Ground Check
# ============================
@groundcheck_bp.route("/cetak/<int:id>")
@login_required
def cetak_gc(id):
    record = GroundCheck.query.get_or_404(id)
    rows = GroundCheckRow.query.filter_by(groundcheck_id=id).all()
    return render_template("llz/cetak_gc.html", record=record, rows=rows)
