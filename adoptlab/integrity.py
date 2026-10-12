"""Evidence snapshots and transactional retries for maintainer decisions."""
import json
import re
from .config import digest


def replay(connection, scope, key, payload):
    if key is None:
        return None
    if not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', key):
        raise ValueError('INVALID_IDEMPOTENCY_KEY')
    row = connection.execute('SELECT payload_hash,response_id FROM submissions WHERE scope=? AND key=?', (scope, key)).fetchone()
    if row:
        if row['payload_hash'] != digest(payload):
            raise ValueError('IDEMPOTENCY_CONFLICT')
        return row['response_id']


def remember(connection, scope, key, payload, response):
    if key is not None:
        connection.execute('INSERT INTO submissions VALUES(?,?,?,?)', (scope, key, digest(payload), response))


def snapshot(store, run_id, require_pass=False):
    from .engine import reverify
    run = store.get_run(run_id)
    task = store.task(run['task_id'])
    if task.get('verifier'):
        raise ValueError('EXPLICIT_VERIFIER_REQUIRED')
    try:
        checked = reverify(store, run_id)
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError('REVISION_EVIDENCE_UNAVAILABLE') from exc
    if not all(checked.get(k) for k in ('manifest_matches_db', 'task_matches', 'artifact_hash_matches')):
        raise ValueError('REVISION_EVIDENCE_CHANGED')
    provenance = run['result'].get('provenance', {})
    if provenance.get('material_hash') != store.material(run['material'])['hash']:
        raise ValueError('REVISION_MATERIAL_CHANGED')
    if require_pass and (run['status'] != 'succeeded' or not checked['verification']['passed']):
        raise ValueError('REVISION_NOT_VERIFIED')
    return {'run_id': run_id, 'result_hash': digest(run['result']), 'task_hash': digest(task),
            'material_hash': provenance['material_hash'], 'condition': store.condition(run),
            'artifact_hash': checked['verification'].get('artifact_hash'),
            'passed': checked['verification']['passed']}


def revision_state(store, revision):
    with store.connect() as c:
        row = c.execute('SELECT content FROM revision_evidence WHERE revision_id=?', (revision['id'],)).fetchone()
    if not row:
        return {'status': 'historical', 'reason': 'NO_CURRENT_SNAPSHOT'}
    saved = json.loads(row['content'])
    try:
        current = {'old': snapshot(store, revision['old_run']), 'new': snapshot(store, revision['new_run'], True)}
        valid = all(current[k] == saved[k] for k in ('old', 'new'))
        return {'status': 'verified' if valid else 'stale', 'verified_at': saved['verified_at']}
    except ValueError as exc:
        return {'status': 'stale', 'verified_at': saved['verified_at'], 'reason': str(exc)}
