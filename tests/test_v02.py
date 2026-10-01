import asyncio
import json
import sqlite3
from pathlib import Path
import pytest
from adoptlab.store import Store
from adoptlab.engine import execute,decode
from adoptlab.packages import validate_profile,validate_task,container_args,verify_rules,safe_path

IMAGE='sha256:'+'a'*64
def profile():return {'id':'filesystem-v1','image':IMAGE,'version':'test-pin','argv':['/input','/output'],'tools':['read_text_file','write_file']}
def task():return json.loads((Path(__file__).parents[1]/'examples/filesystem-task.json').read_text())

def test_migration_preserves_legacy(tmp_path):
    s=Store(tmp_path);e=s.experiment('preserved')
    with s.connect() as c:c.execute('PRAGMA user_version=0')
    s=Store(tmp_path)
    assert s.get_experiment(e)['title']=='preserved'
    assert (tmp_path/'adoptlab.pre-v02.db').exists()
    with s.connect() as c:assert c.execute('PRAGMA user_version').fetchone()[0]==2

def test_registry_immutable_and_paths(tmp_path):
    s=Store(tmp_path);s.register('profile',profile());s.register('task',task())
    t=task();t['instruction']='changed'
    with pytest.raises(ValueError):s.register('task',t)
    with pytest.raises(ValueError):validate_profile({**profile(),'image':'latest'})
    for name in ['../private','/absolute','C:/private','a\\b']:
        with pytest.raises(ValueError):safe_path(tmp_path,name)
    args=container_args(profile(),tmp_path,'adoptlab-test')
    assert '--network=none' in args and '--read-only' in args and '--cap-drop=ALL' in args
    assert '/input,readonly' in ' '.join(args) and 'private' not in ' '.join(args)

def test_rules_reject_wrong_answer(tmp_path):
    p=tmp_path/'outputs';p.mkdir();file=p/'evidence.json'
    file.write_text('{"retry_limit":2,"endpoint":"/v1/records","citation":"guide.txt"}')
    assert verify_rules(task(),tmp_path)['passed']
    file.write_text('{"retry_limit":9}')
    assert not verify_rules(task(),tmp_path)['passed']

def test_external_gate_no_paid_calls(tmp_path,monkeypatch):
    import adoptlab.engine as engine
    monkeypatch.setattr(engine,'readiness',lambda:{'ready':False,'reason':'DOCKER_NOT_INSTALLED'})
    s=Store(tmp_path);s.register('profile',profile());s.register('task',task())
    m=s.add_material('Read input; save output.',{'read_text_file':'read','write_file':'write'})
    r=asyncio.run(execute(s,s.queue(s.experiment('external'),'docs-evidence-01',m['id'],'model')))
    assert r['result']['error_code']=='DOCKER_NOT_INSTALLED' and r['result']['requests']==0

def test_revision_needs_changed_material_success_and_conditions(tmp_path):
    s=Store(tmp_path);e=s.experiment('revision');old=s.queue(e,'task-01','A');new=s.queue(e,'task-01','B')
    asyncio.run(execute(s,old));asyncio.run(execute(s,new));f=s.feedback(e,old,'clarify the guide')
    assert s.revision(f,new,'Explain tool inputs')
    result=s.get_run(new)['result'];s.finish(new,'cancelled',result)
    with pytest.raises(ValueError):s.revision(f,new,'cancelled')
    s.finish(new,'succeeded',result);result['provenance']['backend_hash']='different';s.finish(new,'succeeded',result)
    with pytest.raises(ValueError):s.revision(f,new,'different')
    assert not s.comparison(e)['comparable']

def test_experiment_limits_and_fingerprints(tmp_path):
    s=Store(tmp_path);e=s.experiment('limit',{'max_total_cost_cny':.001,'max_requests':1})
    r=asyncio.run(execute(s,s.queue(e,'task-01','B')))
    p=r['result']['provenance'];assert p['backend_hash']!=p['verifier_hash']
    assert p['tool_schema_hash'] and p['dependencies']['mcp']
    with pytest.raises(ValueError):s.reserve(r['id'],.002)

def test_trusted_extension_explicit_reverify(tmp_path):
    from adoptlab.packages import verify_task
    s=Store(tmp_path);script=tmp_path/'extension.py';script.write_text('import json\nprint(json.dumps({"passed":True}))\n')
    s.register_verifier('schema-v1',script);t=task();t['verifier']='schema-v1'
    outputs=tmp_path/'outputs';outputs.mkdir();(outputs/'evidence.json').write_text('{"retry_limit":2,"endpoint":"/v1/records","citation":"guide.txt"}')
    with pytest.raises(ValueError):verify_task(s,t,tmp_path)
    assert verify_task(s,t,tmp_path,True)['passed']
    (tmp_path/'verifiers'/'schema-v1.py').write_text('print("changed")')
    with pytest.raises(ValueError):verify_task(s,t,tmp_path,True)

def test_saved_request_limit_drives_execution(tmp_path,monkeypatch):
    import adoptlab.engine as engine
    monkeypatch.setenv('DEEPSEEK_API_KEY','unit-test')
    class Response:
        status_code=200
        def json(self):return {'model':'test-double','usage':{'prompt_tokens':20,'completion_tokens':5},'choices':[{'message':{'role':'assistant','content':None,'tool_calls':[{'id':'x','type':'function','function':{'name':'list_fixture_files','arguments':'{}'}}]}}]}
    class Client:
        def __init__(self,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,*args,**kwargs):return Response()
    monkeypatch.setattr(engine.httpx,'AsyncClient',Client)
    s=Store(tmp_path);e=s.experiment('one request',{'max_requests':1});r=asyncio.run(execute(s,s.queue(e,'task-01','B','model')))
    assert r['result']['requests']==1 and r['result']['error_code']=='request_limit'
    assert r['status']=='budget_exhausted'
