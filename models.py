import json
from datetime import datetime

from flask_login import UserMixin

from extensions import db

# ------------------ USER ------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


# ------------------ VHF ------------------

class Station(db.Model):
    __tablename__ = 'station'
    id = db.Column(db.Integer, primary_key=True)
    nama_stasiun = db.Column(db.String(100), nullable=False)
    frekuensi = db.Column(db.String(20), nullable=False)  # atau db.Float jika perlu
    transmissions = db.relationship('Transmission', backref='station', cascade="all, delete", passive_deletes=True)

    def __repr__(self):
        return f"<Station {self.nama_stasiun} - {self.frekuensi} MHz>"

class Transmission(db.Model):
    __tablename__ = 'transmission'
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('station.id', ondelete='CASCADE'), nullable=False)
    tx1_power = db.Column(db.Float, nullable=True)
    tx1_swr = db.Column(db.String(20), nullable=True)
    tx1_mod = db.Column(db.Float, nullable=True)
    tx2_power = db.Column(db.Float, nullable=True)
    tx2_swr = db.Column(db.String(20), nullable=True)
    tx2_mod = db.Column(db.Float, nullable=True)
    tanggal = db.Column(db.Date, nullable=False)
    pic = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<TX {self.tanggal} - PIC {self.pic}>"

# ------------------ DVOR ------------------

class Station_dvor(db.Model):
    __tablename__ = 'station_dvor'
    id = db.Column(db.Integer, primary_key=True)
    nama_stasiun_dvor = db.Column(db.String(100), nullable=False)
    frekuensi_dvor = db.Column(db.String(20), nullable=False)
    transmissions = db.relationship('Transmission_dvor', backref='station_dvor', cascade="all, delete", passive_deletes=True)
    


    def __repr__(self):
        return f"<Station {self.nama_stasiun_dvor} - {self.frekuensi_dvor} MHz>"

class Transmission_dvor(db.Model):
    __tablename__ = 'transmission_dvor'
    id = db.Column(db.Integer, primary_key=True)
    station_dvor_id = db.Column(db.Integer, db.ForeignKey('station_dvor.id', ondelete='CASCADE'), nullable=False)

    tx1_power = db.Column(db.Float, nullable=True)
    tx1_bearing = db.Column(db.Float, nullable=True)
    tx1_modulasi = db.Column(db.Float, nullable=True)
    tx2_power = db.Column(db.Float, nullable=True)
    tx2_bearing = db.Column(db.Float, nullable=True)
    tx2_modulasi = db.Column(db.Float, nullable=True)
    tanggal = db.Column(db.Date, nullable=False)
    pic = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<TX {self.tanggal} - PIC {self.pic}>"

# ------------------ DME ------------------

class Station_dme(db.Model):
    __tablename__ = 'station_dme'
    id = db.Column(db.Integer, primary_key=True)
    nama_stasiun_dme = db.Column(db.String(100), nullable=False)
    frekuensi_dme = db.Column(db.String(20), nullable=False)  # atau db.Float jika perlu
    transmissions_dme = db.relationship('Transmission_dme', backref='station_dme', cascade="all, delete", passive_deletes=True)

    def __repr__(self):
        return f"<Station {self.nama_stasiun_dme} - {self.frekuensi_dme} X>"

class Transmission_dme(db.Model):
    __tablename__ = 'transmission_dme'
    id = db.Column(db.Integer, primary_key=True)
    station_dme_id = db.Column(db.Integer, db.ForeignKey('station_dme.id', ondelete='CASCADE'), nullable=False)

    tx1_power = db.Column(db.Float, nullable=True)
    tx1_spacing = db.Column(db.Float, nullable=True)
    tx1_delay = db.Column(db.Float, nullable=True)
    tx2_power = db.Column(db.Float, nullable=True)
    tx2_spacing = db.Column(db.Float, nullable=True)
    tx2_delay = db.Column(db.Float, nullable=True)
    tanggal = db.Column(db.Date, nullable=False)
    pic = db.Column(db.String(100), nullable=False)
    

    def __repr__(self):
        return f"<TX {self.tanggal} - PIC {self.pic}>"
    
    
# ------------------ RADAR ------------------
class Station_radar(db.Model):
    __tablename__ = 'station_radar'
    id = db.Column(db.Integer, primary_key=True)
    nama_stasiun_radar = db.Column(db.String(100), nullable=False)
    frekuensi_radar = db.Column(db.String(20), nullable=False)
    transmissions = db.relationship('Transmission_radar', backref='station_radar', cascade="all, delete", passive_deletes=True)

    def __repr__(self):
        return f"<Station {self.nama_stasiun_radar} - {self.frekuensi_radar} MHz>"


