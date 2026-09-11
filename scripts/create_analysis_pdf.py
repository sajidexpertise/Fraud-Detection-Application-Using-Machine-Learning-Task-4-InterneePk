from pathlib import Path
import json, csv
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'/'analysis-summary.pdf'
IMG=ROOT/'outputs'/'dashboard-screenshot.png'
MODEL=json.loads((ROOT/'models'/'model_summary.json').read_text(encoding='utf-8'))
with (ROOT/'data'/'task4_dataset.csv').open(newline='',encoding='utf-8') as f:
    rows=list(csv.DictReader(f))

n=len(rows); sus=sum(r['alert_level']!='Normal' for r in rows); high=sum(r['alert_level'] in ('High','Critical') for r in rows)
dup=sum(int(r['duplicate_signal']) for r in rows); rapid=sum(int(r['rapid_submission_signal']) for r in rows); inc=sum(int(r['inconsistent_data_signal']) for r in rows); iso=sum(int(r['isolation_flag']) for r in rows)

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Title2',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=22,leading=26,textColor=colors.HexColor('#0B5B52'),alignment=TA_CENTER,spaceAfter=10))
styles.add(ParagraphStyle(name='Sub',parent=styles['BodyText'],fontSize=10,leading=14,textColor=colors.HexColor('#536B70'),alignment=TA_CENTER,spaceAfter=10))
styles.add(ParagraphStyle(name='H2x',parent=styles['Heading2'],fontName='Helvetica-Bold',fontSize=15,textColor=colors.HexColor('#0B5B52'),spaceBefore=8,spaceAfter=7))
styles.add(ParagraphStyle(name='Bodyx',parent=styles['BodyText'],fontSize=9,leading=13,textColor=colors.HexColor('#263B3F'),spaceAfter=5))
styles.add(ParagraphStyle(name='Smallx',parent=styles['BodyText'],fontSize=8,leading=11,textColor=colors.HexColor('#60777B')))

def footer(canvas,doc):
    canvas.saveState();canvas.setFont('Helvetica',7);canvas.setFillColor(colors.HexColor('#708589'))
    canvas.drawString(15*mm,10*mm,'Internee.pk Task 4 - Fraud Detection in Applications | Sajid Ali')
    canvas.drawRightString(195*mm,10*mm,f'Page {doc.page}');canvas.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=14*mm,leftMargin=14*mm,topMargin=14*mm,bottomMargin=16*mm,title='Fraud Detection in Applications - Task 4',author='Sajid Ali')
story=[]
story += [Paragraph('Fraud Detection in Applications',styles['Title2']),Paragraph('Internee.pk Data Analyst Internship - Task 4 (Major Project)<br/>Prepared by Sajid Ali, Data Analyst Intern',styles['Sub'])]
if IMG.exists():
    im=Image(str(IMG)); im._restrictSize(180*mm,108*mm); story += [im,Spacer(1,5*mm)]
summary_data=[['Applications','Suspicious','High/Critical','Duplicate','Rapid','Inconsistent','IF Flags'],[f'{n}',f'{sus}',f'{high}',f'{dup}',f'{rapid}',f'{inc}',f'{iso}']]
t=Table(summary_data,colWidths=[25*mm]*7)
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0B5B52')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,1),(-1,-1),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('BACKGROUND',(0,1),(-1,1),colors.HexColor('#EAF7F4')),('BOX',(0,0),(-1,-1),.5,colors.HexColor('#B9D8D2')),('INNERGRID',(0,0),(-1,-1),.25,colors.HexColor('#D7E8E5')),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
story += [t,Spacer(1,4*mm),Paragraph('Objective',styles['H2x']),Paragraph('Identify anomalies in internship applications to prevent fake or repeated entries. The project analyzes duplicate patterns, rapid submissions, and inconsistent data, then applies Isolation Forest and K-Means Clustering to prioritize suspicious applications for human review.',styles['Bodyx']),Paragraph('Responsible-use principle: a suspicious score or model flag is not proof of fraud and must not be used as an automatic rejection decision.',styles['Smallx']),PageBreak()]

