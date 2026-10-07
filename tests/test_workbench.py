import asyncio
import json
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from adoptlab.store import Store
from adoptlab.engine import execute
from adoptlab.workbench import preflight

def test_preflight_readonly_and_field_errors(tmp_path):
    s=Store(tmp_path)
    p={'id':'filesystem-v1','image':'sha256:'+'a'*64,'version':'pin','argv':['/input','/output'],'tools':['read_text_file','write_file']}
    s.register('profile',p)
    t=json.loads((Path(__file__).parents[1]/'examples/filesystem-task.json').read_text())
    assert preflight(t,s)['valid']
    assert t['id'] not in s.tasks()
    t['rules'][0]['path']='wrong'
    t['fixtures']['../escape']='bad'
    errors=preflight(t,s)['errors']
    assert any(e['location']==['rules',0,'path'] for e in errors)
    assert any(e['code']=='UNSAFE_PATH' for e in errors)
    assert not (tmp_path/'runs').exists()

def test_migration_backup_retains_legacy_and_new_entities(tmp_path):
    s=Store(tmp_path);exp=s.experiment('historical')
    with s.connect() as c:
        c.execute('DROP TABLE observations');c.execute('DROP TABLE release_checks');c.execute('PRAGMA user_version=2')
    s=Store(tmp_path)
    assert s.get_experiment(exp)['title']=='historical'
    with sqlite3.connect(tmp_path/'adoptlab.pre-v04.db') as c:assert c.execute('PRAGMA user_version').fetchone()[0]==2
    with s.connect() as c:assert c.execute('SELECT count(*) FROM observations').fetchone()[0]==0
    saved=(tmp_path/'adoptlab.pre-v04.db').read_bytes()
    with s.connect() as c:c.execute('PRAGMA user_version=2')
    Store(tmp_path)
    assert (tmp_path/'adoptlab.pre-v04.db').read_bytes()==saved
    assert len(list(tmp_path.glob('adoptlab.pre-v04.*.db')))==1

def test_preflight_malformed_shapes_and_finite_bounds(tmp_path):
    import copy
    s=Store(tmp_path)
    s.register('profile',{'id':'filesystem-v1','image':'sha256:'+'a'*64,'version':'pin','argv':['/input','/output'],'tools':['read_text_file','write_file']})
    original=json.loads((Path(__file__).parents[1]/'examples/filesystem-task.json').read_text())
    for field in ['split','profile','rules','steps','fixtures']:
        for value in [None,[],{},42]:
            t=copy.deepcopy(original);t[field]=value
            result=preflight(t,s)
            assert isinstance(result['valid'],bool)
    for value in [float('nan'),float('inf'),True,'3']:
        t=copy.deepcopy(original);t['rules']=[{'file':'x.json','op':'range','min':value}]
        assert any(e['code']=='INVALID_RANGE' for e in preflight(t,s)['errors'])
    t=copy.deepcopy(original);t['steps'][0]['tool']='delete_file'
    assert any(e['code']=='TOOL_DENIED' for e in preflight(t,s)['errors'])

def test_gate_observation_and_tamper(tmp_path,monkeypatch):
    import adoptlab.web as web
    s=Store(tmp_path);monkeypatch.setattr(web,'store',s)
    exp=s.experiment('gate');run=s.queue(exp,'task-01','B')
    asyncio.run(execute(s,run))
    with TestClient(web.app) as c:
        body={'experiment_id':exp,'material':'B','tasks':['task-01'],'mode':'protocol'}
        gate=c.post('/api/releases',json=body).json()
        assert gate['verdict']=='passed',gate
        missing=c.post('/api/releases',json={**body,'tasks':['task-02']}).json()
        assert missing['verdict']=='insufficient'
        obs={'participant':'anon-01','run_id':run,'started':'2026-10-07T00:00:00+00:00','ended':'2026-10-07T00:01:00+00:00','assistance':'hint','consent':True,'evidence_ref':'session-01','source':'automation'}
        first=c.post('/api/observations',json=obs).json()
        assert first['elapsed_seconds']==60
        assert c.post('/api/observations',json=obs).json()['id']==first['id']
        assert c.get('/api/workbench/summary').json()['observations']['attested_sessions']==0
        assert c.post('/api/observations',json={**obs,'consent':False}).status_code==400
        export=c.get('/api/releases/'+gate['id']+'/export').text
        assert 'participant' not in export and 'session-01' not in export
        files=list((tmp_path/'runs'/run/'outputs').glob('*'))
        assert files
        files[0].write_text('{}',encoding='utf-8')
        assert c.post('/api/releases',json=body).json()['verdict']=='failed'
        assert c.request('DELETE','/api/observations/'+first['id'],json={}).status_code==200


def test_doctor_requires_image_for_a_profile_with_a_task(tmp_path,monkeypatch):
    from adoptlab.config import doctor
    import adoptlab.packages as packages
    s=Store(tmp_path)
    for name in ['filesystem-missing','filesystem-ready']:
        s.register('profile',{'id':name,'image':'sha256:'+'a'*64,'version':'pin','argv':['/input','/output'],'tools':['read_text_file','write_file']})
    task=json.loads((Path(__file__).parents[1]/'examples/filesystem-task.json').read_text())
    task['profile']='filesystem-missing';s.register('task',task)
    monkeypatch.setattr(packages,'readiness',lambda:{'ready':True})
    monkeypatch.setattr(packages,'pinned_image_ready',lambda p:p['id']=='filesystem-ready')
    result=doctor('filesystem',tmp_path)
    assert next(c for c in result['checks'] if c['id']=='filesystem_registration')['passed']
    assert not next(c for c in result['checks'] if c['id']=='pinned_image')['passed']
    assert not result['ready']
