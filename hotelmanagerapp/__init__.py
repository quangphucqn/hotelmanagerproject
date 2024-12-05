from flask import Flask
from urllib.parse import quote
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.secret_key = 'HGHJAHA^&^&*AJAVAHJ*^&^&*%&*^GAFGFAG'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/hotelmanagementapp?charset=utf8mb4" % quote("060204")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db = SQLAlchemy(app=app)