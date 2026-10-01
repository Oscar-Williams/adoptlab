import json
import sqlite3
import uuid
from datetime import datetime, timezone
from .config import RUNTIME, digest
from .tasks import catalog, MATERIALS

def now(): return datetime.now(timezone.utc).isoformat()
def uid(): return uuid.uuid4().hex

class Store:
    def __init__(self, root=RUNTIME):
        self.root=root; root.mkdir(parents=True,exist_ok=True)
        self.db=root/'adoptlab.db'
        if self.db.exists():
            with self.connect() as source:
                schema=source.execute('PRAGMA user_version').fetchone()[0]
                if schema>2:raise ValueError('DATABASE_VERSION_TOO_NEW')
                if schema < 2:
                    with sqlite3.connect(root/'adoptlab.pre-v02.db') as backup:source.backup(backup)
        with self.connect() as c:
            c.executescript('''
            BEGIN IMMEDIATE;
            CREATE TABLE IF NOT EXISTS experiments(id TEXT PRIMARY KEY, title TEXT NOT NULL, created TEXT, config TEXT);
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, experiment_id TEXT REFERENCES experiments(id), task_id TEXT, material TEXT, mode TEXT, cohort TEXT, subject TEXT, trial INTEGER, status TEXT, cancelled INTEGER DEFAULT 0, created TEXT, result TEXT);
            CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, name TEXT, created TEXT, cohort TEXT, subject TEXT, run_id TEXT, experiment_id TEXT, source TEXT, campaign TEXT);
            CREATE TABLE IF NOT EXISTS feedback(id TEXT PRIMARY KEY, experiment_id TEXT REFERENCES experiments(id), run_id TEXT REFERENCES runs(id), text TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS revisions(id TEXT PRIMARY KEY, feedback_id TEXT REFERENCES feedback(id), old_run TEXT REFERENCES runs(id), new_run TEXT REFERENCES runs(id), decision TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS charges(id TEXT PRIMARY KEY, run_id TEXT, reserved REAL, actual REAL, status TEXT, usage TEXT);
            CREATE TABLE IF NOT EXISTS materials(id TEXT PRIMARY KEY, content TEXT, hash TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS registry(kind TEXT, id TEXT, content TEXT, hash TEXT, PRIMARY KEY(kind,id));
            CREATE TABLE IF NOT EXISTS material_metadata(id TEXT PRIMARY KEY REFERENCES materials(id), name TEXT, parent TEXT, reason TEXT);
            CREATE TABLE IF NOT EXISTS owners(run_id TEXT PRIMARY KEY REFERENCES runs(id), pid INTEGER, created TEXT);
            PRAGMA user_version=2;
            COMMIT;
            ''')
            for key,value in MATERIALS.items():c.execute('INSERT OR IGNORE INTO materials VALUES(?,?,?,?)',(key,json.dumps(value),digest(value),now()))
    def material(self,id):
        with self.connect() as c:r=c.execute('SELECT * FROM materials WHERE id=?',(id,)).fetchone()
        if not r:raise ValueError('MATERIAL_NOT_FOUND')
        with self.connect() as c:meta=c.execute('SELECT name,parent,reason FROM material_metadata WHERE id=?',(id,)).fetchone()
        return {'id':r['id'],'content':json.loads(r['content']),'hash':r['hash'],'created':r['created'],'metadata':dict(meta) if meta else {'name':id,'parent':None,'reason':None}}
    def materials(self):
        with self.connect() as c:ids=[r[0] for r in c.execute('SELECT id FROM materials ORDER BY created')]
        return [self.material(id) for id in ids]
    def add_material(self,guide,descriptions,name='',parent=None,reason=''):
        import re
        content={'guide':guide,'descriptions':descriptions}
        toolsets=[set(MATERIALS['A']['descriptions'])]+[set(p['tools']) for p in self.registered('profile')]
        if set(descriptions) not in toolsets or not guide or len(guide)>6000 or any(not isinstance(v,str) or not v or len(v)>1500 for v in descriptions.values()):raise ValueError('INVALID_MATERIAL')
        if parent and set(self.material(parent)['content']['descriptions'])!=set(descriptions):raise ValueError('MATERIAL_TOOL_MISMATCH')
        if len(name)>100 or len(reason)>1000:raise ValueError('INVALID_METADATA')
        if re.search(r'sk-[A-Za-z0-9_-]{12,}|(?:api[_ -]?key|password)\s*[:=]\s*\S+',json.dumps([content,name,reason]),re.I):raise ValueError('SENSITIVE_MATERIAL_DENIED')
        id='material-'+uid()
        with self.connect() as c:
            c.execute('INSERT INTO materials VALUES(?,?,?,?)',(id,json.dumps(content),digest(content),now()))
            c.execute('INSERT INTO material_metadata VALUES(?,?,?,?)',(id,name or id,parent,reason))
        return self.material(id)
    def register(self,kind,data):
        from .packages import validate_task,validate_profile
        if kind not in {'task','profile'}:raise ValueError('REGISTRY_KIND_DENIED')
        (validate_task if kind=='task' else validate_profile)(data)
        if kind=='task':
            if data['id'] in catalog():raise ValueError('BUILTIN_TASK_IMMUTABLE')
            self.registered('profile',data['profile'])
            if data.get('verifier'):self.verifier(data['verifier'])
        with self.connect() as c:
            old=c.execute('SELECT hash FROM registry WHERE kind=? AND id=?',(kind,data['id'])).fetchone()
            if old and old['hash']!=digest(data):raise ValueError('REGISTER_NEW_VERSION_ID')
            c.execute('INSERT OR IGNORE INTO registry VALUES(?,?,?,?)',(kind,data['id'],json.dumps(data),digest(data)))
        return {'id':data['id'],'hash':digest(data)}
    def registered(self,kind,id=None):
        with self.connect() as c:rows=c.execute('SELECT content FROM registry WHERE kind=?'+(' AND id=?' if id else ''),(kind,id) if id else (kind,)).fetchall()
        if id and not rows:raise ValueError('REGISTRY_ITEM_NOT_FOUND')
        values=[json.loads(r['content']) for r in rows]
        return values[0] if id else values
    def register_verifier(self,id,path):
        from .packages import ID
        if not ID.fullmatch(id) or path.suffix!='.py':raise ValueError('INVALID_VERIFIER')
        text=path.read_text(encoding='utf-8');hash=digest(text)
        folder=self.root/'verifiers';folder.mkdir(exist_ok=True);target=folder/(id+'.py')
        if target.exists() and digest(target.read_text(encoding='utf-8'))!=hash:raise ValueError('REGISTER_NEW_VERSION_ID')
        target.write_text(text,encoding='utf-8')
        with self.connect() as c:c.execute('INSERT OR IGNORE INTO registry VALUES(?,?,?,?)',('verifier',id,json.dumps({'id':id,'hash':hash}),hash))
        return {'id':id,'hash':hash,'trust':'Operator-trusted local code; subprocess timeout is not an OS security sandbox.'}
    def verifier(self,id):return self.registered('verifier',id)
    def tasks(self):return {**catalog(),**{t['id']:t for t in self.registered('task')}}
    def task(self,id):
        if id not in self.tasks():raise ValueError('TASK_NOT_FOUND')
        return self.tasks()[id]
    def connect(self):
        c=sqlite3.connect(self.db,timeout=20);c.row_factory=sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON');return c
    def experiment(self,title,settings=None):
        id=uid();config={"contract":"records-normalize-v1","materials":{k:digest(v) for k,v in MATERIALS.items()},"task_hash":digest(catalog()),"max_total_cost_cny":200,"max_requests":8,"max_output_tokens":1024,"input_bound":16000,"episode_seconds":180,"model":"deepseek-flash","price_source":"https://api-docs.deepseek.com/zh-cn/quick_start/pricing/","price_checked":"2026-09-30","input_cny_per_million":2,"output_cny_per_million":8}
        config['max_episode_output_tokens']=8192
        config['task_hash']=digest(self.tasks())
        if settings:
            allowed={'max_total_cost_cny','max_requests','max_output_tokens','max_episode_output_tokens','input_bound','episode_seconds'}
            if set(settings)-allowed:raise ValueError('UNKNOWN_EXECUTION_SETTING')
            for k,v in settings.items():
                if not isinstance(v,(int,float)) or isinstance(v,bool) or not 0<v<=config[k]:raise ValueError('INVALID_EXECUTION_LIMIT')
                if k not in {'max_total_cost_cny','episode_seconds'} and not isinstance(v,int):raise ValueError('INTEGER_EXECUTION_LIMIT_REQUIRED')
            config.update(settings)
        with self.connect() as c:c.execute('INSERT INTO experiments VALUES(?,?,?,?)',(id,title,now(),json.dumps(config)))
        return id
    def get_experiment(self,id):
        with self.connect() as c:r=c.execute('SELECT * FROM experiments WHERE id=?',(id,)).fetchone()
        if not r:raise KeyError('EXPERIMENT_NOT_FOUND')
        d=dict(r);d['config']=json.loads(d['config']);return d
    def queue(self,exp,task,material,mode='protocol',cohort='automation',subject='automation',trial=1):
        self.get_experiment(exp)
        self.material(material)
        if task not in self.tasks() or mode not in {'protocol','model'} or cohort not in {'automation','human_observed','human_unverified'}:raise ValueError('INVALID_RUN')
        t=self.task(task)
        expected=set(self.registered('profile',t['profile'])['tools']) if 'profile' in t else set(MATERIALS['A']['descriptions'])
        if set(self.material(material)['content']['descriptions'])!=expected:raise ValueError('MATERIAL_TOOL_MISMATCH')
        id=uid()
        with self.connect() as c:c.execute('INSERT INTO runs(id,experiment_id,task_id,material,mode,cohort,subject,trial,status,created) VALUES(?,?,?,?,?,?,?,?,?,?)',(id,exp,task,material,mode,cohort,subject,trial,'queued',now()))
        return id
    def get_run(self,id):
        with self.connect() as c:r=c.execute('SELECT * FROM runs WHERE id=?',(id,)).fetchone()
        if not r:raise KeyError('RUN_NOT_FOUND')
        d=dict(r);d['result']=json.loads(d['result']) if d['result'] else None;return d
    def claim(self,id):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            if c.execute("SELECT 1 FROM runs WHERE status='running'").fetchone():return False
            ok=c.execute("UPDATE runs SET status='running' WHERE id=? AND status='queued' AND cancelled=0",(id,)).rowcount==1
            if ok:
                import os
                c.execute('INSERT OR REPLACE INTO owners VALUES(?,?,?)',(id,os.getpid(),now()))
            return ok
    def cancel(self,id):
        self.get_run(id)
        with self.connect() as c:
            c.execute("UPDATE runs SET cancelled=1, status=CASE WHEN status='queued' THEN 'cancelled' ELSE status END WHERE id=?",(id,))
    def finish(self,id,status,result):
        with self.connect() as c:c.execute('UPDATE runs SET status=?,result=? WHERE id=?',(status,json.dumps(result),id))
    def runs(self,exp=None):
        with self.connect() as c:
            rows=c.execute('SELECT id FROM runs'+(' WHERE experiment_id=?' if exp else '')+' ORDER BY created',(exp,) if exp else ()).fetchall()
        return [self.get_run(r['id']) for r in rows]
    def experiments(self):
        with self.connect() as c:return [dict(r) for r in c.execute('SELECT id,title,created FROM experiments ORDER BY created DESC')]
    def reserve(self,run,amount):
        id=uid()
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            total=c.execute('SELECT COALESCE(SUM(COALESCE(actual,reserved)),0) FROM charges').fetchone()[0]
            runrow=c.execute('SELECT experiment_id FROM runs WHERE id=?',(run,)).fetchone()
            config=self.get_experiment(runrow[0])['config']
            subtotal=c.execute('SELECT COALESCE(SUM(COALESCE(actual,reserved)),0) FROM charges WHERE run_id IN (SELECT id FROM runs WHERE experiment_id=?)',(runrow[0],)).fetchone()[0]
            if total+amount>200 or subtotal+amount>config['max_total_cost_cny']:raise ValueError('BUDGET_EXHAUSTED')
            c.execute('INSERT INTO charges VALUES(?,?,?,?,?,?)',(id,run,amount,None,'reserved',None))
        return id
    def settle(self,id,actual,usage):
        with self.connect() as c:c.execute("UPDATE charges SET actual=?,status='observed',usage=? WHERE id=?",(actual,json.dumps(usage),id))
    def cost(self):
        with self.connect() as c:
            r=c.execute('SELECT COALESCE(SUM(COALESCE(actual,reserved)),0),COALESCE(SUM(actual),0),SUM(CASE WHEN actual IS NULL THEN 1 ELSE 0 END) FROM charges').fetchone()
        return {"upper_bound_cny":r[0],"usage_priced_upper_cny":r[1],"unresolved_requests":r[2] or 0,"limit_cny":200}
    def event(self,id,name,cohort,subject,run_id=None,experiment_id=None,source='unknown',campaign='none',internal=False):
        allowed={'entry_viewed','setup_started','feedback_submitted'}
        if internal:allowed|={'integration_checked','task_started','task_verified','task_failed','revision_verified'}
        if name not in allowed:raise ValueError('EVENT_DENIED')
        if run_id:
            run=self.get_run(run_id); experiment_id=run['experiment_id']
            if run['cohort']=='withdrawn':return False
            if internal:cohort,subject=run['cohort'],run['subject']
            if not internal and run['subject']!=subject:raise ValueError('SUBJECT_MISMATCH')
        if experiment_id:self.get_experiment(experiment_id)
        with self.connect() as c:
            return c.execute('INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?,?,?,?)',(id,name,now(),cohort,subject,run_id,experiment_id,source,campaign)).rowcount==1
    def feedback(self,exp,run,text):
        import re
        if re.search(r'sk-[A-Za-z0-9_-]{12,}|(?:api[_ -]?key|token|password)\s*[:=]\s*\S+',text,re.I):raise ValueError('SENSITIVE_FEEDBACK_DENIED')
        r=self.get_run(run)
        if r['experiment_id']!=exp:raise ValueError('RUN_MISMATCH')
        id=uid()
        with self.connect() as c:c.execute('INSERT INTO feedback VALUES(?,?,?,?,?)',(id,exp,run,text,now()))
        return id
    def revision(self,feedback,newrun,decision):
        import re
        if re.search(r'sk-[A-Za-z0-9_-]{12,}|(?:api[_ -]?key|token|password)\s*[:=]\s*\S+',decision,re.I):raise ValueError('SENSITIVE_DECISION_DENIED')
        with self.connect() as c:f=c.execute('SELECT * FROM feedback WHERE id=?',(feedback,)).fetchone()
        if not f:raise KeyError('FEEDBACK_NOT_FOUND')
        new=self.get_run(newrun);old=self.get_run(f['run_id'])
        if new['experiment_id']!=f['experiment_id'] or new['task_id']!=old['task_id'] or new['status']!='succeeded' or not new['result'] or not new['result']['verification']['passed']:raise ValueError('REVISION_NOT_VERIFIED')
        if self.material(new['material'])['hash']==self.material(old['material'])['hash']:raise ValueError('MATERIAL_UNCHANGED')
        if self.condition(old)!=self.condition(new):raise ValueError('EXECUTION_CONDITIONS_DIFFER')
        a=old['result'].get('provenance',{}).get('model');b=new['result'].get('provenance',{}).get('model')
        if a and b and a!=b:raise ValueError('RESPONDER_MODEL_CHANGED')
        id=uid()
        with self.connect() as c:c.execute('INSERT INTO revisions VALUES(?,?,?,?,?,?)',(id,feedback,f['run_id'],newrun,decision,now()))
        self.event(uid(),'revision_verified',new['cohort'],new['subject'],newrun,internal=True)
        return id
    def withdraw(self,subject):
        with self.connect() as c:
            c.execute('DELETE FROM revisions WHERE feedback_id IN (SELECT id FROM feedback WHERE run_id IN (SELECT id FROM runs WHERE subject=?))',(subject,))
            c.execute('DELETE FROM feedback WHERE run_id IN (SELECT id FROM runs WHERE subject=?)',(subject,))
            c.execute('DELETE FROM events WHERE subject=?',(subject,))
            c.execute("UPDATE runs SET subject='withdrawn',cohort='withdrawn' WHERE subject=?",(subject,))
    def funnel(self):
        with self.connect() as c:
            # A two-hour window defines the first local session, not a project schedule.
            rows=c.execute('''WITH grouped AS (
              SELECT cohort,subject,
              MIN(CASE WHEN name='entry_viewed' THEN created END) AS entered,
              MIN(CASE WHEN name='setup_started' THEN created END) AS setup,
              MIN(CASE WHEN name='task_started' THEN created END) AS started,
              MIN(CASE WHEN name='task_verified' THEN created END) AS verified
              FROM events GROUP BY cohort,subject)
              SELECT cohort,COUNT(*) AS subjects,
              SUM(entered IS NOT NULL) AS entered,
              SUM(setup>=entered AND julianday(setup)-julianday(entered)<=2.0/24) AS setup_after_entry,
              SUM(started>=entered AND julianday(started)-julianday(entered)<=2.0/24) AS started_after_entry,
              SUM(verified>=started AND started>=entered AND julianday(verified)-julianday(entered)<=2.0/24) AS verified_after_start,
              SUM(entered IS NULL OR (verified IS NOT NULL AND (started IS NULL OR verified<started))) AS unlinked_or_invalid_order
              FROM grouped GROUP BY cohort''').fetchall()
            channels=c.execute("SELECT cohort,source,campaign,COUNT(DISTINCT subject) AS entering_instances FROM events WHERE name='entry_viewed' GROUP BY cohort,source,campaign").fetchall()
        return {'cohorts':[dict(r) for r in rows],'channels':[dict(r) for r in channels],
                'interpretation':'Ordered local-instance sessions, two-hour first-session window. Unknown sources, missing links and invalid order stay visible. Automation, unverified browser instances and observed humans are separate. No verified unique-person or causal growth claim.'}
    def comparison(self,exp):
        rows=self.runs(exp);cohorts={}
        variants=list(dict.fromkeys(['A','B']+[r['material'] for r in rows]))
        for cohort in ['automation','human_unverified','human_observed','withdrawn']:
            out={}
            for v in variants:
                groups={}
                for mode in ['protocol','model']:
                    runs=[r for r in rows if r['material']==v and r['mode']==mode and r['cohort']==cohort]
                    done=[r for r in runs if r['result']]
                    accepted=lambda r:r['status']=='succeeded' and r['result']['verification']['passed']
                    groups[mode]={"total":len(runs),"completed":len(done),"passed":sum(accepted(r) for r in done),
                        "cost_upper_cny":sum(r['result'].get('cost_upper_cny',0) for r in done),
                        "normal_total":sum(not self.task(r['task_id']).get('expected_error') for r in runs),
                        "normal_passed":sum(accepted(r) and not self.task(r['task_id']).get('expected_error') for r in done),
                        "rejection_total":sum(bool(self.task(r['task_id']).get('expected_error')) for r in runs),
                        "rejection_passed":sum(accepted(r) and bool(self.task(r['task_id']).get('expected_error')) for r in done),
                        "statuses":{status:sum(r['status']==status for r in runs) for status in sorted({r['status'] for r in runs})}}
                out[v]=groups
            cohorts[cohort]=out
        conditions={mode:sorted({self.condition(r) for r in rows if r['result'] and r['mode']==mode}) for mode in ['protocol','model']}
        models=sorted({r['result'].get('provenance',{}).get('model') for r in rows if r['result'] and r['result'].get('provenance',{}).get('model')})
        unknown=[r['id'] for r in rows if r['mode']=='model' and r['result'] and not r['result'].get('provenance',{}).get('model')]
        compatible=all(len(v)<=1 for v in conditions.values()) and len(models)<=1
        return {"experiment_id":exp,"groups":cohorts['automation'] if compatible else {},"cohorts":cohorts if compatible else {},"comparable":compatible,"condition_groups":conditions,"observed_models":models,"unknown_responder_runs":unknown,"incompatible_runs":[r['id'] for r in rows if r['result']] if not compatible else [],"budget":self.cost(),
            "interpretation":"Groups retain automated experiment results. Cohorts separate local browser instances, observed sessions and withdrawn records. Protocol checks measure service correctness; model trials are exploratory. Local instances do not count unique people."}
    def export(self,exp):
        e=self.get_experiment(exp)
        keys=['id','task_id','material','mode','cohort','trial','status','created']
        rows=[]
        for r in self.runs(exp):
            d={k:r[k] for k in keys}
            if r['result']:d['result']={k:r['result'][k] for k in ['verification','requests','tools','elapsed_seconds','cost_upper_cny','error_code','provenance'] if k in r['result']}
            rows.append(d)
        return {"schema":"adoptlab-report-v1","experiment_id":exp,"config":e['config'],"runs":rows,"comparison":self.comparison(exp)}
    @staticmethod
    def condition(run):
        p=(run.get('result') or {}).get('provenance',{})
        # Task IDs vary within a frozen matrix; the catalogue fingerprint covers them together.
        return digest({'mode':run['mode'],**{k:p.get(k) for k in ['backend_hash','verifier_hash','executor_hash','dependencies','model_config_hash','tool_schema_hash','catalog_hash','profile_hash']}})
    def handoff(self,exp):
        self.get_experiment(exp)
        with self.connect() as c:
            return {'feedback':[dict(r) for r in c.execute('SELECT * FROM feedback WHERE experiment_id=? ORDER BY created',(exp,))],
                    'revisions':[dict(r) for r in c.execute('SELECT * FROM revisions WHERE old_run IN (SELECT id FROM runs WHERE experiment_id=?)',(exp,))]}
    def material_diff(self,id):
        import difflib
        new=self.material(id);parent=new['metadata']['parent']
        old=self.material(parent)['content'] if parent else {}
        return {'id':id,'parent':parent,'diff':list(difflib.unified_diff(json.dumps(old,indent=2,ensure_ascii=False).splitlines(),json.dumps(new['content'],indent=2,ensure_ascii=False).splitlines(),fromfile=parent or 'empty',tofile=id))}
    def reconcile(self,id):
        import os
        run=self.get_run(id)
        with self.connect() as c:owner=c.execute('SELECT pid FROM owners WHERE run_id=?',(id,)).fetchone()
        if run['status']!='running' or not owner:raise ValueError('OPERATOR_REVIEW_REQUIRED')
        alive=True
        if os.name=='nt':
            import ctypes
            kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            kernel.OpenProcess.restype=ctypes.c_void_p
            kernel.CloseHandle.argtypes=[ctypes.c_void_p]
            handle=kernel.OpenProcess(0x1000,False,owner['pid'])
            if handle:kernel.CloseHandle(handle)
            elif ctypes.get_last_error()==87:alive=False
        else:
            try:os.kill(owner['pid'],0)
            except ProcessLookupError:alive=False
        if not alive:
            self.finish(id,'interrupted',{'verification':{'passed':False,'reason':'process_interrupted'},'error_code':'process_interrupted','cost_upper_cny':0})
            return {'id':id,'status':'interrupted','notice':'Unresolved charges remain reserved; create a new run explicitly.'}
        raise ValueError('OWNER_PROCESS_STILL_ALIVE')
