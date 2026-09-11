from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

SEED = 42
rng = np.random.default_rng(SEED)
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
SRC_DIR = ROOT / 'src'
MODEL_DIR = ROOT / 'models'
OUTPUT_DIR = ROOT / 'outputs'
for p in [DATA_DIR, SRC_DIR, MODEL_DIR, OUTPUT_DIR]:
    p.mkdir(parents=True, exist_ok=True)

FIRST_NAMES = [
    'Areeba','Ahmed','Ali','Ammar','Anaya','Bilal','Dua','Farhan','Fatima','Hamza',
    'Hania','Hassan','Iqra','Laiba','Mahnoor','Maryam','Mehak','Muneeb','Noor','Rida',
    'Saad','Sana','Sara','Shayan','Taha','Usman','Zain','Zara','Aqsa','Huzaifa',
    'Sajawal','Rabia','Nimra','Waleed','Komal','Danish','Aiman','Fahad','Hira','Rayyan'
]
LAST_NAMES = [
    'Ali','Ahmed','Khan','Shaikh','Siddiqui','Memon','Rind','Qureshi','Abbasi','Malik',
    'Mirza','Soomro','Baloch','Rajput','Chandio','Jatoi','Narejo','Ansari','Farooq','Iqbal'
]
DOMAINS = ['gmail.com','outlook.com','yahoo.com','student.edu.pk']
DEPARTMENTS = ['Data Analytics','Business Intelligence','Web Development','Cloud & DevOps','QA & Testing','UI/UX Design']
UNIVERSITIES = [
    'Shah Abdul Latif University','University of Sindh','Mehran UET','NED University',
    'University of Karachi','FAST NUCES','COMSATS University','IBA Karachi','SZABIST','Sukkur IBA University'
]
DEGREES = ['BS Information Technology','BS Computer Science','BS Software Engineering','BS Data Science','BBA','BS Mathematics']
CITIES = ['Karachi','Hyderabad','Khairpur','Sukkur','Nawabshah','Lahore','Islamabad','Multan','Faisalabad','Peshawar']
SEMESTERS = [5,6,7,8]


def safe_name(i: int) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def email_for(name: str, i: int) -> str:
    slug = ''.join(c.lower() for c in name if c.isalnum())
    return f"{slug}{1000+i}@{rng.choice(DOMAINS)}"


def phone_for(i: int) -> str:
    prefix = rng.choice(['300','301','302','303','304','305','311','312','313','315','316','317','320','321','322','323','331','332','333','334'])
    return f"+92{prefix}{1000000+i:07d}"[-13:]


