import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from .config import digest

class ContractError(ValueError):
    def __init__(self, code):
        self.code=code
        super().__init__(code)

def safe_path(root: Path, name: str):
    if not isinstance(name,str) or not name or '\\' in name or ':' in name or name.startswith('/'):
        raise ContractError("PATH_DENIED")
    parts = Path(name).parts
    if any(p in {"..","."} for p in parts):
        raise ContractError("PATH_DENIED")
    root=root.resolve()
    path=root/name
    current=root
    for part in parts:
        current=current/part
        if current.exists() and (current.is_symlink() or getattr(current,"is_junction",lambda:False)()):
            raise ContractError("PATH_DENIED")
        # Python 3.11: detect Windows junctions/reparse points too.
        if current.exists() and getattr(current.lstat(),"st_file_attributes",0)&0x400:
            raise ContractError("PATH_DENIED")
    if not path.resolve().is_relative_to(root):
        raise ContractError("PATH_DENIED")
    return path

def normalize(records: list, min_cents: int):
    if type(min_cents) is not int or min_cents<0 or not isinstance(records,list) or len(records)>1000:
        raise ContractError("INVALID_INPUT")
    result=[]; seen=set()
    for r in records:
        if not isinstance(r,dict) or set(r)!={"id","status","amount","currency","created_at"} or any(not isinstance(x,str) for x in r.values()):
            raise ContractError("INVALID_FIELDS")
        x={k:v.strip() for k,v in r.items()}
        if not x['id'] or x['id'] in seen: raise ContractError("DUPLICATE_ID")
        seen.add(x['id']); x['status']=x['status'].lower(); x['currency']=x['currency'].upper()
        if x['status'] not in {'active','inactive'}: raise ContractError("INVALID_STATUS")
        if x['currency'] not in {'CNY','USD'}: raise ContractError("INVALID_CURRENCY")
        if not re.fullmatch(r'\d{1,12}(?:\.\d{1,2})?',x['amount']): raise ContractError("INVALID_AMOUNT")
        cents=int(Decimal(x['amount'])*100)
        try:
            dt=datetime.fromisoformat(x['created_at'].replace('Z','+00:00'))
            if dt.tzinfo is None: raise ValueError()
            x['created_at']=dt.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
        except ValueError: raise ContractError("INVALID_DATE") from None
        x['amount_cents']=cents; del x['amount']
        if x['status']=='active' and cents>=min_cents: result.append(x)
    result.sort(key=lambda r:r['id'])
    totals={}
    for x in result: totals[x['currency']]=totals.get(x['currency'],0)+x['amount_cents']
    return {"result":result,"summary":{"count":len(result),"totals_cents":totals}}

def verify(task, root, tool_errors):
    """Independent oracle uses integer parsing and its own normalization logic."""
    if task['expected_error']:
        ok=task['expected_error'] in tool_errors and not any((root/'outputs'/n).exists() for n in ['result.json','summary.json'])
        return {"passed":ok,"kind":"correct_rejection","reason":"expected_error_observed" if ok else "rejection_mismatch"}
    expected=[]; totals={}
    for original in task['records']:
        value=original['amount'].strip().split('.')
        cents=int(value[0])*100+int((value[1] if len(value)>1 else '').ljust(2,'0'))
        if original['status'].strip().casefold()!='active' or cents<task['min_cents']: continue
        dt=datetime.fromisoformat(original['created_at'].strip().replace('Z','+00:00')).astimezone(timezone.utc)
        item={'id':original['id'].strip(),'status':'active','currency':original['currency'].strip().upper(),
              'amount_cents':cents,'created_at':dt.isoformat().replace('+00:00','Z')}
        expected.append(item);totals[item['currency']]=totals.get(item['currency'],0)+cents
    expected.sort(key=lambda x:x['id'])
    try:
        actual={name:json.loads(safe_path(root/'outputs',name+'.json').read_text(encoding='utf-8')) for name in ['result','summary']}
    except (OSError,ValueError): return {"passed":False,"kind":"artifact","reason":"missing_or_invalid_outputs"}
    ok=actual=={"result":expected,"summary":{"count":len(expected),"totals_cents":totals}}
    return {"passed":ok,"kind":"artifact","reason":"matched" if ok else "output_mismatch","artifact_hash":digest(actual)}
