let lang='en',data=null,demoStep=0,loadSequence=0;
const $=id=>document.getElementById(id),mode=r=>r.mode||'model',cohort=r=>r.cohort||'automation';
function comparable(a,b){return a.task_id===b.task_id&&a.trial===b.trial&&a.material!==b.material&&mode(a)===mode(b)&&cohort(a)===cohort(b)&&Boolean(a.condition)&&a.condition===b.condition&&(mode(a)==='protocol'||Boolean(a.responder)&&a.responder===b.responder)}
function pairs(){return data.cases.filter(r=>!r.passed&&mode(r)==='model').map(before=>({before,after:data.cases.find(r=>r.passed&&comparable(before,r))})).filter(p=>p.after)}
function render(){
 document.documentElement.lang=lang;$('language').textContent=lang==='en'?'中文':'English';
 document.querySelectorAll('[data-en]').forEach(e=>e.textContent=e.dataset[lang]);if(!data)return;
 $('report-limits').textContent=lang==='zh'?'保存的合成任务结果；协议测试与模型实验分别统计。相关重复、有限任务族及请求失败限制解释范围。真实用户参与人数为零。':data.limitations;
 const rows=data.cases.filter(r=>['family','material','mode','cohort','split'].every(k=>$(k).value==='all'||(k==='mode'?mode(r):k==='cohort'?cohort(r):r[k]||'unspecified')===$(k).value));
 $('summary').textContent=(lang==='zh'?'分别统计，通过/执行次数：':'Separate acceptance totals, passed/episodes: ')+['protocol','model'].map(m=>{const rs=rows.filter(r=>mode(r)===m);return m+': '+rs.filter(r=>r.passed).length+'/'+rs.length}).join(' · ');
 $('cases').replaceChildren();for(const r of rows){const row=document.createElement('tr');row.dataset.passed=String(r.passed);for(const value of [r.task_id,r.material+' / '+r.trial+' / '+mode(r)+' / '+cohort(r)+' / '+(r.split||'unspecified'),r.passed?(lang==='zh'?'通过':'passed'):(lang==='zh'?'失败':'failed'),r.kind+': '+r.reason+(mode(r)==='model'&&!r.responder&&data.schema.endsWith('v2')?' (unknown responder)':''),r.cost_upper_cny.toFixed(6)]){const cell=document.createElement('td');cell.textContent=value;row.append(cell)}$('cases').append(row)}
 $('guides').replaceChildren();for(const [id,m] of Object.entries(data.materials)){const details=document.createElement('details'),summary=document.createElement('summary'),p=document.createElement('p');summary.textContent=id+' · '+(lang==='zh'?'指南与工具描述':'Guide and tool descriptions');p.textContent=m.guide;details.append(summary,p);for(const [name,description] of Object.entries(m.descriptions)){const line=document.createElement('p');line.textContent=name+' — '+description;details.append(line)}$('guides').append(details)}renderDemo();
}
async function loadReport(){
 const sequence=++loadSequence;data=null;$('summary').textContent=lang==='zh'?'正在加载证据…':'Loading evidence…';$('cases').replaceChildren();$('guides').replaceChildren();$('demo-evidence').textContent='';$('demo-next').disabled=true;
 try{const response=await fetch($('version').value);if(!response.ok)throw Error('Report unavailable');const report=await response.json();if(sequence!==loadSequence)return;data=report;demoStep=0;
 for(const k of ['family','material','mode','cohort','split'])$(k).replaceChildren(new Option('All / 全部','all'),...[...new Set(data.cases.map(r=>k==='mode'?mode(r):k==='cohort'?cohort(r):r[k]||'unspecified'))].sort().map(v=>new Option(v,v)));
 $('mode').value='model';$('demo-case').replaceChildren();render();
 }catch{if(sequence!==loadSequence)return;$('summary').textContent=lang==='zh'?'证据暂不可用，请重试或下载报告。':'Evidence unavailable. Retry or download the report.';$('demo-evidence').textContent=lang==='zh'?'演示等待证据加载。':'Walkthrough awaits evidence.'}
}
function renderDemo(){
 const available=pairs(),chosen=$('demo-case').value;
 $('demo-case').replaceChildren(...available.map((p,i)=>new Option(p.before.task_id+' / '+p.before.material+' → '+p.after.material+' / '+p.before.trial,String(i))));
 if(chosen&&Number(chosen)<available.length)$('demo-case').value=chosen;
 const pair=available[Number($('demo-case').value)||0],labels=lang==='zh'?['选择可比案例','查看失败证据','比较材料差异','查看保存的对照结果']:['Choose comparable case','Inspect failure evidence','Compare material differences','Inspect saved comparison'];
 $('demo-steps').replaceChildren(...labels.map((text,i)=>{const li=document.createElement('li');li.textContent=(i===demoStep?'→ ':'')+text;if(i===demoStep)li.setAttribute('aria-current','step');return li}));
 if(!pair){$('demo-evidence').textContent=lang==='zh'?'该报告没有具备完整条件指纹的可比失败案例。可在下方查看历史结果。':'This report has no failed pair with complete condition fingerprints. Inspect historical results below.';$('demo-next').disabled=true;return}
 const {before,after}=pair,old=data.materials[before.material],changed=data.materials[after.material],diff={guide_changed:old.guide!==changed.guide,changed_tools:Object.keys(old.descriptions).filter(k=>old.descriptions[k]!==changed.descriptions[k])};
 const evidence=[{task_id:before.task_id,trial:before.trial,source:data.schema,date:data.recorded_date,mode:mode(before),cohort:cohort(before)},before,{original:old,comparison:changed,difference:diff},{before,after,conditions_matched:true,interpretation:lang==='zh'?'固定矩阵中的材料对照。实际反馈修订闭环在本地工作台验证，保存的矩阵对照不计为真实用户反馈。':'Material comparison within a frozen matrix. Feedback-linked revision is verified in the local workspace; this saved comparison contributes no human-feedback record.'}];
 $('demo-evidence').textContent=JSON.stringify(evidence[demoStep],null,2);$('demo-next').disabled=demoStep===3;$('demo-next').textContent=lang==='zh'?'下一步：'+(labels[demoStep+1]||'完成'):'Next: '+(labels[demoStep+1]||'complete');
}
$('language').onclick=()=>{lang=lang==='en'?'zh':'en';render()};
for(const k of ['family','material','mode','cohort','split'])$(k).onchange=render;
$('version').onchange=loadReport;$('retry-report').onclick=loadReport;
$('demo-next').onclick=()=>{demoStep=Math.min(3,demoStep+1);renderDemo()};$('demo-reset').onclick=()=>{demoStep=0;if(data)renderDemo()};$('demo-case').onchange=()=>{demoStep=0;renderDemo()};loadReport();
