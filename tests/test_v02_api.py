import json
from fastapi.testclient import TestClient
from adoptlab.store import Store
import time

def wait_run(s,id):
    deadline=time.monotonic()+20
    while s.get_run(id)['status'] in {'queued','running'} and time.monotonic()<deadline:time.sleep(.05)
    return s.get_run(id)

def test_history_handoff_clone_batch_and_import(tmp_path,monkeypatch):
    import adoptlab.web as web
    s=Store(tmp_path);monkeypatch.setattr(web,'store',s)
    with TestClient(web.app) as c:
        e=c.post('/api/experiments',json={'title':'API v02','settings':{'max_requests':2}}).json()['id']
        old=c.post('/api/experiments/'+e+'/runs',json={'task_id':'task-01','material':'A'}).json()['id']
        wait_run(s,old)
        assert c.get('/api/runs',params={'experiment_id':e,'status':'succeeded'}).json()[0]['id']==old
        assert c.get('/api/runs/'+old+'/problem-package').json()['schema']=='adoptlab-problem-v2'
        f=c.post('/api/feedback',json={'experiment_id':e,'run_id':old,'text':'Explicit paths help'}).json()['id']
        assert c.get('/api/experiments/'+e+'/handoff').json()['feedback'][0]['id']==f
        from adoptlab.tasks import MATERIALS
        m=c.post('/api/materials',json={'guide':'Check output. '+MATERIALS['B']['guide'],'descriptions':MATERIALS['B']['descriptions'],'name':'Clear guide','parent':'B','reason':'Explain output'}).json()['id']
        assert c.get('/api/materials/'+m+'/diff').json()['parent']=='B'
        r=c.post('/api/experiments/'+e+'/batch',json={'tasks':['task-01'],'materials':[m],'trials':1})
        assert r.status_code==202 and wait_run(s,r.json()['run_ids'][0])['status']=='succeeded'
        assert c.post('/api/experiments/'+e+'/batch',json={'tasks':['missing'],'materials':['A']}).status_code==400
        assert c.post('/api/tasks/import',json={'id':'bad','profile':'unregistered'}).status_code==400
        assert c.post('/api/experiments',json={'title':'bad','settings':{'max_requests':999}}).status_code==400
        assert c.post('/api/events',json={'event_id':'invalid','name':'entry_viewed','subject':'x'},headers={'content-length':'invalid'}).status_code==400
        assert c.get('/favicon.ico').status_code==204

def test_withdraw_blocks_late_internal_event(tmp_path):
    s=Store(tmp_path);e=s.experiment('withdraw');id=s.queue(e,'task-01','A',subject='person')
    s.withdraw('person')
    assert not s.event('late','task_verified','human_observed','person',id,internal=True)
    assert s.funnel()['cohorts']==[]

def test_future_database_rejected(tmp_path):
    s=Store(tmp_path)
    with s.connect() as c:c.execute('PRAGMA user_version=99')
    import pytest
    with pytest.raises(ValueError):Store(tmp_path)
