import asyncio
import json
import os
import subprocess
import sys
from fastapi.testclient import TestClient
from adoptlab.config import doctor
from adoptlab.onboarding import first_task
from adoptlab.store import Store

def test_single_first_task_and_tamper(tmp_path,monkeypatch):
    for key in ['DEEPSEEK_API_KEY','LANGFUSE_SECRET_KEY','LANGFUSE_PUBLIC_KEY']:monkeypatch.delenv(key,raising=False)
    s=Store(tmp_path);out=asyncio.run(first_task(s))
    assert out['passed'] and out['requests']==0 and len(s.runs())==1
    assert s.runs()[0]['mode']=='protocol' and s.runs()[0]['cohort']=='automation'
    assert json.loads((tmp_path/(out['run_id']+'.first-task.json')).read_text())['passed']
    from adoptlab.engine import reverify
    (tmp_path/'runs'/out['run_id']/'outputs'/'summary.json').write_text('{}')
    assert not reverify(s,out['run_id'])['verification']['passed']

def test_target_readiness_and_privacy(tmp_path,monkeypatch):
    import adoptlab.config as config
    monkeypatch.setattr(config,'load_credentials',lambda:None)
    monkeypatch.delenv('DEEPSEEK_API_KEY',raising=False)
    assert doctor('builtin',tmp_path)['ready']
    model=doctor('model',tmp_path)
    assert not model['ready'] and any(c['id']=='model_key' and not c['passed'] for c in model['checks'])
    blocked=tmp_path/'file';blocked.write_text('occupied')
    assert not doctor('builtin',blocked)['ready']
    import adoptlab.web as web
    monkeypatch.setattr(web,'store',Store(tmp_path))
    with TestClient(web.app) as c:
        data=c.get('/api/doctor').json()
        assert 'runtime' not in data and str(tmp_path) not in json.dumps(data)
        assert c.get('/api/doctor?target=invalid').status_code==422
        assert 'first-task.js' in c.get('/?view=developer').text
        assert 'id="create"' not in c.get('/?view=developer').text
        exp=web.store.experiment('No artifacts');run=web.store.queue(exp,'task-01','B');web.store.cancel(run)
        response=c.post('/api/runs/'+run+'/verification',json={})
        assert response.status_code==400 and response.json()['error']=='ARTIFACTS_UNAVAILABLE'

def test_cli_exit_and_preserved_legacy_doctor(tmp_path):
    env={**os.environ,'ADOPTLAB_RUNTIME':str(tmp_path)}
    result=subprocess.run([sys.executable,'-m','adoptlab.cli','first-task'],env=env,text=True,capture_output=True,timeout=30)
    assert result.returncode==0
    out=json.loads(result.stdout);assert out['passed'] and out['requests']==0
    assert len(Store(tmp_path).runs())==1
    old=subprocess.run([sys.executable,'-m','adoptlab.cli','doctor'],env=env,text=True,capture_output=True,timeout=20)
    assert 'runtime' in json.loads(old.stdout)
    blocked=tmp_path/'occupied';blocked.write_text('file')
    fail=subprocess.run([sys.executable,'-m','adoptlab.cli','first-task'],env={**env,'ADOPTLAB_RUNTIME':str(blocked)},text=True,capture_output=True,timeout=10)
    assert fail.returncode==1 and json.loads(fail.stdout)['error']=='RUNTIME_UNWRITABLE'
    assert str(blocked) not in fail.stdout and not fail.stderr

def test_first_task_failure_is_non_success(tmp_path,monkeypatch):
    import adoptlab.onboarding as onboarding
    from adoptlab.engine import execute
    async def cancelled(store,id):
        store.cancel(id)
        return await execute(store,id)
    monkeypatch.setattr(onboarding,'execute',cancelled)
    out=asyncio.run(first_task(Store(tmp_path)))
    assert not out['passed'] and out['status']=='cancelled'

def test_reconcile_terminated_process_with_retained_handle(tmp_path):
    import pytest
    if os.name!='nt':pytest.skip('Windows process-handle lifetime')
    child=subprocess.Popen([sys.executable,'-c','pass'])
    child.wait(timeout=10)
    s=Store(tmp_path);e=s.experiment('Interrupted owner');id=s.queue(e,'task-01','B');s.claim(id)
    with s.connect() as c:c.execute('UPDATE owners SET pid=? WHERE run_id=?',(child.pid,id))
    assert s.reconcile(id)['status']=='interrupted'
