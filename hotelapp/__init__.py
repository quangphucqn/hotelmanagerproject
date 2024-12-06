from flask import Flask
from urllib.parse import quote
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary
app = Flask(__name__)
app.secret_key='92376423rew4732455234234$#@$#^$%'
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://root:%s@localhost/hotelmanagementapp?charset=utf8mb4' % quote('060204')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=True
db=SQLAlchemy(app=app)

cloudinary.config(
    cloud_name='dywix6n0z',
    api_key='198396299352167',
    api_secret='Hlh12SuOkmrk7ZRQTX8f-nkDwTY'
)

login=LoginManager(app=app)