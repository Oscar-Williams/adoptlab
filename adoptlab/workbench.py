"""Evidence-first workbench APIs. No inference or tools run during preflight."""
import json
import math
import re
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from .config import digest
from .packages import validate_task, ID, safe_path
from .store import uid, now

router = APIRouter(prefix='/api')

def store():
    from . import web
    return web.store

def preflight(data, s):
    errors=[]
    def issue(field, code): errors.append({'location':field,'code':code})
    if not isinstance(data,dict): return {'valid':False,'errors':[{'location':['task'],'code':'OBJECT_REQUIRED'}]}
    for field in ['id','profile']:
        if not isinstance(data.get(field),str) or not ID.fullmatch(data[field]): issue([field],'INVALID_ID')
    for field in ['family','instruction']:
        if not isinstance(data.get(field),str) or not data[field].strip(): issue([field],'TEXT_REQUIRED')
    if data.get('split') not in ['exploration','holdout']:issue(['split'],'INVALID_SPLIT')
    if not isinstance(data.get('fixtures',{}),dict):issue(['fixtures'],'OBJECT_REQUIRED')
    else:
        from pathlib import Path
        for name,value in data.get('fixtures',{}).items():
            try:safe_path(Path('.'),name)
            except (ValueError,TypeError):issue(['fixtures',name],'UNSAFE_PATH')
            if not isinstance(value,str):issue(['fixtures',name],'TEXT_REQUIRED')
    rules=data.get('rules')
    if not isinstance(rules,list) or not rules:issue(['rules'],'RULES_REQUIRED')
    else:
        for i,r in enumerate(rules):
            if not isinstance(r,dict):issue(['rules',i],'OBJECT_REQUIRED');continue
            from pathlib import Path
            try:safe_path(Path('.'),r.get('file'))
            except (ValueError,TypeError):issue(['rules',i,'file'],'UNSAFE_PATH')
            if r.get('op') not in ['exists','equals','contains','set_equals','range','type']:issue(['rules',i,'op'],'UNKNOWN_RULE')
            if not isinstance(r.get('path',[]),list) or any(type(v) not in (int,str) or (isinstance(v,int) and v<0) for v in (r.get('path',[]) if isinstance(r.get('path',[]),list) else [])):issue(['rules',i,'path'],'INVALID_RULE_PATH')
            if r.get('op') in ['equals','contains','set_equals'] and 'expected' not in r:issue(['rules',i,'expected'],'EXPECTED_REQUIRED')
            if r.get('op')=='set_equals' and not isinstance(r.get('expected'),list):issue(['rules',i,'expected'],'ARRAY_REQUIRED')
            if r.get('op')=='type' and r.get('type') not in ['dict','list','str','int','float','bool','NoneType']:issue(['rules',i,'type'],'INVALID_TYPE')
            if r.get('op')=='range':
                bounds=[r[k] for k in ['min','max'] if k in r]
                if not bounds or any(type(v) not in (int,float) or not math.isfinite(v) for v in bounds):issue(['rules',i],'INVALID_RANGE')
                elif r.get('min',float('-inf'))>r.get('max',float('inf')):issue(['rules',i],'INVALID_RANGE')
    if not isinstance(data.get('steps',[]),list):issue(['steps'],'ARRAY_REQUIRED')
    profile=None
    try:profile=s.registered('profile',data.get('profile')) if isinstance(data.get('profile'),str) else None
    except ValueError:issue(['profile'],'PROFILE_NOT_REGISTERED')
    if isinstance(data.get('steps',[]),list):
        for i,step in enumerate(data.get('steps',[])):
            if not isinstance(step,dict) or set(step)!={'tool','arguments'} or not isinstance(step.get('arguments'),dict):issue(['steps',i],'INVALID_REFERENCE_STEP')
            elif profile and step['tool'] not in profile['tools']:issue(['steps',i,'tool'],'TOOL_DENIED')
    if data.get('verifier'):
        try:s.verifier(data['verifier'])
        except (ValueError,TypeError):issue(['verifier'],'VERIFIER_NOT_REGISTERED')
    if not errors:
        try:validate_task(data)
        except (ValueError,TypeError,KeyError,AttributeError) as e:issue(['task'],str(e) if isinstance(e,ValueError) else 'INVALID_TASK_PACKAGE')
    if not errors:
        existing=s.tasks().get(data['id'])
        if existing and digest(existing)!=digest(data):issue(['id'],'REGISTER_NEW_VERSION_ID')
    return {'valid':not errors,'errors':errors,'hash':digest(data) if not errors else None,'notice':'Validation only. No registration, tool execution or model request.'}

@router.post('/tasks/preflight')
async def check_task(data:dict):return preflight(data,store())

