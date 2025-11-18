from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.utils import secure_filename
from backend.config import Config
from backend.parsers.chase_parser import ChaseParser
from backend.parsers.discover_parser import DiscoverParser
from backend.parsers.csv_detector import CSVDetector, CSVType

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
Config.init_app()

all_transactions = []

@app.route('/')
def index():
    if not all_transactions:
        return redirect(url_for('upload'))
    
    total = sum(abs(t.amount) for t in all_transactions if t.is_expense)
    return render_template('index.html', 
                          transactions=all_transactions,
                          total_spent=total)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global all_transactions
    
    if request.method == 'POST':
        files = request.files.getlist('files')
        
        for file in files:
            if not file.filename.endswith('.csv'):
                continue
                
            filename = secure_filename(file.filename)
            path = Config.UPLOAD_FOLDER / filename
            file.save(str(path))
            
            csv_type = CSVDetector.detect(str(path))
            
            if csv_type in (CSVType.CHASE_CREDIT, CSVType.CHASE_DEBIT):
                txns = ChaseParser.parse(str(path))
            elif csv_type == CSVType.DISCOVER:
                txns = DiscoverParser.parse(str(path))
            else:
                flash(f'Unknown format: {file.filename}', 'warning')
                continue
            
            all_transactions.extend(txns)
            flash(f'{file.filename}: {len(txns)} transactions')
        
        if all_transactions:
            return redirect(url_for('index'))
    
    return render_template('upload.html')
