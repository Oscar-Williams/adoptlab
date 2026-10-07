"""Merge reviewed terminal local evidence without replacing historical records.

Stop services using either root before invoking. Credentials are never copied.
Colliding IDs must be identical (built-in material creation dates may differ).
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import uuid

TABLES=('materials','registry','material_metadata','experiments','runs','events','feedback','revisions','charges','release_checks','observations')


def files(root):
    result={}
    if not root.exists():return result
    for p in root.rglob('*'):
        if p.is_symlink():raise ValueError('SYMLINK_ARTIFACT_DENIED')
        if p.is_file():result[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def merge(source, destination):
    source=Path(source).resolve();destination=Path(destination).resolve()
    if source==destination or source in destination.parents or destination in source.parents:raise ValueError('DISTINCT_RUNTIME_ROOTS_REQUIRED')
    source_db=source/'adoptlab.db';destination_db=destination/'adoptlab.db'
    with sqlite3.connect(source_db.as_uri()+'?mode=ro',uri=True) as src, sqlite3.connect(destination_db) as dst:
        src.row_factory=dst.row_factory=sqlite3.Row
        if any(c.execute('PRAGMA user_version').fetchone()[0]!=3 for c in [src,dst]):raise ValueError('SCHEMA_3_REQUIRED')
        if src.execute("SELECT 1 FROM runs WHERE status IN ('queued','running')").fetchone() or dst.execute("SELECT 1 FROM runs WHERE status='running'").fetchone():raise ValueError('TERMINAL_SOURCE_AND_IDLE_DESTINATION_REQUIRED')
        dst.execute('PRAGMA foreign_keys=ON')
        pending=[];summary={}
        for table in TABLES:
            info=src.execute('PRAGMA table_info('+table+')').fetchall()
            keys=[r['name'] for r in sorted(info,key=lambda r:r['pk']) if r['pk']]
            columns=[r['name'] for r in info]
            if columns!=[r['name'] for r in dst.execute('PRAGMA table_info('+table+')')]:raise ValueError('COLUMN_MISMATCH')
            for row in src.execute('SELECT * FROM '+table):
                old=dst.execute('SELECT * FROM '+table+' WHERE '+' AND '.join(k+'=?' for k in keys),tuple(row[k] for k in keys)).fetchone()
                if old:
                    compare=columns if table!='materials' else [c for c in columns if c!='created']
                    if any(old[k]!=row[k] for k in compare):raise ValueError('CONFLICTING_IMMUTABLE_RECORD:'+table)
                else:pending.append((table,columns,tuple(row)));summary[table]=summary.get(table,0)+1
        copies=[]
        for row in src.execute('SELECT id FROM runs'):
            run_id=row['id']
            if len(run_id)!=32 or any(c not in '0123456789abcdef' for c in run_id):raise ValueError('INVALID_RUN_PATH')
            folder=source/'runs'/run_id;target=destination/'runs'/run_id
            if not folder.exists():continue
            if target.exists():
                if files(folder)!=files(target):raise ValueError('CONFLICTING_ARTIFACTS')
            else:
                files(folder);copies.append((folder,target))
        for row in src.execute("SELECT id FROM registry WHERE kind='verifier'"):
            folder=source/'verifiers'/(row['id']+'.py');target=destination/'verifiers'/(row['id']+'.py')
            if folder.parent.resolve()!= (source/'verifiers').resolve():raise ValueError('INVALID_VERIFIER_PATH')
            if not folder.is_file() or folder.is_symlink():raise ValueError('MISSING_VERIFIER')
            if target.exists() and target.read_bytes()!=folder.read_bytes():raise ValueError('CONFLICTING_VERIFIER')
            if not target.exists():copies.append((folder,target))
        backup=destination/('adoptlab.pre-import.'+uuid.uuid4().hex+'.db')
        with sqlite3.connect(backup) as recovery:dst.backup(recovery)
        before=dst.execute('SELECT COALESCE(SUM(COALESCE(actual,reserved)),0) FROM charges').fetchone()[0]
        added=sum(row[2][2] if row[2][3] is None else row[2][3] for row in pending if row[0]=='charges')
        if before+added>200:raise ValueError('BUDGET_LEDGER_LIMIT')
        for folder,target in copies:
            target.parent.mkdir(parents=True,exist_ok=True)
            if folder.is_dir():shutil.copytree(folder,target)
            else:shutil.copy2(folder,target)
        dst.execute('BEGIN IMMEDIATE')
        try:
            for table,columns,row in pending:
                dst.execute('INSERT INTO '+table+' ('+','.join(columns)+') VALUES ('+','.join('?' for _ in row)+')',row)
            if dst.execute('PRAGMA foreign_key_check').fetchone():raise ValueError('BROKEN_REFERENCE')
            dst.commit()
        except Exception:
            dst.rollback();raise
        after=dst.execute('SELECT COALESCE(SUM(COALESCE(actual,reserved)),0) FROM charges').fetchone()[0]
        report={'schema':'adoptlab-runtime-import-v1','added':summary,'copied_artifact_sets':len(copies),'cost_before_cny':before,'cost_after_cny':after,'backup':backup.name,'historical_rows_replaced':0}
        (destination/('import-'+backup.stem+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
        return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path);parser.add_argument('--destination',required=True,type=Path)
    args=parser.parse_args();print(json.dumps(merge(args.source,args.destination)))