story += [Paragraph('Methodology and Task 4 Coverage',styles['H2x'])]
method=[
 ['Requirement','Implementation'],
 ['Duplicate entries','Repeated email, phone and CV fingerprints plus duplicate group counts.'],
 ['Rapid submissions','Submission gaps, device/IP 24-hour activity and very fast form completion.'],
 ['Inconsistent data','CGPA/scale, semester/graduation timing, availability and short-form contradictions.'],
 ['Isolation Forest','350-tree unsupervised model on 16 standardized engineered features with 11% contamination.'],
 ['K-Means','4-cluster behavior segmentation with 25 initializations.'],
 ['Suspicious alerts','Combined risk score, alert level, explainable reason and interactive review queue.']
]
t=Table(method,colWidths=[43*mm,130*mm],repeatRows=1)
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0B5B52')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(0,-1),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#CADFDC')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F4FAF9')]),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
story += [t,Spacer(1,5*mm),Paragraph('Model Validation on Synthetic Reference Scenarios',styles['H2x'])]
v=MODEL['validation']
val=[['Metric','Result'],['Synthetic anomalies planted',str(v['synthetic_truth_anomalies'])],['Isolation Forest flagged',str(v['isolation_forest_flagged'])],['High/Critical queue',str(v['high_or_critical'])],['Precision',f"{v['precision_high_or_critical_vs_synthetic_reference']*100:.2f}%"],['Recall',f"{v['recall_high_or_critical_vs_synthetic_reference']*100:.2f}%"],['F1',f"{v['f1_high_or_critical_vs_synthetic_reference']*100:.2f}%"]]
t=Table(val,colWidths=[90*mm,45*mm])
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#153C42')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('ALIGN',(1,1),(1,-1),'CENTER'),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#D3E3E0')),('FONTSIZE',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story += [t,Spacer(1,4*mm),Paragraph('The reference label is excluded from unsupervised model fitting and is used only to check whether the portfolio experiment surfaces deliberately planted anomaly scenarios.',styles['Smallx']),PageBreak()]

story += [Paragraph('Key Findings and Manager Recommendations',styles['H2x'])]
findings=[
 ('Duplicate behavior is a major review signal',f'{dup} of {n} applications contain a duplicate email, phone or CV pattern in the full synthetic dataset.'),
 ('Rapid behavior is visible in burst patterns',f'{rapid} applications meet at least one rapid-submission condition, including very short form completion or repeated device/IP activity.'),
 ('Inconsistency checks add explainability',f'{inc} records trigger one or more internal consistency rules.'),
 ('Isolation Forest adds multivariate anomaly detection',f'{iso} applications are flagged by the unsupervised model, including cases that may not be obvious from a single rule.'),
 ('Human review remains essential','Use model and rule outputs to prioritize review. Verify evidence before accepting, rejecting or escalating an application.')
]
for i,(h,b) in enumerate(findings,1):
    story += [KeepTogether([Paragraph(f'<b>{i}. {h}</b>',styles['Bodyx']),Paragraph(b,styles['Smallx']),Spacer(1,2*mm)])]
story += [Paragraph('Recommended Controls',styles['H2x'])]
for txt in [
 'Validate and deduplicate email, phone and CV fingerprints during submission.',
 'Apply sensible rate limits and review repeated rapid activity by device and hashed network identifier.',
 'Validate academic and availability fields at data-entry time to reduce contradictions.',
 'Prioritize Critical and High alerts first, then review a sample of medium-risk cases.',
 'Re-evaluate model thresholds and cluster behavior as application patterns change.',
 'Do not use location, university or other contextual attributes as automatic fraud indicators.'
]:
    story.append(Paragraph('• '+txt,styles['Bodyx']))
story += [Spacer(1,5*mm),Paragraph('Deliverables',styles['H2x']),Paragraph('Interactive HTML dashboard, local CSS/JavaScript, 720-row CSV, formatted Excel audit workbook, data dictionary, Python generation and ML validation scripts, README, submission guide, checklist, LinkedIn post draft, demo-video script, Windows launcher, dashboard screenshot, and this analysis summary.',styles['Bodyx'])]

doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
