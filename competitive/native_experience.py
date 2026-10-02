"""Native Promptfoo MCP experience, with private outputs and budgeted model relay."""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import httpx
from adoptlab.config import CODE,RUNTIME,load_credentials
from adoptlab.store import Store
from adoptlab.tasks import catalog,MATERIALS,public_task
from adoptlab.contract import verify

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--promptfoo',type=Path,required=True);parser.add_argument('--model',action='store_true');args=parser.parse_args()
    load_credentials();ledger=Store();output=RUNTIME.parent/'competitive'/'native-v03';output.mkdir(parents=True,exist_ok=True)
    experiment=ledger.experiment('Native Promptfoo MCP experience');records=[]
    cases=[('task-01','A'),('task-01','B'),('task-11','A'),('task-11','B')] if args.model else [('task-01','B')]
    for task_id,material in cases:
        run_id=ledger.queue(experiment,task_id,material,'model' if args.model else 'protocol')
        # Ledger-only marker: Promptfoo owns this run, so AdoptLab cannot execute it.
        if not ledger.claim(run_id):raise SystemExit('EXECUTOR_BUSY: reconcile interrupted runs or wait for active execution.')
        root=output/run_id;(root/'fixtures').mkdir(parents=True);(root/'outputs').mkdir()
        task=catalog()[task_id];(root/'fixtures'/'records.json').write_text(json.dumps(task['records']),encoding='utf-8')
        charges=[];requests=0;cost=0;lock=threading.Lock()
        class Relay(BaseHTTPRequestHandler):
            def log_message(self,*a):pass
            def do_POST(self):
                nonlocal requests,cost
                status=500;body={'error':'relay_error'}
                if self.path!='/v1/chat/completions':status=404;body={'error':'route_denied'}
                else:
                    try:
                        size=int(self.headers.get('Content-Length','0'))
                        if size>16000:raise ValueError('INPUT_BOUND')
                        payload=json.loads(self.rfile.read(size));payload.update(model='deepseek-flash',max_tokens=1024,stream=False,thinking={'type':'disabled'})
                        with lock:
                            if requests>=8:raise ValueError('REQUEST_LIMIT')
                            charge=ledger.reserve(run_id,(16000*2+1024*8)/1e6);requests+=1;cost+=(16000*2+1024*8)/1e6
                        try:
                            response=httpx.post('https://api.deepseek.com/chat/completions',headers={'Authorization':'Bearer '+os.environ['DEEPSEEK_API_KEY']},json=payload,timeout=40)
                        except httpx.RequestError:
                            charges.append({'state':'unresolved'});raise ValueError('NETWORK_OUTCOME_UNKNOWN')
                        status=response.status_code
                        if status!=200:body={'error':'model_http_'+str(status)};charges.append({'state':'unresolved','http':status})
                        else:
                            body=response.json();usage=body.get('usage',{});actual=(usage.get('prompt_tokens',0)*2+usage.get('completion_tokens',0)*8)/1e6
                            if not {'prompt_tokens','completion_tokens'}<=usage.keys():raise ValueError('USAGE_MISSING')
                            ledger.settle(charge,actual,usage);cost+=actual-(16000*2+1024*8)/1e6;charges.append({'state':'settled','usage':usage,'cost_upper_cny':actual})
                    except (ValueError,KeyError) as e:status=400;body={'error':str(e) if str(e).isupper() else 'relay_request_error'}
                data=json.dumps(body).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        relay=ThreadingHTTPServer(('127.0.0.1',0),Relay) if args.model else None
        if relay:threading.Thread(target=relay.serve_forever,daemon=True).start()
        server={'command':sys.executable,'args':[str(CODE/'competitive'/'native_server.py'),str(root),material],'name':'synthetic-records'}
        if args.model:
            provider={'id':'openai:chat:deepseek-flash','config':{'apiBaseUrl':f'http://127.0.0.1:{relay.server_port}/v1','apiKey':'local-relay-placeholder','max_tokens':1024,'temperature':0,'mcp':{'enabled':True,'server':server}}}
            prompt=json.dumps([{'role':'system','content':MATERIALS[material]['guide']},{'role':'user','content':json.dumps(public_task(task))}])
            tests=[{'vars':{},'assert':[{'type':'javascript','value':'(context.providerResponse.metadata?.toolCalls?.length || 0) > 0'}]}]
        else:
            provider={'id':'mcp','config':{'enabled':True,'server':server}}
            prompt='{{call}}'
            calls=[{'tool':'list_fixture_files','args':{}},{'tool':'read_records','args':{'path':'records.json'}},{'tool':'normalize_filter_records','args':{'records':task['records'],'min_cents':task['min_cents']}},{'tool':'normalize_filter_records','args':{'records':catalog()['task-11']['records'],'min_cents':1000}}]
            tests=[{'vars':{'call':json.dumps(c)},'assert':[{'type':'contains','value':v}]} for c,v in zip(calls,['records.json','records','summary','DUPLICATE_ID'])]
        config={'description':'Native MCP experience; synthetic data only','providers':[provider],'prompts':[prompt],'tests':tests}
        cfg=root/'config.json';cfg.write_text(json.dumps(config,indent=2),encoding='utf-8')
        env={k:v for k,v in os.environ.items() if not any(s in k.upper() for s in ['KEY','TOKEN','SECRET','PASSWORD'])}
        # The only HTTP destination in this process is the loopback relay.
        for name in list(env):
            if 'PROXY' in name.upper():env.pop(name)
        env.update(PYTHONPATH=str(CODE),PROMPTFOO_DISABLE_TELEMETRY='1',PROMPTFOO_DISABLE_UPDATE_CHECK='1',PROMPTFOO_CONFIG_DIR=str(output/'state'),PROMPTFOO_CACHE_ENABLED='false',PROMPTFOO_MAX_CONCURRENCY='1')
        started=time.monotonic()
        try:r=subprocess.run([str(args.promptfoo),'eval','-c',str(cfg),'--no-cache','--max-concurrency','1','--output',str(root/'result.json')],env=env,capture_output=True,text=True,encoding='utf-8',timeout=150)
        except subprocess.TimeoutExpired:r=None
        finally:
            if relay:relay.shutdown();relay.server_close()
        (root/'console.log').write_text((r.stdout+'\n'+r.stderr) if r else 'PROCESS_TIMEOUT',encoding='utf-8')
        data=json.loads((root/'result.json').read_text(encoding='utf-8')) if (root/'result.json').exists() else {}
        checks=data.get('results',{}).get('stats',{})
        verification=verify(task,root,[])
        item={'task_id':task_id,'material':material,'path':'native-model-mcp' if args.model else 'native-mcp-provider','process_exit':r.returncode if r else None,'assertion_stats':checks,'contract_passed':verification['passed'],'contract_reason':verification['reason'],'requests':requests,'cost_upper_cny':round(cost,8),'elapsed_seconds':round(time.monotonic()-started,3),'charges':charges}
        records.append(item)
        # Native runs keep their own report semantics, outside the frozen matrix.
        ledger.finish(run_id,'succeeded' if verification['passed'] else 'failed',{'verification':verification,'requests':requests,'cost_upper_cny':cost,'source':'promptfoo_native'})
        print(json.dumps(item),flush=True)
    (output/('model-summary.json' if args.model else 'protocol-summary.json')).write_text(json.dumps({'source':'actual_competitor_execution','records':records},indent=2),encoding='utf-8')

if __name__=='__main__':main()