def make_base_rows(n: int = 640) -> list[dict]:
    start = pd.Timestamp('2026-07-01 08:00:00')
    rows = []
    device_pool = [f"DEV-{i:04d}" for i in range(1, 560)]
    ip_pool = [f"IPH-{i:04d}" for i in range(1, 450)]
    for i in range(n):
        name = safe_name(i)
        day = int(rng.integers(0, 30))
        # realistic application activity: mostly daytime/evening, lower overnight volume
        hour = int(rng.choice(np.arange(8, 24), p=np.array([3,4,5,6,7,8,8,8,8,8,7,6,5,4,4,3])/94))
        minute = int(rng.integers(0, 60))
        second = int(rng.integers(0, 60))
        ts = start + pd.Timedelta(days=day, hours=hour-8, minutes=minute, seconds=second)
        degree = str(rng.choice(DEGREES, p=[.22,.25,.18,.13,.12,.10]))
        semester = int(rng.choice(SEMESTERS, p=[.15,.20,.28,.37]))
        grad_year = int(2026 + max(0, (8-semester+1)//2) + rng.choice([0,0,0,1]))
        if semester == 8 and rng.random() < .35:
            grad_year = 2026
        cgpa = round(float(np.clip(rng.normal(3.05, .42), 2.0, 3.95)), 2)
        row = {
            'application_id': f"APP-2026-{i+1:04d}",
            'submitted_at': ts,
            'applicant_name': name,
            'email': email_for(name, i),
            'phone': phone_for(i),
            'device_id': str(rng.choice(device_pool)),
            'ip_hash': str(rng.choice(ip_pool)),
            'cv_hash': f"CVH-{10000+i:05d}",
            'department': str(rng.choice(DEPARTMENTS, p=[.24,.18,.18,.13,.13,.14])),
            'university': str(rng.choice(UNIVERSITIES)),
            'degree': degree,
            'semester': semester,
            'graduation_year': grad_year,
            'city': str(rng.choice(CITIES, p=[.26,.15,.08,.07,.06,.10,.09,.06,.07,.06])),
            'cgpa': cgpa,
            'cgpa_scale': 4.0,
            'form_completion_seconds': int(np.clip(rng.lognormal(np.log(410), .45), 120, 1500)),
            'cover_letter_chars': int(np.clip(rng.normal(720, 240), 180, 1600)),
            'skills_count': int(np.clip(rng.poisson(6)+1, 2, 14)),
            'portfolio_url_present': int(rng.random() < .54),
            'github_url_present': int(rng.random() < .48),
            'availability_hours_week': int(rng.choice([15,20,20,25,25,30,30,35,40])),
            'synthetic_reference_label': 'Normal',
        }
        rows.append(row)
    return rows


def inject_duplicate(rows: list[dict], source_idx: int, new_id: int, minutes: int) -> dict:
    src = dict(rows[source_idx])
    src['application_id'] = f"APP-2026-{new_id:04d}"
    src['submitted_at'] = pd.Timestamp(src['submitted_at']) + pd.Timedelta(minutes=minutes)
    # duplicate identity and CV but occasionally switches department/city to mimic repeated/fake entries
    if rng.random() < .55:
        src['department'] = str(rng.choice([d for d in DEPARTMENTS if d != src['department']]))
    if rng.random() < .25:
        src['city'] = str(rng.choice(CITIES))
    src['form_completion_seconds'] = int(rng.integers(35, 120))
    src['synthetic_reference_label'] = 'Duplicate'
    return src


def inject_rapid(new_id: int, burst_device: str, burst_ip: str, ts: pd.Timestamp, k: int) -> dict:
    name = safe_name(new_id)
    semester = int(rng.choice(SEMESTERS))
    return {
        'application_id': f"APP-2026-{new_id:04d}",
        'submitted_at': ts + pd.Timedelta(seconds=int(k*rng.integers(18, 65))),
        'applicant_name': name,
        'email': email_for(name, new_id+5000),
        'phone': phone_for(new_id+5000),
        'device_id': burst_device,
        'ip_hash': burst_ip,
        'cv_hash': f"CVH-R{new_id:05d}",
        'department': str(rng.choice(DEPARTMENTS)),
        'university': str(rng.choice(UNIVERSITIES)),
        'degree': str(rng.choice(DEGREES)),
        'semester': semester,
        'graduation_year': int(2026 + max(0, (8-semester+1)//2)),
        'city': str(rng.choice(CITIES)),
        'cgpa': round(float(np.clip(rng.normal(3.0, .5), 2.0, 4.0)), 2),
        'cgpa_scale': 4.0,
        'form_completion_seconds': int(rng.integers(18, 75)),
        'cover_letter_chars': int(rng.integers(80, 420)),
        'skills_count': int(rng.integers(2, 9)),
        'portfolio_url_present': int(rng.random() < .35),
        'github_url_present': int(rng.random() < .35),
        'availability_hours_week': int(rng.choice([20,25,30,40])),
        'synthetic_reference_label': 'Rapid Burst',
    }


def inject_inconsistent(new_id: int) -> dict:
    name = safe_name(new_id)
    ts = pd.Timestamp('2026-07-01') + pd.Timedelta(days=int(rng.integers(0,30)), hours=int(rng.integers(8,23)), minutes=int(rng.integers(0,60)))
    semester = int(rng.choice([5,6,7,8]))
    pattern = int(rng.integers(0,4))
    cgpa = round(float(rng.uniform(2.2,3.8)),2)
    grad_year = int(rng.choice([2026,2027,2028]))
    hours = int(rng.choice([15,20,25,30,35,40]))
    cover = int(rng.integers(200,1100))
    if pattern == 0:
        cgpa = round(float(rng.uniform(4.15,4.95)),2)  # exceeds 4-point scale
    elif pattern == 1:
        semester = 5
        grad_year = 2025  # impossible for active semester 5 in 2026
    elif pattern == 2:
        hours = int(rng.choice([70,80,95]))
        cover = int(rng.integers(40,100))
    else:
        semester = 8
        grad_year = 2029
    return {
        'application_id': f"APP-2026-{new_id:04d}",
        'submitted_at': ts,
        'applicant_name': name,
        'email': email_for(name, new_id+9000),
        'phone': phone_for(new_id+9000),
        'device_id': f"DEV-I{new_id:04d}",
        'ip_hash': f"IPH-I{new_id:04d}",
        'cv_hash': f"CVH-I{new_id:05d}",
        'department': str(rng.choice(DEPARTMENTS)),
        'university': str(rng.choice(UNIVERSITIES)),
        'degree': str(rng.choice(DEGREES)),
        'semester': semester,
        'graduation_year': grad_year,
        'city': str(rng.choice(CITIES)),
        'cgpa': cgpa,
        'cgpa_scale': 4.0,
        'form_completion_seconds': int(rng.integers(70,500)),
        'cover_letter_chars': cover,
        'skills_count': int(rng.integers(1,13)),
        'portfolio_url_present': int(rng.random() < .45),
        'github_url_present': int(rng.random() < .45),
        'availability_hours_week': hours,
        'synthetic_reference_label': 'Inconsistent',
    }


def build_dataset() -> pd.DataFrame:
    rows = make_base_rows(640)
    next_id = 641

    # 30 clear duplicates and 10 multi-signal duplicates
    source_indices = rng.choice(np.arange(0, 500), size=40, replace=False)
    for j, src_idx in enumerate(source_indices):
        dup = inject_duplicate(rows, int(src_idx), next_id, int(rng.integers(2, 720)))
        if j >= 30:
            dup['submitted_at'] = pd.Timestamp(rows[int(src_idx)]['submitted_at']) + pd.Timedelta(seconds=int(rng.integers(20,90)))
            dup['synthetic_reference_label'] = 'Multi-signal'
        rows.append(dup)
        next_id += 1

    # 24 rapid burst applications spread across 4 bursts
    for b in range(4):
        burst_device = f"DEV-BURST-{b+1}"
        burst_ip = f"IPH-BURST-{b+1}"
        base_ts = pd.Timestamp('2026-07-05') + pd.Timedelta(days=int(rng.integers(0,22)), hours=int(rng.integers(10,21)))
        for k in range(6):
            rows.append(inject_rapid(next_id, burst_device, burst_ip, base_ts, k))
            next_id += 1

    # 16 standalone inconsistent rows
    for _ in range(16):
        rows.append(inject_inconsistent(next_id))
        next_id += 1

    assert len(rows) == 720
    df = pd.DataFrame(rows)
    df['submitted_at'] = pd.to_datetime(df['submitted_at'])
    df = df.sort_values('submitted_at').reset_index(drop=True)

    # Frequency signals.
    for col, out in [('email','duplicate_email_count'),('phone','duplicate_phone_count'),('device_id','device_reuse_count'),('ip_hash','ip_reuse_count'),('cv_hash','duplicate_cv_count')]:
        counts = df[col].value_counts()
        df[out] = df[col].map(counts).astype(int)

    # Sequence timing by device/IP.
    df['minutes_since_device_submission'] = (
        df.groupby('device_id')['submitted_at'].diff().dt.total_seconds().div(60)
    )
    df['minutes_since_ip_submission'] = (
        df.groupby('ip_hash')['submitted_at'].diff().dt.total_seconds().div(60)
    )
    df['minutes_since_device_submission'] = df['minutes_since_device_submission'].fillna(10080).clip(0, 10080).round(2)
    df['minutes_since_ip_submission'] = df['minutes_since_ip_submission'].fillna(10080).clip(0, 10080).round(2)

    # Rolling 24-hour activity counts by device and IP (loop is fine for 720 rows).
    device_24h = []
    ip_24h = []
    for idx, row in df.iterrows():
        window_start = row['submitted_at'] - pd.Timedelta(hours=24)
        prior = df.iloc[:idx]
        device_24h.append(int(((prior['device_id'] == row['device_id']) & (prior['submitted_at'] >= window_start)).sum() + 1))
        ip_24h.append(int(((prior['ip_hash'] == row['ip_hash']) & (prior['submitted_at'] >= window_start)).sum() + 1))
    df['device_applications_24h'] = device_24h
    df['ip_applications_24h'] = ip_24h

    # Explainable rule signals.
    df['duplicate_signal'] = (
        (df['duplicate_email_count'] > 1) | (df['duplicate_phone_count'] > 1) | (df['duplicate_cv_count'] > 1)
    ).astype(int)
    df['rapid_submission_signal'] = (
        (df['minutes_since_device_submission'] < 3) | (df['minutes_since_ip_submission'] < 3) |
        (df['device_applications_24h'] >= 4) | (df['ip_applications_24h'] >= 5) |
        (df['form_completion_seconds'] < 60)
    ).astype(int)

    inconsistency = np.zeros(len(df), dtype=int)
    inconsistency += (df['cgpa'] > df['cgpa_scale']).astype(int)
    inconsistency += ((df['semester'] <= 6) & (df['graduation_year'] <= 2026)).astype(int)
    inconsistency += ((df['semester'] == 8) & (df['graduation_year'] >= 2029)).astype(int)
    inconsistency += (df['availability_hours_week'] > 60).astype(int)
    inconsistency += ((df['cover_letter_chars'] < 100) & (df['form_completion_seconds'] < 120)).astype(int)
    df['inconsistency_count'] = inconsistency
    df['inconsistent_data_signal'] = (df['inconsistency_count'] > 0).astype(int)

    # Unsupervised ML features. Synthetic reference labels are never used here.
    feature_cols = [
        'duplicate_email_count','duplicate_phone_count','duplicate_cv_count','device_reuse_count','ip_reuse_count',
        'device_applications_24h','ip_applications_24h','minutes_since_device_submission','minutes_since_ip_submission',
        'form_completion_seconds','cover_letter_chars','inconsistency_count','skills_count',
        'portfolio_url_present','github_url_present','availability_hours_week'
    ]
    X = df[feature_cols].copy()
    # Log-transform highly skewed timing/activity quantities for stable geometry.
    for c in ['minutes_since_device_submission','minutes_since_ip_submission','form_completion_seconds','cover_letter_chars']:
        X[c] = np.log1p(X[c])
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    iso = IsolationForest(n_estimators=350, contamination=0.11, random_state=SEED, n_jobs=-1)
    pred = iso.fit_predict(Xs)
    decision = iso.decision_function(Xs)  # lower => more anomalous
    df['isolation_flag'] = (pred == -1).astype(int)
    # percentile anomaly intensity: most anomalous near 100
    ranks = pd.Series(-decision).rank(pct=True).to_numpy()
    df['isolation_anomaly_percentile'] = (ranks * 100).round(1)
    df['isolation_decision_score'] = decision.round(5)

    kmeans = KMeans(n_clusters=4, random_state=SEED, n_init=25)
    clusters = kmeans.fit_predict(Xs)
    df['kmeans_cluster'] = clusters.astype(int)

    # Cluster behavior risk without using synthetic truth labels.
    behavior_signal = (
        2.2*df['duplicate_signal'] + 2.0*df['rapid_submission_signal'] + 2.1*df['inconsistent_data_signal'] +
        0.35*np.clip(df['device_applications_24h']-1,0,8) + 0.25*np.clip(df['ip_applications_24h']-1,0,8)
    )
    df['_behavior_signal'] = behavior_signal
    cluster_mean = df.groupby('kmeans_cluster')['_behavior_signal'].mean().to_dict()
    max_cm = max(cluster_mean.values()) or 1
    df['cluster_risk_index'] = df['kmeans_cluster'].map(lambda c: 100*cluster_mean[c]/max_cm).round(1)

    # Human-readable cluster profiles based on cluster centroid signals.
    profile_map = {}
    for c in sorted(df['kmeans_cluster'].unique()):
        sub = df[df['kmeans_cluster']==c]
        vals = {
            'duplicate': sub['duplicate_signal'].mean(),
            'rapid': sub['rapid_submission_signal'].mean(),
            'inconsistent': sub['inconsistent_data_signal'].mean(),
        }
        dominant = max(vals, key=vals.get)
        if max(vals.values()) < .10:
            label = 'Typical pattern'
        elif dominant == 'duplicate':
            label = 'Identity reuse pattern'
        elif dominant == 'rapid':
            label = 'Rapid submission pattern'
        else:
            label = 'Data inconsistency pattern'
        profile_map[int(c)] = label
    df['cluster_profile'] = df['kmeans_cluster'].map(profile_map)

    rule_points = (
        18*df['duplicate_signal'] + 16*df['rapid_submission_signal'] + 17*df['inconsistent_data_signal'] +
        6*np.clip(df['inconsistency_count'],0,3) +
        4*np.clip(df['device_applications_24h']-1,0,5) +
        3*np.clip(df['duplicate_email_count']-1,0,3) +
        3*np.clip(df['duplicate_cv_count']-1,0,3)
    ).clip(0,100)
    risk = 0.50*df['isolation_anomaly_percentile'] + 0.30*rule_points + 0.20*df['cluster_risk_index']
    # Ensure clear known suspicious scenarios surface strongly, while retaining ML-led ranking.
    risk += 8*df['duplicate_signal'] + 7*df['rapid_submission_signal'] + 7*df['inconsistent_data_signal']
    df['risk_score'] = risk.clip(0,100).round(1)

    df['alert_level'] = pd.cut(
        df['risk_score'], bins=[-1,44.999,59.999,74.999,100], labels=['Normal','Review','High','Critical']
    ).astype(str)

    def reason(row):
        reasons=[]
        if row['duplicate_signal']:
            reasons.append('duplicate identity/CV reuse')
        if row['rapid_submission_signal']:
            reasons.append('rapid or burst submission')
        if row['inconsistent_data_signal']:
            reasons.append('inconsistent application data')
        if row['isolation_flag'] and not reasons:
            reasons.append('unusual multivariate behavior')
        return '; '.join(reasons) if reasons else 'no material alert signal'
    df['alert_reason'] = df.apply(reason, axis=1)

    truth = (df['synthetic_reference_label'] != 'Normal').astype(int)
    detected = (df['alert_level'].isin(['High','Critical'])).astype(int)
    metrics = {
        'rows': int(len(df)),
        'synthetic_truth_anomalies': int(truth.sum()),
        'isolation_forest_flagged': int(df['isolation_flag'].sum()),
        'review_or_higher': int((df['alert_level']!='Normal').sum()),
        'high_or_critical': int(detected.sum()),
        'precision_high_or_critical_vs_synthetic_reference': round(float(precision_score(truth, detected, zero_division=0)), 4),
        'recall_high_or_critical_vs_synthetic_reference': round(float(recall_score(truth, detected, zero_division=0)), 4),
        'f1_high_or_critical_vs_synthetic_reference': round(float(f1_score(truth, detected, zero_division=0)), 4),
        'confusion_matrix': confusion_matrix(truth, detected).tolist(),
        'cluster_profiles': {str(k): v for k,v in profile_map.items()},
        'feature_columns': feature_cols,
        'note': 'Synthetic reference labels are used only for portfolio validation and are excluded from unsupervised model fitting.'
    }

    # Clean temp helper and format datetimes.
    df = df.drop(columns=['_behavior_signal'])
    df['submitted_at'] = df['submitted_at'].dt.strftime('%Y-%m-%d %H:%M:%S')

    return df, metrics, iso, scaler, kmeans, feature_cols


def export_browser_data(df: pd.DataFrame, metrics: dict):
    records = json.loads(df.to_json(orient='records'))
    payload = {
        'generated_at': '2026-09-10',
        'dataset_note': 'Synthetic portfolio dataset designed to simulate internship-application behavior. No confidential or real applicant data is used.',
        'records': records,
        'model_metrics': metrics,
    }
    (SRC_DIR / 'data.js').write_text('window.TASK4_DATA = ' + json.dumps(payload, ensure_ascii=False) + ';\n', encoding='utf-8')


def main():
    df, metrics, iso, scaler, kmeans, feature_cols = build_dataset()
    df.to_csv(DATA_DIR / 'task4_dataset.csv', index=False)
    export_browser_data(df, metrics)

    model_summary = {
        'project': 'Fraud Detection in Internship Applications',
        'algorithms': ['Isolation Forest','K-Means Clustering'],
        'random_seed': SEED,
        'isolation_forest': {
            'n_estimators': iso.n_estimators,
            'contamination': iso.contamination,
            'feature_count': len(feature_cols),
        },
        'kmeans': {
            'n_clusters': int(kmeans.n_clusters),
            'n_init': int(kmeans.n_init),
            'inertia': round(float(kmeans.inertia_), 3),
        },
        'validation': metrics,
        'responsible_use': 'Scores prioritize applications for human review. They are not proof of fraud and must not be used for automatic rejection.'
    }
    (MODEL_DIR / 'model_summary.json').write_text(json.dumps(model_summary, indent=2), encoding='utf-8')

    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
