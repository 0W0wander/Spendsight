from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.utils import secure_filename
from backend.config import Config
from backend.parsers.chase_parser import ChaseParser

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
Config.init_app()

transactions = []

@app.route('/')
def index():
    if not transactions:
        return redirect(url_for('upload'))
    return render_template('index.html', transactions=transactions)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global transactions
    
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            path = Config.UPLOAD_FOLDER / filename
            file.save(str(path))
            
            new_txns = ChaseParser.parse(str(path))
            transactions.extend(new_txns)
            flash(f'Loaded {len(new_txns)} transactions')
            return redirect(url_for('index'))
    
    return render_template('upload.html')
