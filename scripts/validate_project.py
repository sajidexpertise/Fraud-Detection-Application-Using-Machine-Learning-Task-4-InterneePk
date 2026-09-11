from pathlib import Path
import csv, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
required = [
    'index.html','README.md','SUBMISSION_GUIDE.md','PROJECT_CHECKLIST.md','linkedin_post.txt','video_demo_script.md',
    'requirements.txt','OPEN_DASHBOARD.bat','data/task4_dataset.csv','data/task4_dataset.xlsx','data/data_dictionary.csv',
    'src/styles.css','src/app.js','src/data.js','scripts/data_generation.py','scripts/fraud_detection_ml.py','assets/dashboard-preview.png',
    'outputs/dashboard-screenshot.png','outputs/analysis-summary.pdf'
]
errors=[]
for rel in required:
    if not (ROOT/rel).exists(): errors.append(f'Missing: {rel}')

csv_path=ROOT/'data/task4_dataset.csv'
if csv_path.exists():
    with csv_path.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
    if not 300 <= len(rows) <= 1000: errors.append(f'Dataset row count outside requested range: {len(rows)}')
    required_cols={'duplicate_signal','rapid_submission_signal','inconsistent_data_signal','isolation_flag','kmeans_cluster','risk_score','alert_level'}
    missing=required_cols-set(rows[0]) if rows else required_cols
    if missing: errors.append('Missing analysis columns: '+', '.join(sorted(missing)))
    if rows:
        sus=sum(r['alert_level']!='Normal' for r in rows)
        print(f'CSV rows: {len(rows)} | suspicious: {sus}')

idx=(ROOT/'index.html').read_text(encoding='utf-8') if (ROOT/'index.html').exists() else ''
for token in ['themeToggle','applyFilters','resetFilters','downloadCsv','printReport','Isolation Forest','K-Means']:
    if token not in idx: errors.append(f'index.html missing expected feature token: {token}')
js=(ROOT/'src/app.js').read_text(encoding='utf-8') if (ROOT/'src/app.js').exists() else ''
for token in ['renderTrend','renderDepartment','renderDonut','renderScatter','renderHeatmap','downloadCSV','toggleTheme']:
    if token not in js: errors.append(f'app.js missing feature: {token}')

datajs=(ROOT/'src/data.js').read_text(encoding='utf-8') if (ROOT/'src/data.js').exists() else ''
if datajs:
    m=re.search(r'window\.TASK4_DATA\s*=\s*(\{.*\});\s*$',datajs,re.S)
    if not m: errors.append('Unable to parse src/data.js')
    else:
        payload=json.loads(m.group(1))
        if len(payload.get('records',[])) != len(rows): errors.append('CSV and browser data row counts do not match')

if errors:
    print('\nVALIDATION FAILED')
    for e in errors: print(' -',e)
    sys.exit(1)
print('\nVALIDATION PASSED: required files, dataset range, ML fields and dashboard feature hooks are present.')