@router.get('/catalog')
async def catalog():
    s=store()
    return {'tasks':[{'id':t['id'],'family':t['family'],'split':t['split'],'profile':t.get('profile','builtin'),'hash':digest(t)} for t in s.tasks().values()], 'profiles':s.registered('profile'),'materials':s.materials()}

@router.get('/tasks/{id}/package')
async def task_package(id:str):return store().task(id)

@router.get('/runs/{id}/diagnosis')
async def diagnosis(id:str):
    s=store();r=s.get_run(id);result=r['result'] or {};code=result.get('error_code') or result.get('verification',{}).get('reason') or r['status']
    categories=[('environment',{'DOCKER_NOT_INSTALLED','LINUX_DOCKER_NOT_READY','DOCKER_CHECK_FAILED','PINNED_IMAGE_NOT_FOUND','FileNotFoundError'}),('parameters',{'INVALID_ARGUMENTS','INVALID_ROW','SCHEMA_ERROR'}),('tools',{'TOOL_DENIED','UNKNOWN_TOOL','MCP_TOOL_ERROR','TOOL_CONTRACT_MISMATCH'}),('budget',{'BUDGET_EXHAUSTED','request_limit','output_limit','budget_exhausted'}),('timeout',{'episode_timeout','timed_out'}),('interruption',{'cancelled','interrupted'})]
    category=next((name for name,codes in categories if code in codes),'acceptance' if result.get('verification') else 'pending')
    if r['status']=='succeeded' and result.get('verification',{}).get('passed'):
        category='verified'
    actions={'environment':['Check the matching environment target.','Register the pinned profile before execution.'],'parameters':['Inspect the failed tool and schema.','Revise the material with explicit parameter examples.'],'tools':['Compare the actual tool allowlist and material descriptions.','Inspect the failed call; rerun explicitly.'],'budget':['Inspect settled and unresolved reservations.','Reduce task count or request limits; do not replay unknown requests.'],'timeout':['Inspect the last completed tool.','Check dependencies and execution limits before an explicit rerun.'],'interruption':['Inspect retained state and artifacts.','Reconcile a dead owner through the CLI; never automatically replay.'],'acceptance':['Inspect each failed independent rule.','Link feedback, save a new material and rerun under the same conditions.'],'pending':['Wait for execution to finish or cancel explicitly.']}
    timeline=[{'index':i,**{k:v for k,v in step.items() if k in {'tool','arguments_hash','result_hash','error'}}} for i,step in enumerate(result.get('timeline',[]))]
    actions['verified']=['Inspect independent checks and retained fingerprints.','Export evidence or link feedback; protocol acceptance does not establish model effectiveness.']
    checks=result.get('verification',{}).get('checks',[])
    return {'run_id':id,'status':r['status'],'category':category,'code':code,'timeline':timeline,'checks':checks,'failed_checks':[c for c in checks if not c.get('passed')],'actions':actions[category], 'basis':'Recorded execution and independent acceptance; suggested actions are not proven root causes.'}

class Strict(BaseModel):model_config=ConfigDict(extra='forbid')
class ReleaseInput(Strict):
    experiment_id:str
    material:str
    tasks:list[str]=Field(min_length=1,max_length=16)
    mode:Literal['protocol','model']='protocol'

@router.post('/releases',status_code=201)
async def release(data:ReleaseInput):
    from .engine import reverify
    s=store();s.get_experiment(data.experiment_id);material=s.material(data.material)
    if len(set(data.tasks))!=len(data.tasks):raise ValueError('DUPLICATE_TASK')
    checks=[];selected=[]
    for tid in data.tasks:
        task=s.task(tid)
        runs=[r for r in s.runs(data.experiment_id) if r['task_id']==tid and r['material']==data.material and r['mode']==data.mode and r['cohort']!='withdrawn']
        if not runs:checks.append({'task_id':tid,'verdict':'insufficient','reason':'NO_RUN'});continue
        r=runs[-1];selected.append(r)
        if not r['result'] or r['status'] in {'queued','running'}:checks.append({'task_id':tid,'run_id':r['id'],'verdict':'insufficient','reason':'RUN_NOT_COMPLETED'});continue
        try:
            v=reverify(s,r['id'],False)
            intact=all(v.get(k) for k in ['manifest_matches_db','task_matches','artifact_hash_matches'])
            if task.get('verifier'):intact=False
            passed=r['status']=='succeeded' and v['verification']['passed'] and intact and r['result']['provenance']['material_hash']==material['hash']
            checks.append({'task_id':tid,'run_id':r['id'],'verdict':'passed' if passed else 'failed','reason':'VERIFIED' if passed else 'ACCEPTANCE_OR_INTEGRITY_FAILED'})
        except (ValueError,OSError,KeyError):checks.append({'task_id':tid,'run_id':r['id'],'verdict':'insufficient','reason':'ARTIFACTS_OR_EXPLICIT_EXTENSION_REQUIRED'})
    # Profiles may intentionally differ across task families; compare conditions within each profile.
    groups={}
    for r in selected:
        if r['result']:groups.setdefault(s.task(r['task_id']).get('profile','builtin'),set()).add(s.condition(r))
    responders={(r['result'] or {}).get('provenance',{}).get('model') for r in selected} if data.mode=='model' else set()
    compatible=all(len(v)==1 for v in groups.values()) and len(responders)<=1
    known=data.mode!='model' or all((r['result'] or {}).get('provenance',{}).get('model') for r in selected)
    verdict='failed' if any(c['verdict']=='failed' for c in checks) else 'insufficient' if not compatible or not known or any(c['verdict']=='insufficient' for c in checks) else 'passed'
    value={'id':uid(),'created':now(),'experiment_id':data.experiment_id,'material':data.material,'material_hash':material['hash'],'mode':data.mode,'checks':checks,'comparable':compatible,'known_responder':known,'verdict':verdict,'notice':'A recorded task-set check, not a production or adoption guarantee.'}
    with s.connect() as c:c.execute('INSERT INTO release_checks VALUES(?,?,?)',(value['id'],value['created'],json.dumps(value)))
    return value

