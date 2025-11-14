from flask import Flask, render_template, redirect, url_for
from backend.config import Config

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
app.config.from_object(Config)
Config.init_app()

transactions = []

@app.route('/')
def index():
    if not transactions:
        return redirect(url_for('upload'))
    return render_template('index.html', transactions=transactions)

@app.route('/upload')
def upload():
    return render_template('upload.html')
