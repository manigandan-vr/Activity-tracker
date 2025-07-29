from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
LOGS_FOLDER = 'activity_logs'
DATA_FILE = 'activity_data.json'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOGS_FOLDER, exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_log_file(sno):
    return os.path.join(LOGS_FOLDER, f'activity_{sno}_logs.json')

def load_activity_logs(sno):
    log_file = get_log_file(sno)
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            return json.load(f)
    return []

def save_activity_logs(sno, logs):
    with open(get_log_file(sno), 'w') as f:
        json.dump(logs, f, indent=4)

@app.route('/')
def index():
    activities = load_data()
    return render_template('index.html', activities=activities)

@app.route('/add', methods=['GET', 'POST'])
def add_activity():
    if request.method == 'POST':
        activities = load_data()
        sno = len(activities) + 1

        activity = {
            'sno': sno,
            'priority': request.form.get('priority'),
            'project': request.form.get('project'),
            'line': request.form.get('line'),
            'description': request.form.get('description'),
            'start_date': request.form.get('start_date'),
            'complete_date': request.form.get('complete_date'),
            'status': request.form.get('status'),
            'attachment': '',
            'remarks': request.form.get('remarks')
        }

        file = request.files.get('attachment')
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{sno}_{file.filename}")
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            activity['attachment'] = filename

        activities.append(activity)
        save_data(activities)
        
        # Create initial log entry
        logs = [{
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'Activity Created',
            'details': 'Initial creation of activity',
            'file': activity['attachment']
        }]
        save_activity_logs(sno, logs)
        
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/update/<int:sno>', methods=['GET', 'POST'])
def update_activity(sno):
    if request.method == 'POST':
        activities = load_data()
        activity = next((a for a in activities if a['sno'] == sno), None)
        
        if activity:
            # Load existing logs
            logs = load_activity_logs(sno)
            
            # Prepare update data
            update_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'action': 'Activity Updated',
                'details': request.form.get('update_details', 'No details provided'),
                'file': ''
            }
            
            # Handle file upload
            file = request.files.get('update_file')
            if file and allowed_file(file.filename):
                filename = secure_filename(f"log_{sno}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                update_data['file'] = filename
            
            # Add to logs
            logs.append(update_data)
            save_activity_logs(sno, logs)
            
            return redirect(url_for('index'))
    
    return render_template('update.html', sno=sno)

@app.route('/view_logs/<int:sno>')
def view_logs(sno):
    logs = load_activity_logs(sno)
    return jsonify(logs)

@app.route('/delete/<int:sno>', methods=['POST'])
def delete_activity(sno):
    activities = load_data()
    activities = [act for act in activities if act['sno'] != sno]
    
    # Update serial numbers after deletion
    for idx, act in enumerate(activities, start=1):
        act['sno'] = idx
    
    save_data(activities)
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)