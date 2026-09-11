# Fraud Detection in Applications

**Internee.pk Data Analyst Internship - Task 4 (Major Project)**  
**Author:** Sajid Ali  
**Role:** Data Analyst Intern, Internee.pk  
**Education:** BS Information Technology, Shah Abdul Latif University, Khairpur  
**Location:** Sindh, Pakistan

## Project Overview

This project identifies unusual patterns in internship applications so suspicious entries can be prioritized for human review. It focuses on the three behaviors required by Task 4: **duplicate entries, rapid submissions, and inconsistent data**, and then strengthens the review process with **Isolation Forest** anomaly detection and **K-Means Clustering**.

The main deliverable is an interactive browser dashboard inspired by a professional fraud-operations command center. It opens locally from `index.html`, works without an internet connection, uses a **dark theme by default**, and includes a working **day/night theme toggle**.

> **Responsible-use note:** A suspicious score or model flag is not proof of fraud. The dashboard is designed to prioritize manual review, not to automatically reject applicants.

## Task 4 Objective

> Identify anomalies in internship applications to prevent fake entries.

### Required Task Coverage

- Analyze patterns of duplicate entries.
- Analyze rapid or burst submissions.
- Identify inconsistent application data.
- Use Isolation Forest for anomaly detection.
- Use K-Means Clustering for pattern grouping.
- Implement alerts for suspicious behavior.

All six requirements are implemented in the dataset, scripts, model outputs, alert queue, and interactive dashboard.

## Business Questions

The analysis is designed to answer practical questions such as:

1. How many applications are normal, suspicious, high risk, or critical?
2. Which departments and cities contain the highest concentration of suspicious applications?
3. Which applications reuse the same email address, phone number, or CV fingerprint?
4. Are multiple applications arriving rapidly from the same device or hashed network identifier?
5. Are there internally inconsistent academic or availability fields?
6. Which records are unusual according to Isolation Forest?
7. What recurring behavior profiles are discovered by K-Means?
8. Which applications should be reviewed first by an internship operations team?

## Dataset

The project uses a **realistic synthetic portfolio dataset** because no confidential Internee.pk applicant data is included.

- **Rows:** 720 internship applications
- **Columns:** 45 analytical and supporting fields
- **Period:** July 2026
- **Departments:** Data Analytics, Business Intelligence, Web Development, Cloud & DevOps, QA & Testing, UI/UX Design
- **Geography:** Synthetic Pakistan-based city distribution
- **Synthetic planted scenarios:** normal applications, duplicate entries, rapid-submission bursts, inconsistent entries, and multi-signal entries

The planted reference labels are used only for portfolio validation. They are **not used as features when fitting Isolation Forest or K-Means**.

### Main Data Fields

| Field | Purpose |
|---|---|
| `application_id` | Unique synthetic application ID |
| `submitted_at` | Application timestamp |
| `applicant_name`, `email`, `phone` | Synthetic identity/contact fields |
| `device_id`, `ip_hash`, `cv_hash` | Behavioral identifiers used for reuse/burst analysis |
| `department`, `university`, `degree`, `city` | Segmentation and context |
| `semester`, `graduation_year`, `cgpa`, `cgpa_scale` | Academic consistency checks |
| `form_completion_seconds` | Submission-speed feature |
| `device_applications_24h`, `ip_applications_24h` | Burst activity features |
| `duplicate_signal` | Explainable duplicate-entry flag |
| `rapid_submission_signal` | Explainable rapid/burst flag |
| `inconsistent_data_signal` | Explainable consistency flag |
| `isolation_flag` | Isolation Forest anomaly flag |
| `isolation_anomaly_percentile` | Relative anomaly intensity, 0-100 |
| `kmeans_cluster` | K-Means cluster assignment |
| `cluster_profile` | Human-readable behavior profile |
| `risk_score` | Combined 0-100 review-priority score |
| `alert_level` | Normal, Review, High, or Critical |
| `alert_reason` | Explainable review reason |

See `data/data_dictionary.csv` and the **Data Dictionary** sheet in `data/task4_dataset.xlsx` for the full field-level documentation.

## Tools and Technologies

### Data and Machine Learning

- Python
- Pandas
- NumPy
- Scikit-learn
- Isolation Forest
- K-Means Clustering
- StandardScaler

### Dashboard

- HTML5
- CSS3
- Vanilla JavaScript
- Local embedded dashboard data (`src/data.js`)
- Custom responsive SVG charts

No Power BI file is required by the Task 4 instructions. The browser dashboard was selected because it allows fully working filters, alerts, tooltips, record review, CSV export, printing, mobile responsiveness, and offline use while keeping the Python ML workflow visible in the repository.

## Analysis Methodology

### 1. Duplicate Entry Detection

The project counts repeated identity and document fingerprints across:

- Email address
- Phone number
- CV fingerprint (`cv_hash`)

If one or more identity/document values are reused, the application receives a duplicate signal. Duplicate behavior increases review priority but is not automatically treated as fraudulent because legitimate reuse can occur.

### 2. Rapid Submission Detection

Rapid behavior is evaluated using:

