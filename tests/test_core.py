import asyncio
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from adoptlab.contract import normalize, safe_path, ContractError, verify
from adoptlab.tasks import row,catalog
from adoptlab.store import Store
from adoptlab.engine import execute,reverify

def test_money_and_timezone():
    r=normalize([row(' b ',' ACTIVE ',' 10.01 ',' usd '),row('a',amount='9.99')],1000)
    assert r['result']==[{'id':'b','status':'active','amount_cents':1001,'currency':'USD','created_at':'2026-09-01T00:00:00Z'}]
    assert r['summary']=={'count':1,'totals_cents':{'USD':1001}}

@pytest.mark.parametrize('change,code',[({'amount':'NaN'},'INVALID_AMOUNT'),({'amount':'1.001'},'INVALID_AMOUNT'),({'currency':'EUR'},'INVALID_CURRENCY'),({'created_at':'2026-01-01'},'INVALID_DATE'),({'status':'unknown'},'INVALID_STATUS')])
def test_bad_rows_validated_before_filter(change,code):
    r=row(amount='0.00');r.update(change)
    with pytest.raises(ContractError,match=code):normalize([r],1000)

@pytest.mark.parametrize('path',['../private/.env','/tmp/x','C:/secret','sub\\x'])
def test_path_denied(tmp_path,path):
    with pytest.raises(ContractError,match='PATH_DENIED'):safe_path(tmp_path,path)

def test_symlink_denied(tmp_path):
    outside=tmp_path/'outside';outside.mkdir();root=tmp_path/'root';root.mkdir()
    try:(root/'link').symlink_to(outside,target_is_directory=True)
    except OSError:pytest.skip('symlink privilege unavailable')
    with pytest.raises(ContractError):safe_path(root,'link/x')

def test_windows_junction_denied(tmp_path):
    import sys,subprocess
    if sys.platform!='win32':pytest.skip('Windows junction case')
    root=tmp_path/'root';outside=tmp_path/'outside';root.mkdir();outside.mkdir()
    result=subprocess.run(['cmd','/c','mklink','/J',str(root/'link'),str(outside)],capture_output=True)
    if result.returncode:pytest.skip('junction creation unavailable')
    with pytest.raises(ContractError,match='PATH_DENIED'):safe_path(root,'link/x')

def test_mcp_trial_independent_oracle_and_tamper(tmp_path):
    s=Store(tmp_path);e=s.experiment('test');id=s.queue(e,'task-01','B')
    r=asyncio.run(execute(s,id));assert r['status']=='succeeded'
    assert r['result']['requests']==0 and r['result']['tools']==4
    assert reverify(s,id)['verification']['passed']
    (tmp_path/'runs'/id/'outputs'/'summary.json').write_text('{"count":0,"totals_cents":{}}')
    assert not reverify(s,id)['verification']['passed']
    assert not reverify(s,id)['artifact_hash_matches']
    # Completed run cannot be executed again.
    assert asyncio.run(execute(s,id))['result']==r['result']

def test_mcp_rejection(tmp_path):
    s=Store(tmp_path);e=s.experiment('test');id=s.queue(e,'task-11','A')
    r=asyncio.run(execute(s,id));assert r['status']=='succeeded'
    assert r['result']['verification']['kind']=='correct_rejection'

def test_cancel_queue_budget_and_event_dedup(tmp_path):
    s=Store(tmp_path);e=s.experiment('test');id=s.queue(e,'task-01','A')
    s.cancel(id);assert not s.claim(id);assert s.get_run(id)['status']=='cancelled'
    assert s.event('same','entry_viewed','human_unverified','anon')
    assert not s.event('same','entry_viewed','human_unverified','anon')
    with pytest.raises(ValueError):s.event('forge','task_verified','human_unverified','anon')
    charge=s.reserve(id,199.9)
    with pytest.raises(ValueError,match='BUDGET_EXHAUSTED'):s.reserve(id,.2)
    s.settle(charge,.1,{'prompt_tokens':1,'completion_tokens':1})
    assert s.cost()['upper_bound_cny']==.1

def test_api_boundaries(tmp_path,monkeypatch):
    import adoptlab.web as web
    monkeypatch.setattr(web,'store',Store(tmp_path))
    with TestClient(web.app) as client:
        assert client.get('/').status_code==200
        assert client.get('/?lang=zh&view=developer').status_code==200
        assert client.post('/api/experiments',json={'title':'x'},headers={'Origin':'https://evil.test'}).status_code==403
        assert client.get('/',headers={'Host':'evil.test'}).status_code==403
        assert client.post('/api/experiments',json={'title':'x','api_key':'fake'}).status_code==422
        assert client.post('/api/events',json={'event_id':'x','name':'task_verified','subject':'a'}).status_code==422
        e=client.post('/api/experiments',json={'title':'x'}).json()['id']
        assert client.post('/api/experiments/'+e+'/runs',json={'task_id':'../../secret','material':'A'}).status_code==400
        assert 'config' in client.get('/api/experiments/'+e+'/export').json()

