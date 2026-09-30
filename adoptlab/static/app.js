const $=id=>document.getElementById(id),zh=document.body.dataset.lang==='zh';
let subject=localStorage.getItem('adoptlab-subject');if(!subject){subject=crypto.randomUUID();localStorage.setItem('adoptlab-subject',subject)}
let currentRun=null,feedbackID=null,timer=null;
async function api(path,data){const r=await fetch(path,data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const j=await r.json();if(!r.ok)throw Error(j.error||JSON.stringify(j));return j}
function message(e){$('message').textContent=e.message||e}
function show(x){$('result').textContent=JSON.stringify(x,null,2)}
function guard(fn){return async e=>{if(e)e.preventDefault();$('message').textContent='';try{await fn()}catch(x){message(x)}}}
function exp(){if(!$('experiment').value)throw Error(zh?'请先创建或选择实验':'Create or select an experiment first');return $('experiment').value}
async function poll(){const r=await api('/api/runs/'+currentRun);show(r);$('status').textContent=r.status;const terminal=!['queued','running'].includes(r.status);$('cancel').disabled=terminal;$('run').disabled=!terminal;if(!terminal)timer=setTimeout(()=>poll().catch(message),700);else{const b=await api('/api/budget');$('budget').textContent=(zh?'费用上界 ¥':'Cost upper bound ¥')+b.upper_bound_cny.toFixed(4)}}
$('create').onsubmit=guard(async()=>{const e=await api('/api/experiments',{title:$('title').value});const option=new Option($('title').value,e.id);$('experiment').add(option);$('experiment').value=e.id});
$('run').onclick=guard(async()=>{const r=await api('/api/experiments/'+exp()+'/runs',{task_id:$('task').value,material:$('material').value,mode:$('mode').value,subject});currentRun=r.id;clearTimeout(timer);await poll()});
$('cancel').onclick=guard(async()=>{await api('/api/runs/'+currentRun+'/cancel',{});await poll()});
$('compare').onclick=guard(async()=>show(await api('/api/experiments/'+exp()+'/comparison')));
$('export').onclick=e=>{try{$('export').href='/api/experiments/'+exp()+'/export'}catch(x){e.preventDefault();message(x)}};
$('verify').onclick=guard(async()=>{if(!currentRun)throw Error(zh?'先运行任务':'Run a task first');show(await api('/api/runs/'+currentRun+'/verification'))});
$('send-feedback').onclick=guard(async()=>{if(!currentRun)throw Error(zh?'先运行任务':'Run a task first');const r=await api('/api/feedback',{experiment_id:exp(),run_id:currentRun,text:$('feedback').value});feedbackID=r.id;show(r)});
$('revision').onclick=guard(async()=>{if(!feedbackID)throw Error(zh?'先保存反馈':'Save feedback first');show(await api('/api/revisions',{feedback_id:feedbackID,new_run:$('new-run').value,decision:$('decision').value}))});
$('withdraw').onclick=guard(async()=>{show(await api('/api/withdraw',{subject}));localStorage.removeItem('adoptlab-subject')});
async function loadMaterials(){const chosen=$('material').value;const values=await api('/api/materials');$('material').replaceChildren(...values.map(m=>new Option(m.id==='A'||m.id==='B'?m.id:m.id.slice(0,17)+' · '+m.hash.slice(0,8),m.id)));if(values.some(m=>m.id===chosen))$('material').value=chosen}
if($('save-material'))$('save-material').onclick=guard(async()=>{const material=await api('/api/materials',{guide:$('material-guide').value,descriptions:JSON.parse($('material-descriptions').value)});await loadMaterials();$('material').value=material.id;show({material_id:material.id,hash:material.hash});message(zh?'新版本已保存，可选择任务复查。':'New version saved. Run the same task to verify it.')});
loadMaterials().catch(message);
const params=new URLSearchParams(location.search);const clean=v=>(v||'unknown').replace(/[^a-zA-Z0-9_-]/g,'').slice(0,40)||'unknown';
api('/api/events',{event_id:crypto.randomUUID(),name:'entry_viewed',subject,source:clean(params.get('source')),campaign:clean(params.get('campaign'))}).catch(message);