- Minutes since the previous submission from the same device
- Minutes since the previous submission from the same hashed network identifier
- Number of applications from the same device in 24 hours
- Number of applications from the same network identifier in 24 hours
- Very short form-completion time

This detects bursts and unusually fast submissions that may indicate automation, repeated entries, or a shared submission source.

### 3. Inconsistent Data Detection

Consistency rules examine examples such as:

- CGPA exceeding the declared scale
- Semester and graduation-year combinations that do not make sense for the application period
- Implausibly high weekly availability
- Extremely short written responses combined with very fast form completion

Each application receives an inconsistency count and an explainable consistency signal.

### 4. Isolation Forest

Isolation Forest is trained on 16 engineered behavioral/application features.

- Trees: **350**
- Contamination: **11%**
- Random seed: **42**
- Output: anomaly flag, decision score, and anomaly percentile

The algorithm isolates rare multivariate patterns without using the planted synthetic fraud label.

### 5. K-Means Clustering

K-Means groups applications into four behavior clusters.

- Number of clusters: **4**
- Initializations: **25**
- Random seed: **42**

Current cluster profiles include typical behavior, identity reuse, rapid submission, and data inconsistency patterns. Cluster IDs are mathematical labels and can change if the model configuration changes.

### 6. Combined Review Risk

The final `risk_score` combines:

- Isolation Forest anomaly percentile
- Explainable duplicate/rapid/inconsistent rule points
- Cluster-level behavior risk
- Additional weighting for multiple strong behavioral signals

The score is used only for review prioritization.

## KPI Definitions

| KPI | Definition |
|---|---|
| Total Applications | Number of records after current filters |
| Suspicious Applications | Applications with alert level other than Normal |
| Fraud / Anomaly Rate | Suspicious applications divided by current application count |
| Duplicate Clusters | Repeated email, phone, and CV groups in the filtered view |
| Rapid Submission Bursts | Distinct devices associated with rapid-submission signals |
| High-Risk Cities | Cities with at least five records and a High/Critical share of 12% or more |

All dashboard KPIs recalculate when filters are applied.

## Dashboard Features

The dashboard intentionally uses a dark forensic-operations visual identity with teal, amber, red, purple, and cyan accents. The **dark theme is the default**.

Working features include:

- Day/night theme toggle
- Date-from and date-to filters
- Department filter
- City filter
- Alert-level filter
- Functional model filter:
  - Combined Risk
  - Isolation Forest Flagged
  - K-Means High-Risk Cluster
- Application/email/name search
- Apply Filters
- Reset Filters
- Dynamic KPI recalculation
- Dynamic chart recalculation
- CSV download of the current filtered rows
- Print / Export using the browser print dialog
- Responsive desktop, tablet, and mobile layout
- Empty-state display when no rows match
- Sortable/paginated application table
- Fraud alert queue
- Clickable `View` / `Review` buttons with an application detail modal
- Model Analytics tab
- Management Reports tab

### Main Dashboard Charts

1. **Anomaly Trend Over Time** - total applications vs suspicious activity by day.
2. **Suspicious Cases by Department** - total and suspicious records by internship department.
3. **Alert Composition** - mutually exclusive primary alert categories.
4. **Top Risky Cities** - ranking by suspicious application volume.
5. **Submission Speed vs Anomaly Score** - relationship between form-completion speed and Isolation Forest anomaly percentile.
6. **Duplicate Email / Phone / IP Patterns** - department-level heatmap of repeated identifiers.
7. **Isolation Forest Distribution** - anomaly-percentile distribution in Model Analytics.
8. **K-Means Cluster Risk Profiles** - average combined risk by cluster.

## Current Full-Dataset Results

With no dashboard filters applied:

- Total applications: **720**
- Suspicious / review-or-higher: **121**
- High or Critical: **117**
- Duplicate-signal records: **80**
- Rapid-submission records: **39**
- Inconsistent-data records: **20**
- Isolation Forest anomalies: **80**
- Synthetic-reference precision for High/Critical queue: **65.81%**
- Synthetic-reference recall: **96.25%**
- Synthetic-reference F1: **78.17%**

These validation metrics describe performance against deliberately planted synthetic scenarios. They do not represent production fraud-detection accuracy.

## Key Findings

- Duplicate identity/CV reuse is a major source of review activity in the synthetic portfolio dataset.
- Rapid bursts are concentrated in repeated device/network behavior and very short form-completion times.
- Isolation Forest helps identify multivariate outliers that may not trigger a single hard rule.
- K-Means provides a useful behavioral segmentation layer rather than a fraud/legitimate classifier.
- Combining rule-based evidence with unsupervised model signals creates a more explainable review queue than using a model score alone.

## Practical Recommendations

1. Add email, phone, and CV fingerprint deduplication during application submission.
2. Add submission rate limits and device/network monitoring for repeated rapid entries.
3. Use form-completion timing as a supporting risk feature, not as a standalone rejection rule.
4. Validate academic fields at entry time to reduce contradictory records.
5. Review Critical and High applications first, while preserving a documented human-review process.
6. Periodically retrain/re-evaluate anomaly models as legitimate applicant behavior changes.
7. Avoid using city, university, or other contextual attributes as automatic fraud indicators.

