import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
import pytest
from adoptlab.store import Store
from adoptlab.engine import execute


def pair(tmp_path):
    s=Store(tmp_path);e=s.experiment('integrity')
    a=s.queue(e,'task-01','A');b=s.queue(e,'task-01','B')
    asyncio.run(execute(s,a));asyncio.run(execute(s,b))
    return s,e,a,b


def test_concurrent_feedback_retry_and_conflict(tmp_path):
    s=Store(tmp_path);e=s.experiment('retry');run=s.queue(e,'task-01','A')
    with ThreadPoolExecutor(max_workers=6) as pool:
        ids=list(pool.map(lambda _:s.feedback(e,run,'field unclear','retry-key-1'),range(8)))
    assert len(set(ids))==1
    with pytest.raises(ValueError,match='IDEMPOTENCY_CONFLICT'):
        s.feedback(e,run,'different feedback','retry-key-1')
    assert s.feedback(e,run,'field unclear','new-intent-1')!=ids[0]
    with s.connect() as c:
        assert c.execute('SELECT count(*) FROM feedback').fetchone()[0]==2
        assert c.execute("SELECT count(*) FROM events WHERE name='feedback_submitted'").fetchone()[0]==2


def test_revision_revalidates_and_detects_staleness(tmp_path):
    s,e,a,b=pair(tmp_path);f=s.feedback(e,a,'clarify')
    rev=s.revision(f,b,'explicit contract','revision-key-1')
    assert s.revision(f,b,'explicit contract','revision-key-1')==rev
    assert s.handoff(e)['revisions'][0]['verification']['status']=='verified'
    output=next((tmp_path/'runs'/b/'outputs').glob('*'));original=output.read_bytes()
    output.write_text('{}')
    assert s.handoff(e)['revisions'][0]['verification']['status']=='stale'
    f2=s.feedback(e,a,'second issue')
    with pytest.raises(ValueError,match='REVISION_EVIDENCE_CHANGED'):
        s.revision(f2,b,'new decision')
    output.write_bytes(original)
    assert s.handoff(e)['revisions'][0]['verification']['status']=='verified'
    s.withdraw('automation')
    with s.connect() as c:
        assert c.execute('SELECT count(*) FROM revision_evidence').fetchone()[0]==0
        assert c.execute('SELECT count(*) FROM submissions').fetchone()[0]==0


def test_unknown_model_does_not_suppress_protocol_set(tmp_path):
    s,e,a,b=pair(tmp_path)
    run=s.queue(e,'task-01','A','model')
    s.finish(run,'failed',{'verification':{'passed':False},'provenance':{}})
    data=s.comparison(e)
    assert not data['comparable']
    assert next(g for g in data['comparison_sets'] if g['mode']=='protocol')['status']=='COMPARABLE'
    assert next(g for g in data['comparison_sets'] if g['mode']=='model')['status']=='INSUFFICIENT'
    s.queue(e,'task-02','B')
    assert next(g for g in s.comparison(e)['comparison_sets'] if g['mode']=='protocol')['status']=='INSUFFICIENT'


def test_schema_three_backup_and_readback(tmp_path):
    s=Store(tmp_path);e=s.experiment('historical')
    with s.connect() as c:
        c.execute('DROP TABLE submissions');c.execute('DROP TABLE revision_evidence');c.execute('PRAGMA user_version=3')
    s=Store(tmp_path)
    assert s.get_experiment(e)['title']=='historical'
    assert (tmp_path/'adoptlab.pre-v05.db').exists()
    with s.connect() as c:assert c.execute('PRAGMA user_version').fetchone()[0]==4


def test_settlement_retry_preserves_observed_cost(tmp_path):
    s=Store(tmp_path);e=s.experiment('cost');run=s.queue(e,'task-01','A')
    charge=s.reserve(run,1);usage={'prompt_tokens':10,'completion_tokens':2}
    s.settle(charge,.1,usage);s.settle(charge,.1,usage)
    assert s.cost()['upper_bound_cny']==.1
    with pytest.raises(ValueError,match='SETTLEMENT_CONFLICT'):s.settle(charge,.2,usage)
    with pytest.raises(ValueError,match='INVALID_SETTLEMENT'):s.settle(charge,float('nan'),usage)
    assert s.cost()['upper_bound_cny']==.1


def test_json_syntax_positions_match_invalid_character():
    import shutil,subprocess
    from pathlib import Path
    node=shutil.which('node')
    if not node:pytest.skip('Node runtime unavailable')
    source=(Path(__file__).parents[1]/'adoptlab/static/json-position.js').read_text()
    cases=[('{\n  "id":\n}',10),('{"x": [1,]}',9),('{"a" 1}',5),('true false',5)]
    program=source+'\nconst cases='+json.dumps(cases)+'; for(const [s,p] of cases){if(jsonErrorPosition(s)!==p)throw Error(s+":"+jsonErrorPosition(s)+" expected "+p);}'
    subprocess.run([node,'-e',program],check=True,capture_output=True)