class Transmission_radar(db.Model):
    __tablename__ = 'transmission_radar'
    id = db.Column(db.Integer, primary_key=True)
    station_radar_id = db.Column(
        db.Integer, db.ForeignKey('station_radar.id', ondelete='CASCADE'), nullable=False
    )

    power_forward = db.Column(db.Float, nullable=True)
    azimuth_ilan = db.Column(db.Float, nullable=True)  # Encoder
    power_reflected = db.Column(db.Float, nullable=True)

    # Integration Pulse
    integration_mod_a = db.Column(db.Float, nullable=True)     # 0.8 ms
    integration_mod_c = db.Column(db.Float, nullable=True)     # 21 ms

    # Mod S: terdiri dari P1, P2, PG
    mod_s_p1 = db.Column(db.Float, nullable=True)              # 0.8 ms
    mod_s_p2 = db.Column(db.Float, nullable=True)              # 0.8 ms
    mod_s_pg = db.Column(db.Float, nullable=True)              # 112 ms

    
    tanggal = db.Column(db.Date, nullable=False)
    pic = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<TX {self.tanggal} - PIC {self.pic}>"
    
# ------------------ILS----------------------------

class Station_ils(db.Model):
    __tablename__= 'station_ils'
    id = db.Column(db.Integer, primary_key=True)
    lokasi_stasiun_ils = db.Column(db.String(50), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    pic = db.Column(db.String(100), nullable=False)

    gp = db.relationship('Transmission_Gp', backref='station_ils', uselist=False, cascade='all, delete')
    localizer = db.relationship('Transmission_Localizer', backref='station_ils', uselist=False, cascade='all, delete')
    tdme = db.relationship('Transmission_Tdme', backref='station_ils', uselist=False, cascade='all, delete')

    def __repr__(self):
        return f"<Station {self.lokasi_stasiun_ils}>"
    
class Transmission_Gp(db.Model):
    __tablename__ = 'transmissions_gp'
    id = db.Column(db.Integer, primary_key=True)
    station_ils_id = db.Column(db.Integer, db.ForeignKey('station_ils.id'))
    # lokasi = db.Column(db.String(50), nullable=False)
    csb_power = db.Column(db.Float)
    sbo_power = db.Column(db.Float)
    sdm_80 = db.Column(db.Float)
    course_ddm = db.Column(db.Float)
    ds_ddm = db.Column(db.Float)
    clr_ddm = db.Column(db.Float)    
    
class Transmission_Localizer(db.Model):
    __tablename__ = 'transmissions_localizer'
    id = db.Column(db.Integer, primary_key=True)
    station_ils_id = db.Column(db.Integer, db.ForeignKey('station_ils.id'))
    # lokasi = db.Column(db.String(50), nullable=False)
    csb_power = db.Column(db.Float)
    sbo_power = db.Column(db.Float)
    sdm_40 = db.Column(db.Float)
    course_ddm = db.Column(db.Float)
    ds_ddm = db.Column(db.Float)
    clr_ddm = db.Column(db.Float)
    

class Transmission_Tdme(db.Model):
    __tablename__ = 'transmissions_tdme'
    id = db.Column(db.Integer, primary_key=True)
    station_ils_id = db.Column(db.Integer, db.ForeignKey('station_ils.id'))
    # lokasi = db.Column(db.String(50), nullable=False)
    tx1_power = db.Column(db.Float)
    spacing1 = db.Column(db.String(20))
    delay1 = db.Column(db.String(20))
    tx2_power = db.Column(db.Float)
    spacing2 = db.Column(db.String(20))
    delay2 = db.Column(db.String(20))

    def __repr__(self):
        return f"<TX {self.tanggal} - PIC {self.pic}>"
    


# ------------------GC---------------------------

from extensions import db


class GroundCheck(db.Model):
    __tablename__ = "ground_check"

    id = db.Column(db.Integer, primary_key=True)
    lokasi = db.Column(db.String(50), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    teknisi = db.Column(db.Text, nullable=True)
    catatan = db.Column(db.Text, nullable=True)

    manager_tujuan = db.Column(db.String(50), nullable=False) 
    status = db.Column(db.String(20), default="Proses")   # Proses / Selesai
    manager = db.Column(db.String(100), nullable=True)    # nama manager yang acc

    rows = db.relationship(
        "GroundCheckRow",
        backref="ground_check",
        cascade="all, delete-orphan"
    )



class GroundCheckRow(db.Model):
    __tablename__ = "ground_check_row"

    id = db.Column(db.Integer, primary_key=True)
    groundcheck_id = db.Column(db.Integer, db.ForeignKey("ground_check.id"), nullable=False)

    freq = db.Column(db.String(10), nullable=True)      # 90 Hz / 150 Hz / Center
    jarak = db.Column(db.Float, nullable=True)          # angka (bisa kosong)
    degree = db.Column(db.String(20), nullable=True)    # simpan string supaya bisa "±1.85"

    # TX1 (semua nullable)
    tx1_ddm_persen = db.Column(db.Float, nullable=True)
    tx1_ddm_ua = db.Column(db.Float, nullable=True)
    tx1_sum = db.Column(db.Float, nullable=True)
    tx1_mod90 = db.Column(db.Float, nullable=True)
    tx1_mod150 = db.Column(db.Float, nullable=True)
    tx1_rf = db.Column(db.Float, nullable=True)

    # TX2 (semua nullable)
    tx2_ddm_persen = db.Column(db.Float, nullable=True)
    tx2_ddm_ua = db.Column(db.Float, nullable=True)
    tx2_sum = db.Column(db.Float, nullable=True)
    tx2_mod90 = db.Column(db.Float, nullable=True)
    tx2_mod150 = db.Column(db.Float, nullable=True)
    tx2_rf = db.Column(db.Float, nullable=True)