## Folder Structure

```text
Task_4_Fraud_Detection_Applications/
├── index.html
├── README.md
├── SUBMISSION_GUIDE.md
├── PROJECT_CHECKLIST.md
├── linkedin_post.txt
├── video_demo_script.md
├── requirements.txt
├── OPEN_DASHBOARD.bat
├── data/
│   ├── task4_dataset.csv
│   ├── task4_dataset.xlsx
│   └── data_dictionary.csv
├── assets/
│   ├── internshield-mark.svg
│   └── dashboard-preview.png
├── src/
│   ├── app.js
│   ├── data.js
│   └── styles.css
├── scripts/
│   ├── data_generation.py
│   ├── fraud_detection_ml.py
│   └── validate_project.py
├── models/
│   └── model_summary.json
└── outputs/
    ├── dashboard-screenshot.png
    ├── analysis-summary.pdf
    ├── browser-qa-results.txt
    └── project-validation.txt
```

## How to Run on Windows

### Method 1 - Direct, easiest method

1. Extract the ZIP file.
2. Open the `Task_4_Fraud_Detection_Applications` folder.
3. Double-click `index.html`.
4. The dashboard opens in Chrome, Edge, or your default browser.

The dashboard does **not** need Python for normal viewing because all dashboard data is stored locally in `src/data.js`.

### Method 2 - Use the Windows launcher

Double-click:

```text
OPEN_DASHBOARD.bat
```

The launcher checks that `index.html` exists and opens it directly.

### Method 3 - Optional local server mode

Run from Command Prompt:

```bat
OPEN_DASHBOARD.bat server
```

The launcher checks Python in this order:

1. `C:\Python314\python.exe`
2. `python`
3. `py -3`

If Python is found, it starts:

```text
http://127.0.0.1:8000/index.html
```

If Python is missing, the launcher shows a readable error and reminds you that direct `index.html` mode still works.

## Re-run the Machine-Learning Check

Optional: create a virtual environment and install the requirements.

```bash
pip install -r requirements.txt
```

Then run:

```bash
python scripts/fraud_detection_ml.py
```

This writes a recheck summary to:

```text
outputs/ml_recheck_summary.json
```

To recreate the synthetic dataset/model outputs from the generation script:

```bash
python scripts/data_generation.py
```

If the dataset is regenerated, rebuild the Excel workbook if you want the formatted audit workbook to reflect the regenerated data.

## Open on Mobile

### From the extracted project

If your Android file manager/browser allows local HTML files:

1. Extract the ZIP.
2. Navigate to the project folder.
3. Tap `index.html`.
4. Choose Chrome if prompted.

### Recommended mobile method

Deploy the project to GitHub Pages and open the live URL. This avoids local-file restrictions on some mobile browsers.

## Upload to GitHub

Recommended repository name:

```text
Fraud-Detection-Applications-Task-4-InterneePk
```

1. Sign in to GitHub.
2. Create a new public repository with the recommended name.
3. Extract this ZIP on your computer.
4. Upload the **contents inside** `Task_4_Fraud_Detection_Applications` so `index.html` is at the repository root.
5. Commit the files.

Do not claim a repository URL until GitHub has actually created it.

## Deploy with GitHub Pages

1. Open the repository.
2. Go to **Settings**.
3. Open **Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**.
5. Branch: `main`.
6. Folder: `/(root)`.
7. Click **Save**.
8. Wait for GitHub Pages to finish deployment.

Expected URL format:

```text
https://sajidexpertise.github.io/Fraud-Detection-Applications-Task-4-InterneePk/
```

Use the actual URL GitHub shows after deployment.

## Update Live Links

After creating the repository and live dashboard, replace these placeholders in `linkedin_post.txt`:

```text
<GITHUB_REPOSITORY_URL>
<LIVE_DASHBOARD_URL>
```

Then use the final links in your Internee.pk submission.

## Known Limitations

- The dataset is synthetic and intentionally contains planted anomaly patterns for educational portfolio validation.
- Isolation Forest and K-Means are unsupervised and do not establish fraud as ground truth.
- Risk thresholds are demonstration thresholds rather than production policy.
- Hashed network/device identifiers are synthetic and do not represent real tracking data.
- The browser dashboard reads pre-generated model results; it does not train Scikit-learn inside the browser.
- Printing uses the browser print dialog; choose **Save as PDF** if you need a PDF export.

## Ethical and Data Note

No confidential internship applications, real IP addresses, real CV files, or private applicant records are used. The project demonstrates responsible anomaly-review concepts using synthetic portfolio data. Any real implementation should define retention limits, access controls, human-review standards, appeal processes, and bias/privacy testing before operational use.

## Credits

**Sajid Ali**  
Data Analyst Intern - Internee.pk  
BS Information Technology - Shah Abdul Latif University, Khairpur  
Sindh, Pakistan  
GitHub: `sajidexpertise`  
LinkedIn: `https://www.linkedin.com/in/sajidexpertise`  
Portfolio: `https://sajidexpertise.vercel.app/`
