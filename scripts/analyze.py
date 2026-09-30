"""Recompute family-level descriptive evidence from stored trials."""
import json
import random
import statistics
from collections import Counter
from pathlib import Path
from adoptlab.store import Store
from adoptlab.tasks import catalog
from adoptlab.config import RUNTIME

def mean(xs):return sum(xs)/len(xs) if xs else None
def interval(values):
    rng=random.Random(20260930); samples=sorted(mean([rng.choice(values) for _ in values]) for _ in range(10000))
    return [samples[249],samples[9749]]

def analyze():
    s=Store();exp=next(e for e in s.experiments() if e['title']=='Frozen exploratory matrix v1')
    rows=s.runs(exp['id']);tasks=catalog();families=sorted({t['family'] for t in tasks.values()})
    detail=[]
    for family in families:
        d={'family':family,'split':next(t['split'] for t in tasks.values() if t['family']==family)}
        for material in ['A','B']:
            group=[r for r in rows if tasks[r['task_id']]['family']==family and r['material']==material]
            d[material]={'n':len(group),'passed':sum(bool(r['result'] and r['result']['verification']['passed']) for r in group),
                         'cost_upper_cny':sum(r['result']['cost_upper_cny'] for r in group if r['result'])}
        d['difference']=d['B']['passed']/d['B']['n']-d['A']['passed']/d['A']['n'];detail.append(d)
    uncertainty={}
    for label in ['all','exploration','held_out']:
        diffs=[f['difference'] for f in detail if label=='all' or f['split']==label]
        uncertainty[label]={'families':len(diffs),'mean_difference':mean(diffs),'family_bootstrap_95_percentile':interval(diffs),
                            'interpretation':'Exploratory family resampling with few clusters; not a population guarantee or significance test.'}
    efficiency={}
    for material in ['A','B']:
        group=[r for r in rows if r['material']==material and r['result']]
        results=[r['result'] for r in group]
        passed=sum(r['status']=='succeeded' for r in group)
        cost=sum(r.get('cost_upper_cny',0) for r in results)
        efficiency[material]={'episodes':len(group),'median_seconds':statistics.median(r['elapsed_seconds'] for r in results),
            'total_model_requests':sum(r['requests'] for r in results),'total_tool_calls':sum(r['tools'] for r in results),
            'cost_upper_cny_per_success':cost/passed if passed else None,
            'interpretation':'Includes failed episodes in total cost; latency is local elapsed time, not a platform speed benchmark.'}
    report={'experiment_id':exp['id'],'comparison':s.comparison(exp['id']),'families':detail,'uncertainty':uncertainty,'efficiency':efficiency,
            'failures':dict(Counter(r['material']+':'+r['result']['verification']['reason'] for r in rows if r['result'] and r['status']!='succeeded')),
            'protocol':'frozen-protocol-v1.json','human_participants':0}
    (RUNTIME/'analysis-v1.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    destination=Path(__file__).resolve().parents[1]/'docs'/'experiment-results.md'
    lines=['# Materials experiment v1','', 'Measured on 2026-09-30 using DeepSeek Flash, temperature 0, thinking disabled, one serial executor. Six synthetic task families, two materials and three correlated trials per task produced 72 episodes. B was fixed before held-out observations.','',
           '| Stratum | A | B |','|---|---:|---:|']
    c=report['comparison']['groups']
    for key,total,title in [('passed','total','All task verdicts'),('normal_passed','normal_total','Valid artifacts'),('rejection_passed','rejection_total','Correct input rejection')]:
        lines.append(f"| {title} | {c['A']['model'][key]}/{c['A']['model'][total]} | {c['B']['model'][key]}/{c['B']['model'][total]} |")
    lines+=['','| Family | Split | A | B |','|---|---|---:|---:|']
    for d in detail:lines.append(f"| {d['family']} | {d['split']} | {d['A']['passed']}/{d['A']['n']} | {d['B']['passed']}/{d['B']['n']} |")
    lines+=['','## Interpretation','',
      'The improved material completed more of these frozen tasks. Empty outputs and invalid inputs accounted for most failures with A. The two variants have identical tool schemas and backend code; descriptions and the onboarding guide change together. This experiment estimates the bundled material effect and does not isolate each wording change.',
      '',f"Usage/reservation-priced cost upper bounds: A ¥{c['A']['model']['cost_upper_cny']:.6f}; B ¥{c['B']['model']['cost_upper_cny']:.6f}. Peak cache-miss rates conservatively price all input; actual invoice charges may be lower. Unresolved network attempts retain their worst-case reservation.",
      '', '## Execution efficiency', '', '| Material | Median seconds | Requests | Tool calls | Cost upper bound per success (CNY) |', '|---|---:|---:|---:|---:|',
      *[f"| {v} | {d['median_seconds']:.3f} | {d['total_model_requests']} | {d['total_tool_calls']} | {d['cost_upper_cny_per_success']:.6f} |" for v,d in efficiency.items()],
      '', 'Cost per success includes failed attempts. Elapsed time includes this local workflow and network conditions; it does not rank competitive platforms. Token counts and requests remain in the private execution traces.',
      '', 'Family-level uncertainty:', '```json',json.dumps(uncertainty,indent=2),'```','',
      'Three held-out families and three trials per task support exploratory comparisons. Trial repetition, a single model, synthetic records and preselected task families limit transfer. This result measures model task performance. Independent human integration, product-market fit, retention and revenue await real user evidence.',
      '', 'Recompute: `python scripts/analyze.py`. Original traces and the frozen protocol remain outside the repository in the local runtime directory. A public report omits credentials, personal paths, subject IDs and free text.']
    destination.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (destination.parent/'experiment-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'episodes':len(rows),'families':detail,'uncertainty':uncertainty}))

if __name__=='__main__':analyze()
