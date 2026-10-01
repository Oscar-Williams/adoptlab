import asyncio
import json
import os
import sys
import time
from datetime import timedelta
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .config import CODE, load_credentials, digest
from .contract import verify
from .store import Store, uid
from .tasks import catalog, MATERIALS, public_task
from .packages import safe_path,container_args,readiness,verify_rules,verify_task,docker_command
EXECUTOR_HASH=digest((CODE/'adoptlab'/'engine.py').read_text(encoding='utf-8'))

class StopRun(Exception):pass
EPISODE_SECONDS=180

def classify_error(error):
    leaves=[]
    def walk(e):
        if isinstance(e,BaseExceptionGroup):
            for child in e.exceptions:walk(child)
        else:leaves.append(e)
    walk(error)
    for e in leaves:
        if isinstance(e,StopRun):
            code=str(e)
            return code,{'cancelled':'cancelled','request_limit':'budget_exhausted','output_limit':'budget_exhausted','BUDGET_EXHAUSTED':'budget_exhausted'}.get(code,'failed')
        if isinstance(e,TimeoutError):return 'episode_timeout','timed_out'
        if isinstance(e,asyncio.CancelledError):return 'cancelled','cancelled'
    return type(leaves[0]).__name__ if leaves else type(error).__name__,'failed'

def decode(result):
    if result.isError:return {'error':'MCP_TOOL_ERROR'}
    if result.structuredContent is not None:return result.structuredContent if isinstance(result.structuredContent,dict) else {'value':result.structuredContent}
    texts=[c.text for c in result.content if hasattr(c,'text')]
    try:
        value=json.loads('\n'.join(texts))
        return value if isinstance(value,dict) else {'value':value}
    except ValueError:return {'text':'\n'.join(texts)} if texts else {'error':'UNSUPPORTED_CONTENT'}

