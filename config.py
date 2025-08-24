import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI','mysql+pymysql://root:@localhost/data_vhf')
    SQLALCHEMY_TRACK_MODIFICATIONS = False