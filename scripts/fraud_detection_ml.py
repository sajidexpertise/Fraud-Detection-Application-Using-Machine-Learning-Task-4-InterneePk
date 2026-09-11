"""Re-run the unsupervised fraud/anomaly models on the Task 4 dataset.

This script intentionally does not use synthetic_reference_label as a training
feature. The reference label is only used after training for portfolio-level
validation of the combined review queue.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "task4_dataset.csv"
OUT = ROOT / "outputs" / "ml_recheck_summary.json"
SEED = 42

FEATURES = [
    'duplicate_email_count','duplicate_phone_count','duplicate_cv_count','device_reuse_count','ip_reuse_count',
    'device_applications_24h','ip_applications_24h','minutes_since_device_submission','minutes_since_ip_submission',
    'form_completion_seconds','cover_letter_chars','inconsistency_count','skills_count',
    'portfolio_url_present','github_url_present','availability_hours_week'
]
LOG_FEATURES = ['minutes_since_device_submission','minutes_since_ip_submission','form_completion_seconds','cover_letter_chars']

def main():
    df = pd.read_csv(DATA)
    X = df[FEATURES].copy()
    for c in LOG_FEATURES:
        X[c] = np.log1p(X[c])
    Xs = StandardScaler().fit_transform(X)

    iso = IsolationForest(n_estimators=350, contamination=0.11, random_state=SEED, n_jobs=-1)
    iso_pred = iso.fit_predict(Xs)
    kmeans = KMeans(n_clusters=4, random_state=SEED, n_init=25)
    km_pred = kmeans.fit_predict(Xs)

    expected_iso = df['isolation_flag'].astype(int).to_numpy()
    expected_km = df['kmeans_cluster'].astype(int).to_numpy()
    iso_match = float((expected_iso == (iso_pred == -1).astype(int)).mean())
    # K-Means cluster IDs can be permuted, so compare cluster-size distributions.
    expected_sizes = sorted(pd.Series(expected_km).value_counts().tolist())
    rerun_sizes = sorted(pd.Series(km_pred).value_counts().tolist())

    truth = (df['synthetic_reference_label'] != 'Normal').astype(int)
    detected = df['alert_level'].isin(['High','Critical']).astype(int)
    result = {
        'rows': int(len(df)),
        'training_features': FEATURES,
        'synthetic_reference_used_in_training': False,
        'isolation_forest': {'trees': 350, 'contamination': 0.11, 'flag_count': int((iso_pred == -1).sum()), 'stored_flag_match_rate': round(iso_match,4)},
        'kmeans': {'clusters': 4, 'rerun_cluster_sizes': rerun_sizes, 'stored_cluster_sizes': expected_sizes},
        'combined_queue_validation': {
            'precision': round(float(precision_score(truth, detected, zero_division=0)),4),
            'recall': round(float(recall_score(truth, detected, zero_division=0)),4),
            'f1': round(float(f1_score(truth, detected, zero_division=0)),4),
        },
        'responsible_use': 'Anomaly scores and alerts prioritize human review; they are not proof of fraud.'
    }
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
