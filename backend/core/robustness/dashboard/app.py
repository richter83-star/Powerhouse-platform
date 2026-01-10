from flask import Flask, render_template
import json
import os

app = Flask(__name__, template_folder='templates')

@app.route('/')
def dashboard():
    results_file = os.path.join(os.path.dirname(__file__), 'red_team_results.json')
    
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            results = json.load(f)
    else:
        results = {"total_attacks": 0, "successful_attacks": 0, "vulnerabilities": []}
    
    vulnerabilities = results.get('vulnerabilities', [])
    severity_counts = {'high': 0, 'medium': 0, 'low': 0}
    
    for vuln in vulnerabilities:
        sev = vuln.get('severity', 'low')
        if sev in severity_counts:
            severity_counts[sev] += 1
    
    metrics = {
        'total_attacks': results.get('total_attacks', 0),
        'successful_attacks': results.get('successful_attacks', 0),
        'total_vulnerabilities': len(vulnerabilities),
        'severity_counts': severity_counts
    }
    
    return render_template('dashboard.html', metrics=metrics)

if __name__ == '__main__':
    app.run(debug=True)