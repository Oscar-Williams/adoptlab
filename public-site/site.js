let lang='en',data=null;
const $=id=>document.getElementById(id);
function render(){
 document.documentElement.lang=lang;$('language').textContent=lang==='en'?'中文':'English';
 document.querySelectorAll('[data-en]').forEach(e=>e.textContent=e.dataset[lang]);
 if(!data)return;
 const rows=data.cases.filter(r=>($('family').value==='all'||r.family===$('family').value)&&($('material').value==='all'||r.material===$('material').value));
 const passed=rows.filter(r=>r.passed).length;
 $('summary').textContent=lang==='zh'?`选中 ${rows.length} 次执行，通过 ${passed} 次。正常输出与正确拒绝按任务判据记录。`:`${passed}/${rows.length} selected episodes passed. Valid output and correct rejection follow task-specific criteria.`;
 $('cases').replaceChildren();for(const r of rows){const row=document.createElement('tr');row.dataset.passed=String(r.passed);for(const value of [r.task_id,`${r.material} / ${r.trial}`,r.passed?(lang==='zh'?'通过':'passed'):(lang==='zh'?'失败':'failed'),r.kind+': '+r.reason,r.cost_upper_cny.toFixed(6)]){const cell=document.createElement('td');cell.textContent=value;row.append(cell)}$('cases').append(row)}
 $('guides').replaceChildren();for(const [id,m] of Object.entries(data.materials)){const details=document.createElement('details'),summary=document.createElement('summary'),p=document.createElement('p');summary.textContent=id+' · '+(lang==='zh'?'指南与工具描述':'Guide and tool descriptions');p.textContent=m.guide;details.append(summary,p);for(const [name,description] of Object.entries(m.descriptions)){const line=document.createElement('p');line.textContent=name+' — '+description;details.append(line)}$('guides').append(details)}
}
$('language').onclick=()=>{lang=lang==='en'?'zh':'en';render()};$('family').onchange=render;$('material').onchange=render;
fetch('report.json').then(r=>{if(!r.ok)throw Error('Report unavailable');return r.json()}).then(x=>{data=x;for(const family of [...new Set(data.cases.map(r=>r.family))])$('family').add(new Option(family,family));render()}).catch(()=>{$('summary').textContent='Report unavailable. Reload or open the downloadable report.'});