async def execute(store:Store,id:str,recorder=None):
    if not store.claim(id):return store.get_run(id)
    run=store.get_run(id);task=store.task(run['task_id']);root=store.root/'runs'/id
    exp=store.get_experiment(run['experiment_id'])['config']
    generic='profile' in task
    material=store.material(run['material'])['content']
    for sub in ['fixtures','outputs']: (root/sub).mkdir(parents=True,exist_ok=False)
    if generic:
        for name,text in task.get('fixtures',{}).items():
            path=safe_path(root/'fixtures',name);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
    else:(root/'fixtures'/'records.json').write_text(json.dumps(task['records']),encoding='utf-8')
    # Verification inputs are never supplied to the MCP process.
    errors=[];trace=[];requests=0;cost=0;start=time.monotonic();code=None
    from importlib.metadata import version
    profile=store.registered('profile',task['profile']) if generic else None
    provenance={"contract":'task-package-v1' if generic else "records-normalize-v1","material_hash":digest(material),
                "task_hash":digest(task),"catalog_hash":exp['task_hash'],
                "executor_hash":EXECUTOR_HASH,
                "backend_hash":digest(profile) if generic else digest((CODE/'adoptlab'/'server.py').read_text(encoding='utf-8')),
                "verifier_hash":digest((CODE/'adoptlab'/('packages.py' if generic else 'contract.py')).read_text(encoding='utf-8')),
                "profile_hash":digest(profile),"model_config_hash":digest(exp),
                "dependencies":{p:version(p) for p in ['mcp','httpx']},"model":None}
    if generic and task.get('verifier'):provenance['verifier_hash']=digest({'rules':provenance['verifier_hash'],'extension':store.verifier(task['verifier'])['hash']})
    store.event(uid(),'task_started',run['cohort'],run['subject'],id,internal=True)
    env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','COMSPEC','TEMP','TMP','PATHEXT','USERPROFILE','APPDATA','LOCALAPPDATA'}}
    env.update(ADOPTLAB_RUN_ROOT=str(root),ADOPTLAB_MATERIAL=run['material'],PYTHONPATH=str(CODE),PYTHONIOENCODING='utf-8')
    env['ADOPTLAB_MATERIAL_DATA']=json.dumps(material)
    async def stopped():
        if store.get_run(id)['cancelled']:raise StopRun('cancelled')
    async def workflow():
        nonlocal requests,cost
        if generic:
            check=readiness()
            if not check['ready']:raise StopRun(check['reason'])
            params=StdioServerParameters(command=docker_command(),args=container_args(profile,root,'adoptlab-'+id),env=env)
        else:params=StdioServerParameters(command=sys.executable,args=['-m','adoptlab.server'],env=env)
        async with stdio_client(params) as streams:
            async with ClientSession(*streams,read_timeout_seconds=timedelta(seconds=20)) as session:
                await session.initialize()
                tools=await session.list_tools()
                provenance['tool_schema_hash']=digest([{'name':t.name,'schema':t.inputSchema} for t in tools.tools])
                if generic:
                    names={t.name for t in tools.tools}
                    if not set(profile['tools'])<=names:raise StopRun('TOOL_CONTRACT_MISMATCH')
                    tools.tools=[t for t in tools.tools if t.name in profile['tools']]
                store.event(uid(),'integration_checked',run['cohort'],run['subject'],id,internal=True)
                async def call(name,args):
                    await stopped()
                    if name not in {t.name for t in tools.tools}:raise StopRun('TOOL_DENIED')
                    observation=recorder.start_tool(name,args) if recorder else None
                    res=decode(await session.call_tool(name,args))
                    if len(json.dumps(res).encode())>32000:res={'error':'TOOL_RESPONSE_TOO_LARGE'}
                    if observation:recorder.end(observation,res)
                    trace.append({"tool":name,"arguments_hash":digest(args),"result_hash":digest(res),"error":res.get('error')})
                    if res.get('error'):errors.append(res['error'])
                    return res
                if run['mode']=='protocol':
                    if generic:
                        if not task.get('steps'):raise StopRun('REFERENCE_STEPS_REQUIRED')
                        for step in task['steps']:await call(step['tool'],step['arguments'])
                        return
                    await call('list_fixture_files',{})
                    data=await call('read_records',{'path':'records.json'})
                    processed=await call('normalize_filter_records',{'records':data['records'],'min_cents':task['min_cents']})
                    if not processed.get('error'):await call('write_outputs',processed)
                    return
                load_credentials()
                if not os.getenv('DEEPSEEK_API_KEY'):raise StopRun('credentials_missing')
                model=exp['model']
                if model!='deepseek-flash':raise StopRun('unpriced_model')
                price_in=exp['input_cny_per_million'];price_out=exp['output_cny_per_million']
                if price_in<2 or price_out<8:raise StopRun('prices_missing_or_under_reserved')
                tooldefs=[{'type':'function','function':{'name':t.name,'description':material['descriptions'].get(t.name,t.description),'parameters':t.inputSchema}} for t in tools.tools]
                public={'instruction':task['instruction'],'input_root':'/input','output_root':'/output'} if generic else public_task(task)
                messages=[{'role':'system','content':material['guide']}, {'role':'user','content':json.dumps(public)}]
                output_used=0
                async with httpx.AsyncClient(timeout=45,trust_env=True) as client:
                    for step in range(int(exp['max_requests'])):
                        await stopped()
                        byte_bound=len(json.dumps({'messages':messages,'tools':tooldefs},ensure_ascii=False).encode())+1024
                        if byte_bound>exp['input_bound']:raise StopRun('context_limit')
                        max_tokens=min(int(exp['max_output_tokens']),int(exp.get('max_episode_output_tokens',8192))-output_used)
                        if max_tokens<=0:raise StopRun('output_limit')
                        reserved=(exp['input_bound']*price_in+max_tokens*price_out)/1000000
                        try:charge=store.reserve(id,reserved)
                        except ValueError:raise StopRun('BUDGET_EXHAUSTED') from None
                        requests+=1;cost+=reserved
                        observation=recorder.start_generation(model,messages,tooldefs) if recorder else None
                        trace.append({'request':requests,'reserved_cny':reserved,'status':'sent'})
                        (root/'trace.json').write_text(json.dumps(trace),encoding='utf-8')
                        try:
                            response=await client.post('https://api.deepseek.com/chat/completions',headers={'Authorization':'Bearer '+os.environ['DEEPSEEK_API_KEY']},json={'model':model,'messages':messages,'tools':tooldefs,'temperature':0,'max_tokens':max_tokens,'thinking':{'type':'disabled'}})
                        except (httpx.TimeoutException,httpx.NetworkError):
                            if observation:recorder.end(observation,{'error':'network_error'})
                            if step==0:continue # one bounded retry; uncertain attempt keeps reservation
                            raise StopRun('network_error') from None
                        if response.status_code!=200:
                            if observation:recorder.end(observation,{'error':'model_http_'+str(response.status_code)})
                            raise StopRun('model_http_'+str(response.status_code))
                        data=response.json();usage=data.get('usage')
                        if not usage:raise StopRun('usage_missing')
                        if observation:recorder.end(observation,data['choices'][0]['message'],usage)
                        actual=(usage['prompt_tokens']*price_in+usage['completion_tokens']*price_out)/1000000
                        store.settle(charge,actual,usage);cost+=actual-reserved;output_used+=usage['completion_tokens']
                        provenance['model']=data.get('model');trace[-1].update(status='received',usage=usage,cost_upper_cny=actual)
                        if actual>reserved:raise StopRun('token_bound_exceeded')
                        m=data['choices'][0]['message'];calls=m.get('tool_calls') or []
                        if len(calls)>8:raise StopRun('tool_limit')
                        messages.append({k:v for k,v in m.items() if k in {'role','content','tool_calls'}})
                        if not calls:return
                        for t in calls:
                            f=t['function'];name=f['name']
                            if name not in {x.name for x in tools.tools}:res={'error':'UNKNOWN_TOOL'};errors.append('UNKNOWN_TOOL')
                            else:
                                try:args=json.loads(f['arguments'])
                                except ValueError:args=None
                                res=await call(name,args) if isinstance(args,dict) else {'error':'INVALID_ARGUMENTS'}
                            messages.append({'role':'tool','tool_call_id':t['id'],'content':json.dumps(res)})
                    raise StopRun('request_limit')
    status='failed'
    deadline=asyncio.timeout(min(EPISODE_SECONDS,exp['episode_seconds']))
    try:
        async with deadline:await workflow()
    except StopRun as e:
        code=str(e);status={'cancelled':'cancelled','request_limit':'budget_exhausted','output_limit':'budget_exhausted','BUDGET_EXHAUSTED':'budget_exhausted'}.get(code,'failed')
    except TimeoutError:code='episode_timeout';status='timed_out'
    except BaseException as e:
        # Persist safe error type, never credential-bearing exception text.
        if deadline.expired():code,status='episode_timeout','timed_out'
        else:code,status=classify_error(e)
    if generic:
        # Explicit cleanup also covers a stdio client being cancelled mid-request.
        import shutil,subprocess
        if docker_command():
            try:await asyncio.to_thread(subprocess.run,[docker_command(),'rm','-f','adoptlab-'+id],capture_output=True,timeout=10)
            except (OSError,subprocess.TimeoutExpired):pass
    try:verification=await asyncio.to_thread(verify_task,store,task,root,True) if generic else verify(task,root,errors)
    except (ValueError,OSError):
        verification={'passed':False,'kind':'verifier_error','reason':'verifier_integrity_or_execution_error'}
        code=code or 'verifier_error';status='failed'
    if verification['passed'] and code is None:status='succeeded'
    result={'verification':verification,'requests':requests,'tools':len([x for x in trace if 'tool' in x]),
            'elapsed_seconds':round(time.monotonic()-start,3),'cost_upper_cny':round(cost,8),'error_code':code,
            'provenance':provenance,'tool_errors':errors,
            'timeline':trace,'diagnosis':{'category':code or verification.get('reason'),'next_action':'Review failed contract checks and material diff; rerun explicitly after a revision.'}}
    (root/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    (root/'manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    store.finish(id,status,result)
    store.event(uid(),'task_verified' if status=='succeeded' else 'task_failed',run['cohort'],run['subject'],id,internal=True)
    return store.get_run(id)

def reverify(store,id,extensions=False):
    run=store.get_run(id)
    if not run['result']:raise ValueError('RUN_NOT_COMPLETED')
    path=store.root/'runs'/id
    manifest=json.loads((path/'manifest.json').read_text(encoding='utf-8'))
    task=store.task(run['task_id'])
    current=verify_task(store,task,path,extensions) if 'profile' in task else verify(task,path,manifest['tool_errors'])
    return {'verification':current,'manifest_matches_db':digest(manifest)==digest(run['result']),
            'task_matches':digest(task)==manifest['provenance']['task_hash'],
            'artifact_hash_matches':current.get('artifact_hash')==manifest['verification'].get('artifact_hash')}
