"""Paired factorial summaries with exploratory family-cluster bootstrap intervals."""
import json
import random
from collections import defaultdict
from adoptlab.config import RUNTIME
from adoptlab.tasks import catalog

def main():
    report=json.loads((RUNTIME/'v02-factorial-results.json').read_text(encoding='utf-8'))
    from adoptlab.store import Store
    comparison=Store().comparison(report['experiment_id'])
    if not comparison['comparable']:raise ValueError('INCOMPATIBLE_EXECUTION_CONDITIONS')
    reverse={v:k for k,v in report['protocol']['variants'].items()}
    groups={};paired=defaultdict(dict)
    for row in report['runs']:
        if row['mode']!='model':continue
        v=reverse[row['material']];passed=int(row['status']=='succeeded' and row['result']['verification']['passed'])
        g=groups.setdefault(v,{'total':0,'passed':0,'cost_upper_cny':0,'requests':0,'statuses':{}})
        g['total']+=1;g['passed']+=passed;g['cost_upper_cny']+=row['result']['cost_upper_cny'];g['requests']+=row['result']['requests'];g['statuses'][row['status']]=g['statuses'].get(row['status'],0)+1
        paired[(row['task_id'],row['trial'])][v]=passed
    effects=defaultdict(list);family=defaultdict(lambda:defaultdict(list))
    for (task,trial),v in paired.items():
        if set(v)!={'AA','AB','BA','BB'}:raise ValueError('INCOMPLETE_FACTORIAL_PAIR')
        values={'guide':((v['BA']-v['AA'])+(v['BB']-v['AB']))/2,
                'description':((v['AB']-v['AA'])+(v['BB']-v['BA']))/2,
                'interaction':v['BB']-v['BA']-v['AB']+v['AA']}
        for key,value in values.items():effects[key].append(value);family[catalog()[task]['family']][key].append(value)
    rng=random.Random(20261001);estimates={};families=list(family)
    for key,values in effects.items():
        means=[sum(family[f][key])/len(family[f][key]) for f in families]
        samples=sorted(sum(rng.choices(means,k=len(means)))/len(means) for _ in range(2000))
        estimates[key]={'effect_percentage_points':100*sum(values)/len(values),'exploratory_family_bootstrap_95_percent_interval_pp':[100*samples[50],100*samples[1949]],'clusters':len(families)}
    splits={}
    for split in {t['split'] for t in catalog().values()}:
        splits[split]={v:{'total':sum(1 for r in report['runs'] if r['mode']=='model' and reverse[r['material']]==v and catalog()[r['task_id']]['split']==split),'passed':sum(r['status']=='succeeded' and r['result']['verification']['passed'] for r in report['runs'] if r['mode']=='model' and reverse[r['material']]==v and catalog()[r['task_id']]['split']==split)} for v in groups}
    out={'groups':groups,'effects':estimates,'splits':splits,'observed_models':comparison['observed_models'],'unknown_responder_runs':comparison['unknown_responder_runs'],'interpretation':'Six synthetic families, one requested model, correlated repeats. Runs failing before a model response retain an unknown responder; failures remain in denominators. Cluster intervals are exploratory with few clusters. No causal human-adoption claim.'}
    (RUNTIME/'v02-analysis.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out))

if __name__=='__main__':main()