def test_revision_and_export(tmp_path):
    s=Store(tmp_path);e=s.experiment('x')
    old=s.queue(e,'task-01','A');new=s.queue(e,'task-01','B')
    asyncio.run(execute(s,old));asyncio.run(execute(s,new))
    f=s.feedback(e,old,'Tool error was hard to understand')
    assert s.revision(f,new,'Add structured input guidance')
    report=json.dumps(s.export(e))
    assert 'subject' not in report and str(tmp_path) not in report and 'Tool error was hard' not in report

def test_custom_material_immutable_execution(tmp_path):
    from adoptlab.tasks import MATERIALS
    s=Store(tmp_path);e=s.experiment('materials')
    m=s.add_material('Use integer cents. '+MATERIALS['B']['guide'],MATERIALS['B']['descriptions'])
    assert s.material(m['id'])['hash']==m['hash']
    r=asyncio.run(execute(s,s.queue(e,'task-01',m['id'])))
    assert r['status']=='succeeded' and r['result']['provenance']['material_hash']==m['hash']
    with pytest.raises(ValueError):s.add_material('x',{'unknown':'bad'})

def test_sensitive_input_and_masking(tmp_path):
    from adoptlab.tracing import scrub
    s=Store(tmp_path);e=s.experiment('x');id=s.queue(e,'task-01','A')
    fake='sk-'+'z'*25
    with pytest.raises(ValueError):s.feedback(e,id,fake)
    assert fake not in json.dumps(scrub({'api_key':fake,'path':r'F:\private\secret','text':fake}))
    import adoptlab.web as web
    with TestClient(web.app) as c:
        response=c.post('/api/experiments',json={'title':'x','api_key':fake})
        assert fake not in response.text

def test_cancel_inside_mcp_scope(tmp_path,monkeypatch):
    s=Store(tmp_path);e=s.experiment('cancel');id=s.queue(e,'task-01','A')
    original=s.event
    def event(*a,**kw):
        out=original(*a,**kw)
        if a[1]=='task_started':s.cancel(id)
        return out
    monkeypatch.setattr(s,'event',event)
    r=asyncio.run(execute(s,id));assert r['status']=='cancelled'
    assert r['result']['requests']==0

def test_deadline_inside_mcp_scope(tmp_path,monkeypatch):
    import adoptlab.engine as engine
    monkeypatch.setattr(engine,'EPISODE_SECONDS',.05)
    s=Store(tmp_path);e=s.experiment('deadline');id=s.queue(e,'task-01','A')
    r=asyncio.run(execute(s,id));assert r['status']=='timed_out'

def test_model_request_limit_without_paid_calls(tmp_path,monkeypatch):
    import adoptlab.engine as engine
    for key,value in {'DEEPSEEK_API_KEY':'unit-test','ADOPTLAB_INPUT_PRICE_CNY':'2','ADOPTLAB_OUTPUT_PRICE_CNY':'8','DEEPSEEK_MODEL':'deepseek-flash'}.items():monkeypatch.setenv(key,value)
    class Response:
        status_code=200
        def json(self):return {'model':'test-double','usage':{'prompt_tokens':20,'completion_tokens':5},'choices':[{'message':{'role':'assistant','content':None,'tool_calls':[{'id':'test','type':'function','function':{'name':'list_fixture_files','arguments':'{}'}}]}}]}
    class Client:
        def __init__(self,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,*args,**kwargs):return Response()
    monkeypatch.setattr(engine.httpx,'AsyncClient',Client)
    s=Store(tmp_path);e=s.experiment('limit');id=s.queue(e,'task-01','B','model')
    r=asyncio.run(execute(s,id))
    assert r['status']=='budget_exhausted' and r['result']['requests']==8
    assert r['result']['provenance']['model']=='test-double'

def test_ordered_funnel_and_withdrawal(tmp_path):
    s=Store(tmp_path);e=s.experiment('adoption');id=s.queue(e,'task-01','A','protocol','human_unverified','subject')
    s.event('entry','entry_viewed','human_unverified','subject',source='unknown')
    asyncio.run(execute(s,id));f=s.feedback(e,id,'A synthetic observation')
    funnel=s.funnel()['cohorts'][0];assert funnel['verified_after_start']==1
    s.withdraw('subject')
    assert s.get_run(id)['cohort']=='withdrawn'
    with s.connect() as c:assert c.execute('SELECT COUNT(*) FROM feedback WHERE id=?',(f,)).fetchone()[0]==0

def test_comparison_keeps_browser_and_automation_separate(tmp_path):
    s=Store(tmp_path);e=s.experiment('comparison')
    id=s.queue(e,'task-01','B','protocol','human_unverified','browser')
    asyncio.run(execute(s,id));c=s.comparison(e)
    assert c['groups']['B']['protocol']['total']==0
    assert c['cohorts']['human_unverified']['B']['protocol']['passed']==1
    s.withdraw('browser');c=s.comparison(e)
    assert c['cohorts']['human_unverified']['B']['protocol']['total']==0
    assert c['cohorts']['withdrawn']['B']['protocol']['total']==1
