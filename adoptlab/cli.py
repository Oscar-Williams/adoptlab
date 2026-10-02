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
    check=subs.add_parser('doctor');check.add_argument('--target',choices=['builtin','filesystem','model'])
    subs.add_parser('first-task')
    for command in ['register-profile','register-task','check-task']:
        p=subs.add_parser(command);p.add_argument('--file',type=Path,required=True)
    subs.add_parser('history')
    plugin=subs.add_parser('register-verifier');plugin.add_argument('--id',required=True);plugin.add_argument('--file',type=Path,required=True)
    reconcile=subs.add_parser('reconcile');reconcile.add_argument('--run',required=True)
    run=subs.add_parser('run');run.add_argument('--config',type=Path,required=True)
    compare=subs.add_parser('compare');compare.add_argument('--experiment',required=True)
    verify=subs.add_parser('verify');verify.add_argument('--run',required=True)
    serve=subs.add_parser('serve');serve.add_argument('--port',type=int,default=8766)
    args=parser.parse_args()
    if args.command=='doctor':out=doctor(args.target)
    elif args.command=='serve':
        import uvicorn
        uvicorn.run('adoptlab.web:app',host='127.0.0.1',port=args.port);return
    else:
        try:store=Store()
        except OSError:
            if args.command!='first-task':raise
            print(json.dumps({'passed':False,'error':'RUNTIME_UNWRITABLE','next_action':'Set ADOPTLAB_RUNTIME to a writable directory on your data drive, then start again.'}))
            raise SystemExit(1)
        if args.command=='first-task':
            from .onboarding import first_task
            out=asyncio.run(first_task(store))
            print(json.dumps(out,ensure_ascii=False,indent=2))
            raise SystemExit(0 if out['passed'] else 1)
        elif args.command=='register-verifier':out=store.register_verifier(args.id,args.file)
        elif args.command in {'register-profile','register-task','check-task'}:
            data=json.loads(args.file.read_text(encoding='utf-8'))
            if args.command=='check-task':
                from .packages import validate_task
                validate_task(data);out={'valid':True,'task_id':data['id']}
            else:out=store.register('profile' if args.command=='register-profile' else 'task',data)
        elif args.command=='history':out=store.runs()
        elif args.command=='reconcile':out=store.reconcile(args.run)
        elif args.command=='run':
            config=json.loads(args.config.read_text(encoding='utf-8'))
            allowed={'title','mode','tasks','materials','trials','experiment_id','settings'}
            if set(config)-allowed:raise ValueError('UNKNOWN_CONFIG_FIELD')
            if config.get('trials',1) not in range(1,4):raise ValueError('INVALID_TRIALS')
            exp=config.get('experiment_id') or store.experiment(config.get('title','Onboarding comparison'),config.get('settings'))
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
        else:
            if not (store.root/'runs'/args.run/'manifest.json').is_file():
                store.get_run(args.run)
                print(json.dumps({'error':'ARTIFACTS_UNAVAILABLE','next_action':'Inspect the terminal status and start a new run explicitly after resolving the issue.'}))
                raise SystemExit(1)
            out=reverify(store,args.run,extensions=True)
    print(json.dumps(out,ensure_ascii=False,indent=2))
    if args.command=='doctor' and args.target and not out['ready']:raise SystemExit(1)

if __name__=='__main__':main()
