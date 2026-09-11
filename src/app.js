(() => {
  'use strict';
  const payload = window.TASK4_DATA || {records:[], model_metrics:{}};
  const all = (payload.records || []).map(r => ({...r, _date:new Date(r.submitted_at)}));
  let filtered = [...all], currentTab = 'dashboard', page = 1, sortDir = 'desc';
  const PAGE_SIZE = 24;
  const $ = id => document.getElementById(id);
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const fmt = n => Number(n || 0).toLocaleString('en-US');
  const pct = (a,b) => b ? (100*a/b) : 0;
  const mean = a => a.length ? a.reduce((s,v)=>s+Number(v||0),0)/a.length : 0;
  const uniq = a => [...new Set(a)];
  const slug = s => String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,'-');
  const suspicious = r => r.alert_level !== 'Normal';
  const highRisk = r => ['Critical','High'].includes(r.alert_level);
  const color = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  function showToast(msg){const t=$('toast');t.textContent=msg;t.classList.add('show');clearTimeout(showToast._t);showToast._t=setTimeout(()=>t.classList.remove('show'),2200)}
  function minmaxDate(){const ds=all.map(r=>r._date).filter(d=>!isNaN(d));return [new Date(Math.min(...ds)),new Date(Math.max(...ds))]}
  function dateValue(d){return d.toISOString().slice(0,10)}
  function primarySignal(r){
    const s=[]; if(r.duplicate_signal)s.push('Duplicate'); if(r.rapid_submission_signal)s.push('Rapid Submission'); if(r.inconsistent_data_signal)s.push('Inconsistent Data');
    if(s.length>1) return 'Multiple Signals'; if(s.length===1) return s[0]; if(r.isolation_flag) return 'ML Anomaly'; return 'No Alert';
  }
  function duplicateClusterCount(rows){
    let groups=0;
    ['email','phone','cv_hash'].forEach(k=>{const m={};rows.forEach(r=>m[r[k]]=(m[r[k]]||0)+1);groups += Object.values(m).filter(v=>v>1).length;});
    return groups;
  }
  function rapidBurstCount(rows){return uniq(rows.filter(r=>r.rapid_submission_signal).map(r=>r.device_id)).length}
  function highRiskCityCount(rows){
    const m={};rows.forEach(r=>{m[r.city]??={n:0,s:0};m[r.city].n++;if(highRisk(r))m[r.city].s++;});
    return Object.values(m).filter(v=>v.n>=5 && v.s/v.n>=.12).length;
  }

  function setup(){
    document.documentElement.dataset.theme='dark';
    const [mn,mx]=minmaxDate(); $('fromDate').value=dateValue(mn); $('toDate').value=dateValue(mx);
    const fill=(id,vals)=>{const s=$(id);vals.sort().forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=v;s.appendChild(o)})};
    fill('departmentFilter',uniq(all.map(r=>r.department))); fill('cityFilter',uniq(all.map(r=>r.city)));
    document.querySelectorAll('.nav-btn').forEach(b=>b.addEventListener('click',()=>switchTab(b.dataset.tab)));
    document.querySelectorAll('[data-tab-jump]').forEach(b=>b.addEventListener('click',()=>switchTab(b.dataset.tabJump)));
    $('applyFilters').addEventListener('click',applyFilters); $('resetFilters').addEventListener('click',resetFilters); $('emptyReset').addEventListener('click',resetFilters);
    $('downloadCsv').addEventListener('click',downloadCSV); $('printReport').addEventListener('click',()=>window.print()); $('reportPrint').addEventListener('click',()=>window.print());
    $('themeToggle').addEventListener('click',toggleTheme); $('mobileMenu').addEventListener('click',()=>$('sidebar').classList.toggle('open'));
    $('sortField').addEventListener('change',()=>{page=1;renderApplications()}); $('sortDirection').addEventListener('click',()=>{sortDir=sortDir==='desc'?'asc':'desc';$('sortDirection').dataset.dir=sortDir;$('sortDirection').textContent=sortDir==='desc'?'Descending ↓':'Ascending ↑';renderApplications()});
    $('prevPage').addEventListener('click',()=>{if(page>1){page--;renderApplications()}}); $('nextPage').addEventListener('click',()=>{page++;renderApplications()});
    let timer; $('globalSearch').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(applyFilters,260)});
    $('globalSearch').addEventListener('keydown',e=>{if(e.key==='Enter')applyFilters()});
    document.addEventListener('click',e=>{const v=e.target.closest('[data-view-id]');if(v)openRecord(v.dataset.viewId);if(e.target.matches('[data-close-modal]'))closeModal()});
    document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal()});
    renderAll();
  }

  function switchTab(tab){
    currentTab=tab; document.querySelectorAll('.tab-panel').forEach(p=>p.classList.toggle('active',p.id===tab)); document.querySelectorAll('.nav-btn').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));
    $('sidebar').classList.remove('open'); if(tab==='applications')renderApplications(); if(tab==='alerts')renderAlerts(); if(tab==='models')renderModels(); if(tab==='reports')renderReports(); window.scrollTo({top:0,behavior:'smooth'});
  }
  function toggleTheme(){const light=document.documentElement.dataset.theme==='light';document.documentElement.dataset.theme=light?'dark':'light';$('themeIcon').textContent=light?'☾':'☀';renderCharts();showToast(light?'Dark mode enabled':'Light mode enabled')}

  function filterConfig(){return {from:$('fromDate').value,to:$('toDate').value,department:$('departmentFilter').value,city:$('cityFilter').value,alert:$('alertFilter').value,model:$('modelFilter').value,search:$('globalSearch').value.trim().toLowerCase()}}
  function filterRecords(rows,cfg){
    const from=cfg.from?new Date(cfg.from+'T00:00:00'):null,to=cfg.to?new Date(cfg.to+'T23:59:59'):null;
    return rows.filter(r=>{
      if(from && r._date<from)return false;if(to && r._date>to)return false;if(cfg.department && r.department!==cfg.department)return false;if(cfg.city && r.city!==cfg.city)return false;if(cfg.alert && r.alert_level!==cfg.alert)return false;
      if(cfg.model==='isolation' && !r.isolation_flag)return false;if(cfg.model==='kmeans' && Number(r.cluster_risk_index)<60)return false;
      if(cfg.search){const hay=[r.application_id,r.applicant_name,r.email,r.phone,r.device_id,r.ip_hash,r.department,r.city,r.university].join(' ').toLowerCase();if(!hay.includes(cfg.search))return false;}
      return true;
    });
  }
  function applyFilters(){filtered=filterRecords(all,filterConfig());page=1;renderAll();showToast(`${filtered.length} applications in current view`)}
  function resetFilters(){const [mn,mx]=minmaxDate();$('fromDate').value=dateValue(mn);$('toDate').value=dateValue(mx);$('departmentFilter').value='';$('cityFilter').value='';$('alertFilter').value='';$('modelFilter').value='combined';$('globalSearch').value='';filtered=[...all];page=1;renderAll();showToast('Filters reset')}

  function renderAll(){
    const empty=!filtered.length; $('emptyState').hidden=!empty; document.querySelectorAll('.tab-panel').forEach(p=>p.style.display=empty?'none':'');
    if(empty){$('filterSummary').textContent='0 applications in current view';return;} else {document.querySelectorAll('.tab-panel').forEach(p=>p.style.display='');switchTabSilently(currentTab)}
    $('filterSummary').textContent=`Current view: ${fmt(filtered.length)} of ${fmt(all.length)} applications · ${fmt(filtered.filter(suspicious).length)} suspicious · filters update every KPI, chart and review table.`;
    $('alertBadge').textContent=filtered.filter(suspicious).length;
    renderKPIs(); renderCharts(); renderRecent(); renderInsights(); renderApplications(); renderAlerts(); renderModels(); renderReports();
  }
  function switchTabSilently(tab){document.querySelectorAll('.tab-panel').forEach(p=>p.classList.toggle('active',p.id===tab));document.querySelectorAll('.nav-btn').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab))}

  function renderKPIs(){
    const n=filtered.length,s=filtered.filter(suspicious).length,dups=duplicateClusterCount(filtered),bursts=rapidBurstCount(filtered),cities=highRiskCityCount(filtered),high=filtered.filter(highRisk).length;
    const items=[
      ['◎','Total Applications',fmt(n),`${pct(n,all.length).toFixed(1)}% of full dataset`],
      ['△','Suspicious Applications',fmt(s),`${pct(s,n).toFixed(1)}% review share`],
      ['◇','Fraud / Anomaly Rate',`${pct(s,n).toFixed(1)}%`,`${fmt(high)} high or critical`],
      ['≋','Duplicate Clusters',fmt(dups),`${fmt(filtered.filter(r=>r.duplicate_signal).length)} records affected`],
      ['ϟ','Rapid Submission Bursts',fmt(bursts),`${fmt(filtered.filter(r=>r.rapid_submission_signal).length)} rapid records`],
      ['⌖','High-Risk Cities',fmt(cities),`≥12% high/critical share`]
    ];
    $('kpiGrid').innerHTML=items.map(x=>`<article class="kpi-card"><div class="kpi-icon">${x[0]}</div><div><span class="kpi-label">${x[1]}</span><div class="kpi-value">${x[2]}</div><div class="kpi-sub"><b>●</b> ${x[3]}</div></div></article>`).join('');
  }

  const svgWrap=(content,w,h)=>`<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" role="img">${content}</svg>`;
  function renderCharts(){renderTrend();renderDepartment();renderDonut();renderCities();renderScatter();renderHeatmap();renderIsoHistogram();renderClusters()}
  function dayKey(d){return d.toISOString().slice(0,10)}
  function renderTrend(){
    const hst={};filtered.forEach(r=>{const k=dayKey(r._date);hst[k]??={t:0,s:0};hst[k].t++;if(suspicious(r))hst[k].s++});const data=Object.entries(hst).sort((a,b)=>a[0].localeCompare(b[0]));
    const host=$('trendChart');if(!data.length){host.innerHTML='';return}const w=560,h=215,p={l:38,r:10,t:14,b:30},iw=w-p.l-p.r,ih=h-p.t-p.b,max=Math.max(...data.map(d=>d[1].t),1);let s='';
    for(let i=0;i<=4;i++){const y=p.t+ih*i/4,val=Math.round(max*(1-i/4));s+=`<line class="gridline" x1="${p.l}" y1="${y}" x2="${p.l+iw}" y2="${y}"/><text class="axis" x="${p.l-6}" y="${y+3}" text-anchor="end">${val}</text>`}
    const points=(key)=>data.map((d,i)=>`${p.l+iw*i/Math.max(1,data.length-1)},${p.t+ih-ih*d[1][key]/max}`).join(' ');
    s+=`<polyline points="${points('t')}" fill="none" stroke="${color('--teal')}" stroke-width="2.5"/><polyline points="${points('s')}" fill="none" stroke="${color('--amber')}" stroke-width="2.5"/>`;
    data.forEach((d,i)=>{const x=p.l+iw*i/Math.max(1,data.length-1),yt=p.t+ih-ih*d[1].t/max,ys=p.t+ih-ih*d[1].s/max;s+=`<circle cx="${x}" cy="${yt}" r="2.5" fill="${color('--teal')}"><title>${d[0]} · Total ${d[1].t}</title></circle><circle cx="${x}" cy="${ys}" r="2.5" fill="${color('--amber')}"><title>${d[0]} · Suspicious ${d[1].s}</title></circle>`});
    const tick=Math.max(1,Math.floor(data.length/5));data.forEach((d,i)=>{if(i%tick===0||i===data.length-1)s+=`<text class="axis" x="${p.l+iw*i/Math.max(1,data.length-1)}" y="${h-8}" text-anchor="middle">${d[0].slice(5)}</text>`});host.innerHTML=svgWrap(s,w,h);
  }
  function renderDepartment(){
    const m={};filtered.forEach(r=>{m[r.department]??={t:0,s:0};m[r.department].t++;if(suspicious(r))m[r.department].s++});const data=Object.entries(m).sort((a,b)=>b[1].t-a[1].t);const host=$('departmentChart'),w=520,h=215,p={l:34,r:8,t:10,b:42},iw=w-p.l-p.r,ih=h-p.t-p.b,max=Math.max(...data.map(d=>d[1].t),1),group=iw/Math.max(1,data.length);let s='';
    for(let i=0;i<=3;i++){const y=p.t+ih*i/3,val=Math.round(max*(1-i/3));s+=`<line class="gridline" x1="${p.l}" y1="${y}" x2="${p.l+iw}" y2="${y}"/><text class="axis" x="${p.l-5}" y="${y+3}" text-anchor="end">${val}</text>`}
    data.forEach((d,i)=>{const x=p.l+i*group+group*.18,bw=group*.27,ht=ih*d[1].t/max,hs=ih*d[1].s/max;s+=`<rect x="${x}" y="${p.t+ih-ht}" width="${bw}" height="${ht}" rx="2" fill="${color('--teal')}"><title>${d[0]} · Total ${d[1].t}</title></rect><rect x="${x+bw+3}" y="${p.t+ih-hs}" width="${bw}" height="${hs}" rx="2" fill="${color('--amber')}"><title>${d[0]} · Suspicious ${d[1].s}</title></rect><text class="axis" x="${x+bw}" y="${h-19}" text-anchor="middle" transform="rotate(-28 ${x+bw} ${h-19})">${esc(d[0].replace(' Development',' Dev'))}</text>`});host.innerHTML=svgWrap(s,w,h)
  }
  function renderDonut(){
    const counts={'Duplicate':0,'Rapid Submission':0,'Inconsistent Data':0,'Multiple Signals':0,'ML Anomaly':0};filtered.filter(suspicious).forEach(r=>{const p=primarySignal(r);if(counts[p]!==undefined)counts[p]++});const entries=Object.entries(counts).filter(x=>x[1]>0),total=entries.reduce((a,b)=>a+b[1],0);const host=$('signalDonut');if(!total){host.innerHTML='<div style="padding:30px;color:var(--muted)">No suspicious alerts in this view.</div>';return}const cols=[color('--teal'),color('--amber'),color('--red'),color('--purple'),color('--cyan')];let offset=0,cir=2*Math.PI*42,s=`<g transform="translate(92 98) rotate(-90)">`;
    entries.forEach((e,i)=>{const len=cir*e[1]/total;s+=`<circle r="42" cx="0" cy="0" fill="none" stroke="${cols[i]}" stroke-width="21" stroke-dasharray="${len} ${cir-len}" stroke-dashoffset="${-offset}"><title>${e[0]}: ${e[1]} (${pct(e[1],total).toFixed(1)}%)</title></circle>`;offset+=len});s+=`</g><text x="92" y="94" text-anchor="middle" fill="${color('--text')}" font-size="22" font-weight="800">${total}</text><text x="92" y="108" text-anchor="middle" class="axis">Alerts</text>`;
    entries.forEach((e,i)=>{const y=38+i*29;s+=`<circle cx="178" cy="${y}" r="5" fill="${cols[i]}"/><text x="189" y="${y+3}" fill="${color('--text')}" font-size="9">${esc(e[0])}</text><text x="292" y="${y+3}" class="axis" text-anchor="end">${pct(e[1],total).toFixed(0)}%</text>`});host.innerHTML=svgWrap(s,305,210)
  }
  function renderCities(){
    const m={};filtered.forEach(r=>{m[r.city]??={n:0,s:0,r:[]};m[r.city].n++;if(suspicious(r))m[r.city].s++;m[r.city].r.push(r.risk_score)});const data=Object.entries(m).map(([k,v])=>({k,s:v.s,avg:mean(v.r)})).sort((a,b)=>b.s-a.s||b.avg-a.avg).slice(0,8);const host=$('cityChart'),w=430,h=215,p={l:88,r:24,t:10,b:20},iw=w-p.l-p.r,ih=h-p.t-p.b,max=Math.max(...data.map(d=>d.s),1),bh=ih/Math.max(1,data.length)*.58;let s='';
    data.forEach((d,i)=>{const y=p.t+i*ih/data.length+4,width=iw*d.s/max;s+=`<text class="axis" x="${p.l-7}" y="${y+bh*.75}" text-anchor="end">${esc(d.k)}</text><rect x="${p.l}" y="${y}" width="${Math.max(2,width)}" height="${bh}" rx="2" fill="${color('--teal')}"><title>${d.k}: ${d.s} suspicious · average risk ${d.avg.toFixed(1)}</title></rect><text class="axis" x="${p.l+Math.max(2,width)+5}" y="${y+bh*.75}">${d.s}</text>`});host.innerHTML=svgWrap(s,w,h)
  }
  function renderScatter(){
    const host=$('scatterChart'),w=500,h=215,p={l:40,r:12,t:12,b:34},iw=w-p.l-p.r,ih=h-p.t-p.b;let s='';for(let i=0;i<=4;i++){const y=p.t+ih*i/4,x=p.l+iw*i/4;s+=`<line class="gridline" x1="${p.l}" y1="${y}" x2="${p.l+iw}" y2="${y}"/><line class="gridline" x1="${x}" y1="${p.t}" x2="${x}" y2="${p.t+ih}"/><text class="axis" x="${p.l-5}" y="${y+3}" text-anchor="end">${100-25*i}</text>`}
    const sample=filtered.length>340?filtered.filter((_,i)=>i%Math.ceil(filtered.length/340)===0):filtered;const maxLog=Math.log10(Math.max(...filtered.map(r=>r.form_completion_seconds),100)+1);sample.forEach(r=>{const x=p.l+iw*Math.log10(Number(r.form_completion_seconds)+1)/maxLog,y=p.t+ih-ih*Number(r.isolation_anomaly_percentile)/100,fill=highRisk(r)?color('--red'):suspicious(r)?color('--amber'):color('--teal');s+=`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${highRisk(r)?3.3:2.3}" fill="${fill}" opacity=".78"><title>${r.application_id} · ${r.form_completion_seconds}s · anomaly ${r.isolation_anomaly_percentile}% · risk ${r.risk_score}</title></circle>`});s+=`<text class="axis" x="${p.l+iw/2}" y="${h-7}" text-anchor="middle">Form completion speed (log seconds) →</text><text class="axis" x="12" y="${p.t+ih/2}" transform="rotate(-90 12 ${p.t+ih/2})" text-anchor="middle">Isolation anomaly percentile</text>`;host.innerHTML=svgWrap(s,w,h)
  }
  function renderHeatmap(){
    const deps=uniq(filtered.map(r=>r.department)).sort(),rows=['Email','Phone','IP Address'];const matrix=rows.map(()=>Array(deps.length).fill(0));filtered.forEach(r=>{const j=deps.indexOf(r.department);if(r.duplicate_email_count>1)matrix[0][j]++;if(r.duplicate_phone_count>1)matrix[1][j]++;if(r.ip_reuse_count>1)matrix[2][j]++});const max=Math.max(1,...matrix.flat()),host=$('heatmapChart'),w=500,h=215,p={l:70,r:25,t:16,b:60},iw=w-p.l-p.r,ih=h-p.t-p.b,cw=iw/Math.max(1,deps.length),ch=ih/3;let s='';
    const stops=[[22,215,176],[255,179,77],[255,93,103]];const cellColor=v=>{const t=v/max;if(t<.5){const q=t*2,a=stops[0],b=stops[1];return `rgb(${Math.round(a[0]+(b[0]-a[0])*q)},${Math.round(a[1]+(b[1]-a[1])*q)},${Math.round(a[2]+(b[2]-a[2])*q)})`}const q=(t-.5)*2,a=stops[1],b=stops[2];return `rgb(${Math.round(a[0]+(b[0]-a[0])*q)},${Math.round(a[1]+(b[1]-a[1])*q)},${Math.round(a[2]+(b[2]-a[2])*q)})`};
    rows.forEach((r,i)=>{s+=`<text class="axis" x="${p.l-8}" y="${p.t+i*ch+ch/2+3}" text-anchor="end">${r}</text>`;deps.forEach((d,j)=>{const v=matrix[i][j],x=p.l+j*cw,y=p.t+i*ch;s+=`<rect x="${x+1}" y="${y+1}" width="${Math.max(2,cw-2)}" height="${Math.max(2,ch-2)}" rx="2" fill="${cellColor(v)}" opacity="${.25+.75*(v/max)}"><title>${d} · ${r}: ${v} repeated-pattern records</title></rect>`})});deps.forEach((d,j)=>{const x=p.l+j*cw+cw/2;s+=`<text class="axis" x="${x}" y="${h-15}" text-anchor="end" transform="rotate(-32 ${x} ${h-15})">${esc(d.replace(' Development',' Dev'))}</text>`});host.innerHTML=svgWrap(s,w,h)
  }
  function renderIsoHistogram(){
    const host=$('isoHistogram');if(!host)return;const bins=Array.from({length:10},(_,i)=>({lo:i*10,hi:(i+1)*10,n:0}));filtered.forEach(r=>bins[Math.min(9,Math.floor(Number(r.isolation_anomaly_percentile)/10))].n++);const w=530,h=240,p={l:38,r:10,t:15,b:34},iw=w-p.l-p.r,ih=h-p.t-p.b,max=Math.max(...bins.map(b=>b.n),1),bw=iw/bins.length*.72;let s='';bins.forEach((b,i)=>{const x=p.l+i*iw/bins.length+8,hh=ih*b.n/max,y=p.t+ih-hh;s+=`<rect x="${x}" y="${y}" width="${bw}" height="${hh}" rx="2" fill="${i>=8?color('--red'):i>=6?color('--amber'):color('--teal')}"><title>${b.lo}-${b.hi}: ${b.n} applications</title></rect><text class="axis" x="${x+bw/2}" y="${h-12}" text-anchor="middle">${b.lo}</text>`});host.innerHTML=svgWrap(s,w,h)
  }
  function renderClusters(){
    const host=$('clusterChart');if(!host)return;const m={};filtered.forEach(r=>{m[r.kmeans_cluster]??={n:0,r:[],p:r.cluster_profile};m[r.kmeans_cluster].n++;m[r.kmeans_cluster].r.push(r.risk_score)});const data=Object.entries(m).map(([k,v])=>({k:Number(k),n:v.n,avg:mean(v.r),p:v.p})).sort((a,b)=>a.k-b.k),w=530,h=240,p={l:45,r:16,t:16,b:48},iw=w-p.l-p.r,ih=h-p.t-p.b,max=100,group=iw/Math.max(1,data.length);let s='';[0,25,50,75,100].forEach(v=>{const y=p.t+ih-ih*v/100;s+=`<line class="gridline" x1="${p.l}" y1="${y}" x2="${p.l+iw}" y2="${y}"/><text class="axis" x="${p.l-6}" y="${y+3}" text-anchor="end">${v}</text>`});data.forEach((d,i)=>{const x=p.l+i*group+group*.2,bw=group*.6,hh=ih*d.avg/max;s+=`<rect x="${x}" y="${p.t+ih-hh}" width="${bw}" height="${hh}" rx="5" fill="${[color('--teal'),color('--cyan'),color('--purple'),color('--amber')][i%4]}"><title>Cluster ${d.k}: ${d.p} · ${d.n} applications · average risk ${d.avg.toFixed(1)}</title></rect><text class="axis" x="${x+bw/2}" y="${h-28}" text-anchor="middle">Cluster ${d.k}</text><text class="axis" x="${x+bw/2}" y="${h-14}" text-anchor="middle">${esc(d.p.replace(' pattern',''))}</text>`});host.innerHTML=svgWrap(s,w,h)
  }

  function signalPills(r){const s=[];if(r.duplicate_signal)s.push('Duplicate');if(r.rapid_submission_signal)s.push('Rapid');if(r.inconsistent_data_signal)s.push('Inconsistent');if(r.isolation_flag)s.push('Isolation');return (s.length?s:['No signal']).map(x=>`<span class="signal-pill">${x}</span>`).join(' ')}
  function renderRecent(){
    const rows=[...filtered].filter(suspicious).sort((a,b)=>b.risk_score-a.risk_score||b._date-a._date).slice(0,7);$('recentTable').innerHTML=`<table><thead><tr><th>#</th><th>Applicant</th><th>Department</th><th>City</th><th>Submitted</th><th>Alert Type</th><th>Risk</th><th>Action</th></tr></thead><tbody>${rows.map((r,i)=>`<tr><td>${i+1}</td><td><b>${esc(r.applicant_name)}</b><br><span style="color:var(--muted)">${esc(r.email)}</span></td><td>${esc(r.department)}</td><td>${esc(r.city)}</td><td>${esc(r.submitted_at)}</td><td><span class="risk-pill ${slug(r.alert_level)}">${esc(primarySignal(r))}</span></td><td><b>${r.risk_score}</b></td><td><button class="view-btn" data-view-id="${esc(r.application_id)}">View</button></td></tr>`).join('')||'<tr><td colspan="8">No suspicious applications in this view.</td></tr>'}</tbody></table>`
  }
  function renderInsights(){
    const n=filtered.length, sus=filtered.filter(suspicious), dup=filtered.filter(r=>r.duplicate_signal).length, rapid=filtered.filter(r=>r.rapid_submission_signal).length, top=[...filtered].sort((a,b)=>b.risk_score-a.risk_score)[0];
    const city={};filtered.forEach(r=>{city[r.city]??={n:0,s:0};city[r.city].n++;if(suspicious(r))city[r.city].s++});const tc=Object.entries(city).map(([k,v])=>({k,rate:v.s/v.n,s:v.s})).sort((a,b)=>b.rate-a.rate)[0];
    const items=[
      [`Highest-risk application: ${top.application_id}`,`${top.alert_reason}. Risk score ${top.risk_score}; review identity and submission evidence before a decision.`],
      [`${pct(dup,n).toFixed(1)}% show duplicate signals`,`${dup} applications reuse an email, phone or CV fingerprint. Add identity deduplication checks at submission.`],
      [`${rapid} rapid-submission records detected`,`Use rate limiting, minimum completion checks and device/IP review for short-gap or burst activity.`],
      [`Risk concentration is highest in ${tc.k}`,`${tc.s} suspicious applications in this city (${pct(tc.s,city[tc.k].n).toFixed(1)}% of its current records). Investigate patterns without assuming location itself causes fraud.`]
    ];$('insightsList').innerHTML=items.map((x,i)=>`<div class="insight-item"><div class="insight-no">${i+1}</div><div><b>${esc(x[0])}</b><p>${esc(x[1])}</p></div></div>`).join('')
  }

  function sortedRows(){const f=$('sortField').value,arr=[...filtered];arr.sort((a,b)=>{let av=a[f],bv=b[f];if(f==='submitted_at'){av=a._date;bv=b._date}if(typeof av==='string')return sortDir==='asc'?av.localeCompare(bv):bv.localeCompare(av);return sortDir==='asc'?Number(av)-Number(bv):Number(bv)-Number(av)});return arr}
  function renderApplications(){
    const arr=sortedRows(),pages=Math.max(1,Math.ceil(arr.length/PAGE_SIZE));if(page>pages)page=pages;const start=(page-1)*PAGE_SIZE,view=arr.slice(start,start+PAGE_SIZE);$('recordsTable').innerHTML=`<table><thead><tr><th>Application</th><th>Submitted</th><th>Applicant</th><th>Department</th><th>City</th><th>Completion</th><th>Signals</th><th>Cluster</th><th>Isolation</th><th>Risk</th><th>Alert</th><th>Action</th></tr></thead><tbody>${view.map(r=>`<tr><td><b>${esc(r.application_id)}</b></td><td>${esc(r.submitted_at)}</td><td>${esc(r.applicant_name)}<br><span style="color:var(--muted)">${esc(r.email)}</span></td><td>${esc(r.department)}</td><td>${esc(r.city)}</td><td>${r.form_completion_seconds}s</td><td>${signalPills(r)}</td><td><span class="cluster-pill">C${r.kmeans_cluster}</span></td><td>${r.isolation_anomaly_percentile}%</td><td><b>${r.risk_score}</b></td><td><span class="risk-pill ${slug(r.alert_level)}">${r.alert_level}</span></td><td><button class="view-btn" data-view-id="${esc(r.application_id)}">Review</button></td></tr>`).join('')}</tbody></table>`;$('pageStatus').textContent=`Page ${page} of ${pages} · ${fmt(arr.length)} records`;$('prevPage').disabled=page<=1;$('nextPage').disabled=page>=pages
  }
  function renderAlerts(){
    const rows=filtered.filter(suspicious).sort((a,b)=>b.risk_score-a.risk_score),levels=['Critical','High','Review'];$('alertStats').innerHTML=[['All Alerts',rows.length],...levels.map(l=>[l,rows.filter(r=>r.alert_level===l).length])].map(x=>`<div class="mini-stat"><strong>${fmt(x[1])}</strong><span>${x[0]}</span></div>`).join('');$('alertsTable').innerHTML=`<table><thead><tr><th>Application</th><th>Applicant</th><th>Alert Level</th><th>Risk</th><th>Suspicious Signals</th><th>K-Means Profile</th><th>Isolation</th><th>Reason</th><th>Action</th></tr></thead><tbody>${rows.slice(0,100).map(r=>`<tr><td><b>${esc(r.application_id)}</b></td><td>${esc(r.applicant_name)}<br><span style="color:var(--muted)">${esc(r.email)}</span></td><td><span class="risk-pill ${slug(r.alert_level)}">${r.alert_level}</span></td><td><b>${r.risk_score}</b></td><td>${signalPills(r)}</td><td><span class="cluster-pill">C${r.kmeans_cluster} · ${esc(r.cluster_profile)}</span></td><td>${r.isolation_anomaly_percentile}%</td><td>${esc(r.alert_reason)}</td><td><button class="view-btn" data-view-id="${esc(r.application_id)}">View</button></td></tr>`).join('')||'<tr><td colspan="9">No suspicious alerts found.</td></tr>'}</tbody></table>`
  }
  function renderModels(){
    const m=payload.model_metrics||{},iso=filtered.filter(r=>r.isolation_flag).length,clusters=uniq(filtered.map(r=>r.kmeans_cluster)).length;const metrics=[['350','Isolation Forest Trees'],[fmt(iso),'Isolation Flags'],[clusters,'K-Means Clusters'],[`${((m.precision_high_or_critical_vs_synthetic_reference||0)*100).toFixed(1)}%`,'Synthetic Precision']];$('modelMetrics').innerHTML=metrics.map(x=>`<div class="model-metric"><strong>${x[0]}</strong><span>${x[1]}</span></div>`).join('');renderIsoHistogram();renderClusters()
  }
  function renderReports(){
    const n=filtered.length,s=filtered.filter(suspicious).length,high=filtered.filter(highRisk).length,dup=filtered.filter(r=>r.duplicate_signal).length,rapid=filtered.filter(r=>r.rapid_submission_signal).length,inc=filtered.filter(r=>r.inconsistent_data_signal).length;const cards=[['Application Scope',fmt(n),`${fmt(s)} suspicious applications (${pct(s,n).toFixed(1)}%).`],['High-Priority Queue',fmt(high),'Applications classified High or Critical by combined risk logic.'],['Duplicate Behavior',fmt(dup),`${pct(dup,n).toFixed(1)}% of current applications show an identity/CV reuse signal.`],['Rapid / Inconsistent',`${rapid} / ${inc}`,'Rapid submission and inconsistent-data records for targeted review.']];$('reportCards').innerHTML=cards.map(x=>`<article class="report-card"><span>${x[0]}</span><strong>${x[1]}</strong><p>${x[2]}</p></article>`).join('')
  }

  function openRecord(id){const r=all.find(x=>x.application_id===id);if(!r)return;$('modalBody').innerHTML=`<span class="eyebrow">APPLICATION REVIEW</span><h2>${esc(r.application_id)}</h2><p>${esc(r.alert_reason)}. Machine-learning and behavior signals prioritize this application for human review; they are not proof of fraud.</p><div class="detail-grid"><div><span>Applicant</span><b>${esc(r.applicant_name)}</b></div><div><span>Alert Level</span><b>${esc(r.alert_level)} · Risk ${r.risk_score}</b></div><div><span>Email</span><b>${esc(r.email)}</b></div><div><span>Phone</span><b>${esc(r.phone)}</b></div><div><span>Department</span><b>${esc(r.department)}</b></div><div><span>City</span><b>${esc(r.city)}</b></div><div><span>Form Completion</span><b>${r.form_completion_seconds} seconds</b></div><div><span>Isolation Forest</span><b>${r.isolation_flag?'Flagged anomaly':'Model normal'} · ${r.isolation_anomaly_percentile}% percentile</b></div><div><span>K-Means</span><b>Cluster ${r.kmeans_cluster} · ${esc(r.cluster_profile)}</b></div><div><span>Signals</span><b>${esc(primarySignal(r))}</b></div><div><span>Device 24h Activity</span><b>${r.device_applications_24h} applications</b></div><div><span>IP 24h Activity</span><b>${r.ip_applications_24h} applications</b></div></div>`;$('modal').hidden=false}
  function closeModal(){if($('modal'))$('modal').hidden=true}

  function csvString(rows){if(!rows.length)return'';const cols=Object.keys(rows[0]).filter(k=>k!=='_date');const q=v=>`"${String(v??'').replace(/"/g,'""')}"`;return [cols.map(q).join(','),...rows.map(r=>cols.map(c=>q(r[c])).join(','))].join('\r\n')}
  function downloadCSV(){if(!filtered.length){showToast('No records to download');return}const blob=new Blob([csvString(filtered)],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='task4_filtered_applications.csv';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),600);showToast(`Downloaded ${filtered.length} filtered rows`)}

  window.dashboardAPI={allCount:()=>all.length,filteredCount:()=>filtered.length,applyFilters:(cfg)=>{filtered=filterRecords(all,{from:cfg.from||'',to:cfg.to||'',department:cfg.department||'',city:cfg.city||'',alert:cfg.alert||'',model:cfg.model||'combined',search:(cfg.search||'').toLowerCase()});renderAll();return filtered.length},reset:()=>{filtered=[...all];renderAll();return filtered.length},csv:()=>csvString(filtered),kpis:()=>({total:filtered.length,suspicious:filtered.filter(suspicious).length,duplicates:filtered.filter(r=>r.duplicate_signal).length,rapid:filtered.filter(r=>r.rapid_submission_signal).length,inconsistent:filtered.filter(r=>r.inconsistent_data_signal).length,isolation:filtered.filter(r=>r.isolation_flag).length})};
  setup();
})();
