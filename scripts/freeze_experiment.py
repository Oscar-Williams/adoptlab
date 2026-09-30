import json
from datetime import datetime,timezone
from adoptlab.config import RUNTIME,digest,CODE
from adoptlab.tasks import catalog,MATERIALS
from adoptlab.store import Store

protocol={'id':'materials-v1','frozen_at':datetime.now(timezone.utc).isoformat(),'mode':'model','model':'deepseek-flash','temperature':0,'thinking':'disabled',
          'requests_per_episode':8,'output_tokens_per_request':1024,'input_bound':16000,'episode_seconds':180,'trials':3,
          'tasks':{k:{'family':t['family'],'split':t['split'],'hash':digest(t)} for k,t in catalog().items()},
          'materials':{k:digest(v) for k,v in MATERIALS.items()},'code':{name:digest((CODE/'adoptlab'/name).read_text(encoding='utf-8')) for name in ['contract.py','server.py','engine.py','tasks.py']},
          'primary':'Task success, with valid-output and correct-rejection strata reported separately. Failures and exhausted runs remain in denominator.',
          'cost':'Peak input-miss/output rates 2/8 CNY per million. Report usage-priced upper bound; invoice may be lower.',
          'worst_model_cny':72*8*(16000*2+1024*8)/1e6,'existing_cost':Store().cost(),
          'limits':'Six task families, three held-out families. Repeated trials are correlated. No human adoption or population causal claim.',
          'selection':'B fixed before held-out observations; no updates to A/B during this matrix. Alternate order per task/trial. No application response cache.'}
RUNTIME.mkdir(parents=True,exist_ok=True)
path=RUNTIME/'frozen-protocol-v1.json'
if path.exists():raise SystemExit('Protocol already exists; create a new version for changes.')
path.write_text(json.dumps(protocol,indent=2),encoding='utf-8')
print(json.dumps({'frozen':True,'episodes':72,'worst_cny':protocol['worst_model_cny']}))