@router.get('/releases')
async def releases():
    with store().connect() as c:return [json.loads(r['content']) for r in c.execute('SELECT content FROM release_checks ORDER BY created DESC')]

@router.get('/releases/{id}/export')
async def release_export(id:str):
    with store().connect() as c:r=c.execute('SELECT content FROM release_checks WHERE id=?',(id,)).fetchone()
    if not r:raise KeyError('NOT_FOUND')
    # The stored check is already a strict projection, without fixtures, observations or free text.
    return JSONResponse({'schema':'adoptlab-release-v1','release':json.loads(r['content'])},headers={'Content-Disposition':'attachment; filename=adoptlab-release.json'})

class ObservationInput(Strict):
    participant:str=Field(pattern=r'^[A-Za-z0-9_-]{1,64}$')
    run_id:str
    started:datetime
    ended:datetime
    assistance:Literal['none','hint','guided']
    consent:bool
    evidence_ref:str=Field(min_length=1,max_length=100,pattern=r'^[A-Za-z0-9_./-]+$')
    source:Literal['observed_session','self_report','automation']='self_report'

@router.post('/observations',status_code=201)
async def observation(data:ObservationInput):
    s=store();r=s.get_run(data.run_id)
    if not data.consent:raise ValueError('CONSENT_REQUIRED')
    if data.started.tzinfo is None or data.ended.tzinfo is None or data.ended<data.started:raise ValueError('INVALID_OBSERVATION_TIME')
    if r['status'] in {'queued','running'} or r['cohort']=='withdrawn':raise ValueError('RUN_NOT_OBSERVABLE')
    if '..' in data.evidence_ref or re.search(r'(?:secret|password|token|api.key)',data.evidence_ref,re.I):raise ValueError('INVALID_EVIDENCE_REF')
    value={**data.model_dump(mode='json'),'id':uid(),'created':now(),'accepted':bool(r['status']=='succeeded' and (r['result'] or {}).get('verification',{}).get('passed')),'elapsed_seconds':(data.ended-data.started).total_seconds(),'evidence_status':'observer_attested' if data.source=='observed_session' else 'unverified'}
    key=digest({k:value[k] for k in ['participant','run_id','started','ended','source']})
    with s.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        existing=c.execute('SELECT content FROM observations WHERE fingerprint=?',(key,)).fetchone()
        if existing:return json.loads(existing['content'])
        c.execute('INSERT INTO observations VALUES(?,?,?,?,?)',(value['id'],data.participant,value['created'],key,json.dumps(value)))
    return value

@router.get('/observations')
async def observations():
    with store().connect() as c:return [json.loads(r['content']) for r in c.execute('SELECT content FROM observations ORDER BY created DESC')]

@router.delete('/observations/{id}')
async def delete_observation(id:str):
    with store().connect() as c:
        if not c.execute('DELETE FROM observations WHERE id=?',(id,)).rowcount:raise KeyError('NOT_FOUND')
    return {'deleted':True}

@router.get('/workbench/summary')
async def summary():
    s=store();runs=s.runs();obs=await observations()
    cohorts={}
    for r in runs:
        key=r['mode']+':'+r['cohort'];row=cohorts.setdefault(key,{'total':0,'accepted':0})
        row['total']+=1;row['accepted']+=int(r['status']=='succeeded' and bool((r['result'] or {}).get('verification',{}).get('passed')))
    return {'tasks':len(s.tasks()),'materials':len(s.materials()),'experiments':len(s.experiments()),'cohorts':cohorts,'budget':s.cost(),'observations':{'sessions':len(obs),'attested_sessions':sum(o['source']=='observed_session' for o in obs),'interpretation':'Observer-entered sessions; external identity and adoption are not automatically verified.'}}
