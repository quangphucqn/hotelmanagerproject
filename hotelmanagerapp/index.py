from flask import render_template, request, redirect, url_for
from hotelmanagerapp import app


@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)