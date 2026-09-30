import argparse
import asyncio
import json
from pathlib import Path
from .config import doctor, RUNTIME
from .store import Store
from .engine import execute, reverify
from .tasks import catalog

def main():
    parser=argparse.ArgumentParser(description='AdoptLab: verify first value and compare onboarding materials')
    subs=parser.add_subparsers(dest='command',required=True)
    subs.add_parser('doctor')
    run=subs.add_parser('run');run.add_argument('--config',type=Path,required=True)
    compare=subs.add_parser('compare');compare.add_argument('--experiment',required=True)
    verify=subs.add_parser('verify');verify.add_argument('--run',required=True)
    serve=subs.add_parser('serve');serve.add_argument('--port',type=int,default=8766)
    args=parser.parse_args()
    if args.command=='doctor':out=doctor()
    elif args.command=='serve':
        import uvicorn
        uvicorn.run('adoptlab.web:app',host='127.0.0.1',port=args.port);return
    else:
        store=Store()
        if args.command=='run':
            config=json.loads(args.config.read_text(encoding='utf-8'))
            allowed={'title','mode','tasks','materials','trials','experiment_id'}
            if set(config)-allowed:raise ValueError('UNKNOWN_CONFIG_FIELD')
            if config.get('trials',1) not in range(1,4):raise ValueError('INVALID_TRIALS')
            exp=config.get('experiment_id') or store.experiment(config.get('title','Onboarding comparison'))
            tasks=config.get('tasks',list(catalog())); variants=config.get('materials',['A','B'])
            # Alternating order controls fixed position effects, all trials remain correlated.
            for trial in range(1,config.get('trials',1)+1):
                for ti,task in enumerate(tasks):
                    for material in variants if (ti+trial)%2 else list(reversed(variants)):
                        id=store.queue(exp,task,material,config.get('mode','protocol'),trial=trial)
                        r=asyncio.run(execute(store,id))
                        print(json.dumps({'run_id':id,'task_id':task,'material':material,'status':r['status'],'result':r['result']},ensure_ascii=False),flush=True)
                        if r['result'] and r['result']['error_code'] in {'credentials_missing','unpriced_model','prices_missing_or_under_reserved','model_http_401','model_http_402'}:
                            print(json.dumps({'experiment_id':exp,'stopped':'configuration_or_account_gate'}));return
            out=store.export(exp)
            (store.root/(exp+'.report.json')).write_text(json.dumps(out,indent=2),encoding='utf-8')
        elif args.command=='compare':out=store.comparison(args.experiment)
        else:out=reverify(store,args.run)
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
