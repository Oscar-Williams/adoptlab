import asyncio
import sqlite3
import pytest
from adoptlab.store import Store
from adoptlab.engine import execute
from scripts.import_runtime import merge


def test_runtime_import_preserves_history_budget_and_is_idempotent(tmp_path):
    old=Store(tmp_path/'old');new=Store(tmp_path/'new')
    history=old.experiment('history');paid=old.queue(history,'task-01','B')
    charge=old.reserve(paid,1);old.finish(paid,'uncertain',{'verification':{'passed':False}})
    pending=old.queue(history,'task-02','B')
    fresh=new.experiment('fresh');run=new.queue(fresh,'task-01','B');asyncio.run(execute(new,run))
    old_row=old.get_run(paid)
    result=merge(new.root,old.root)
    assert result['historical_rows_replaced']==0 and result['cost_after_cny']==1
    assert old.get_run(paid)==old_row and old.get_run(run)['status']=='succeeded'
    assert old.get_run(pending)['status']=='queued'
    assert (old.root/'runs'/run/'manifest.json').exists()
    with sqlite3.connect(old.root/result['backup']) as c:
        assert c.execute('SELECT COUNT(*) FROM experiments').fetchone()[0]==1
    assert merge(new.root,old.root)['added']=={}
    with new.connect() as c:c.execute("UPDATE experiments SET title='changed' WHERE id=?",(fresh,))
    with pytest.raises(ValueError,match='CONFLICTING_IMMUTABLE_RECORD'):merge(new.root,old.root)
