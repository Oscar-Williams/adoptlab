import asyncio
import json
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.responses import Response
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field
from .config import CODE
from .store import Store, uid
from .tasks import catalog, MATERIALS
from .engine import execute, reverify

store=Store();workers=set()
@asynccontextmanager
async def lifespan(app):
    # A CLI experiment can run concurrently with the server. Never reset its state.
    # Interrupted runs require operator reconciliation; paid requests are not replayed.
    yield
    for worker in list(workers):worker.cancel()
    if workers:await asyncio.gather(*workers,return_exceptions=True)

app=FastAPI(title='AdoptLab',version='0.4.0',lifespan=lifespan)
app.mount('/static',StaticFiles(directory=CODE/'adoptlab'/'static'),name='static')
templates=Jinja2Templates(directory=CODE/'adoptlab'/'templates')
@app.get('/favicon.ico',include_in_schema=False)
async def favicon():return Response(status_code=204)
@app.middleware('http')
async def boundary(request,call_next):
    host=request.headers.get('host','')
    if host.split(':')[0] not in {'127.0.0.1','localhost','testserver'}:return JSONResponse({'error':'HOST_DENIED'},status_code=403)
    if request.method in {'POST','PUT','PATCH','DELETE'}:
        origin=request.headers.get('origin')
        if origin and origin!='http://'+host:return JSONResponse({'error':'ORIGIN_DENIED'},status_code=403)
        if request.headers.get('content-type','').split(';')[0]!='application/json':return JSONResponse({'error':'JSON_REQUIRED'},status_code=415)
        try:size=int(request.headers.get('content-length','0'))
        except ValueError:return JSONResponse({'error':'INVALID_CONTENT_LENGTH'},status_code=400)
        if size<0:return JSONResponse({'error':'INVALID_CONTENT_LENGTH'},status_code=400)
        if size>20000:return JSONResponse({'error':'BODY_TOO_LARGE'},status_code=413)
        body=await request.body()
        if len(body)>20000:return JSONResponse({'error':'BODY_TOO_LARGE'},status_code=413)
    response=await call_next(request)
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control']='no-store'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'"
    response.headers['X-Content-Type-Options']='nosniff'
    return response
@app.exception_handler(KeyError)
async def missing(request,e):return JSONResponse({'error':'NOT_FOUND'},status_code=404)
@app.exception_handler(ValueError)
async def invalid(request,e):
    import re
    code=str(e)
    return JSONResponse({'error':code if re.fullmatch(r'[A-Z_]{3,80}',code) else 'INVALID_REQUEST'},status_code=400)
@app.exception_handler(RequestValidationError)
async def schema_error(request,e):
    return JSONResponse({'error':'SCHEMA_ERROR','fields':[{'location':list(x['loc']),'type':x['type']} for x in e.errors()]},status_code=422)

class Strict(BaseModel):model_config=ConfigDict(extra='forbid')
class ExperimentInput(Strict):
    title:str=Field(min_length=1,max_length=100)
    settings:dict[str,int|float]|None=None
class RunInput(Strict):
    task_id:str
    material:str=Field(default='A',max_length=64,pattern=r'^[A-Za-z0-9_-]+$')
    mode:Literal['protocol','model']='protocol'
    subject:str=Field(default='local-browser',max_length=64,pattern=r'^[a-zA-Z0-9_-]+$')
class EventInput(Strict):
    event_id:str=Field(min_length=1,max_length=64,pattern=r'^[a-zA-Z0-9_-]+$')
    name:Literal['entry_viewed','setup_started']
    subject:str=Field(min_length=1,max_length=64,pattern=r'^[a-zA-Z0-9_-]+$')
    source:str=Field(default='unknown',max_length=40,pattern=r'^[a-zA-Z0-9_-]+$')
    campaign:str=Field(default='none',max_length=40,pattern=r'^[a-zA-Z0-9_-]+$')
class FeedbackInput(Strict):
    experiment_id:str
    run_id:str
    text:str=Field(min_length=1,max_length=2000)
class RevisionInput(Strict):
    feedback_id:str
    new_run:str
    decision:str=Field(min_length=1,max_length=2000)
class WithdrawInput(Strict):subject:str=Field(min_length=1,max_length=64,pattern=r'^[a-zA-Z0-9_-]+$')
class MaterialInput(Strict):
    guide:str=Field(min_length=1,max_length=6000)
    descriptions:dict[str,str]
    name:str=Field(default='',max_length=100)
    parent:str|None=None
    reason:str=Field(default='',max_length=1000)
class BatchInput(Strict):
    tasks:list[str]=Field(min_length=1,max_length=16)
    materials:list[str]=Field(min_length=1,max_length=4)
    mode:Literal['protocol','model']='protocol'
    trials:int=Field(default=1,ge=1,le=3)
@app.get('/',response_class=HTMLResponse)
async def home(request:Request,lang:Literal['en','zh']='zh',view:Literal['maintainer','developer']='maintainer'):
    if 'view' not in request.query_params:return templates.TemplateResponse(request=request,name='workspace.html',context={'lang':lang})
    return templates.TemplateResponse(request=request,name='developer.html' if view=='developer' else 'index.html',context={'lang':lang,'view':view,'experiments':store.experiments(),'tasks':store.tasks(),'materials':{m['id']:m['content'] for m in store.materials()},'material_names':{m['id']:m['metadata']['name'] for m in store.materials()}})
@app.post('/api/experiments')
async def experiment(data:ExperimentInput):return {'id':store.experiment(data.title,data.settings)}
@app.get('/api/experiments')
async def experiments():return store.experiments()
@app.get('/api/tasks')
async def tasks():return [{'id':t['id'],'family':t['family'],'split':t['split'],'profile':t.get('profile','builtin')} for t in store.tasks().values()]
@app.get('/api/tasks/{id}')
async def task_context(id):
    task=store.task(id)
    if 'profile' in task:return {'id':id,'instruction':task['instruction'],'input_root':'/input','output_root':'/output','profile':task['profile']}
    from .tasks import public_task
    return public_task(task)
@app.get('/api/materials')
async def materials():return store.materials()
@app.post('/api/materials')
async def material(data:MaterialInput):return store.add_material(data.guide,data.descriptions,data.name,data.parent,data.reason)
@app.get('/api/doctor')
async def check_environment(target:Literal['builtin','filesystem','model']='builtin'):
    from .config import doctor
    return await asyncio.to_thread(doctor,target,store.root)
@app.get('/api/profiles')
async def profiles():return store.registered('profile')
@app.get('/api/materials/{id}/diff')
async def material_diff(id):return store.material_diff(id)
@app.get('/api/runs')
async def history(experiment_id:str|None=None,status:str|None=None):
    return [{k:v for k,v in r.items() if k!='subject'} for r in store.runs(experiment_id) if not status or r['status']==status]
@app.get('/api/experiments/{id}/handoff')
async def handoff(id):return store.handoff(id)
@app.post('/api/experiments/{id}/batch',status_code=202)
async def batch(id:str,data:BatchInput):
    store.get_experiment(id)
    if len(set(data.tasks))!=len(data.tasks) or len(set(data.materials))!=len(data.materials):raise ValueError('DUPLICATE_BATCH_ITEM')
    for tid in data.tasks:
        task=store.task(tid)
        for mid in data.materials:
            material=store.material(mid)
            tools=set(store.registered('profile',task['profile'])['tools']) if 'profile' in task else set(MATERIALS['A']['descriptions'])
            if set(material['content']['descriptions'])!=tools:raise ValueError('MATERIAL_TOOL_MISMATCH')
    ids=[]
    for trial in range(1,data.trials+1):
        for ti,tid in enumerate(data.tasks):
            for mid in data.materials if (ti+trial)%2 else list(reversed(data.materials)):
                run=store.queue(id,tid,mid,data.mode,trial=trial);ids.append(run)
    async def run_batch():
        for run in ids:await background(run)
    worker=asyncio.create_task(run_batch());workers.add(worker);worker.add_done_callback(workers.discard)
    return {'run_ids':ids,'cohort':'automation','notice':'Automated batch; independent observed use is counted separately.'}
@app.post('/api/tasks/import')
async def import_task(data:dict):
    from .workbench import preflight
    checked=preflight(data,store)
    if not checked['valid']:return JSONResponse(checked,status_code=400)
    return store.register('task',data)
@app.get('/api/runs/{id}/problem-package')
async def problem_package(id):
    r=store.get_run(id)
    report=store.export(r['experiment_id'])
    return JSONResponse({'schema':'adoptlab-problem-v2','run':next(x for x in report['runs'] if x['id']==id),'config':report['config'],'notice':'Task and material hashes identify locally retained inputs. No private fixtures or raw conversations exported.'},headers={'Content-Disposition':'attachment; filename=adoptlab-problem.json'})
async def background(id):
    while store.get_run(id)['status']=='queued':
        result=await execute(store,id)
        if result['status']!='queued':return
        await asyncio.sleep(.25)
@app.post('/api/experiments/{id}/runs',status_code=202)
async def queue(id:str,data:RunInput):
    run=store.queue(id,data.task_id,data.material,data.mode,'human_unverified',data.subject)
    task=asyncio.create_task(background(run));workers.add(task);task.add_done_callback(workers.discard)
    return {'id':run,'cohort':'human_unverified','notice':'Local browser execution; independent human adoption requires an observed session or local integration evidence.'}
@app.get('/api/runs/{id}')
async def getrun(id):return {k:v for k,v in store.get_run(id).items() if k!='subject'}
def require_artifacts(id):
    store.get_run(id)
    if not (store.root/'runs'/id/'manifest.json').is_file():raise ValueError('ARTIFACTS_UNAVAILABLE')
@app.post('/api/runs/{id}/cancel')
async def cancel(id):store.cancel(id);return {'cancel_requested':True}
@app.get('/api/runs/{id}/verification')
async def verification(id):
    require_artifacts(id)
    return reverify(store,id)
@app.post('/api/runs/{id}/verification')
async def explicit_verification(id):
    require_artifacts(id)
    return await asyncio.to_thread(reverify,store,id,True)
@app.get('/api/experiments/{id}/comparison')
async def compare(id):store.get_experiment(id);return store.comparison(id)
@app.get('/api/experiments/{id}/export')
async def export(id):return JSONResponse(store.export(id),headers={'Content-Disposition':'attachment; filename=adoptlab-report.json'})
@app.post('/api/events')
async def event(data:EventInput):return {'inserted':store.event(data.event_id,data.name,'human_unverified',data.subject,source=data.source,campaign=data.campaign)}
@app.post('/api/feedback')
async def feedback(data:FeedbackInput):return {'id':store.feedback(data.experiment_id,data.run_id,data.text)}
@app.post('/api/revisions')
async def revision(data:RevisionInput):return {'id':store.revision(data.feedback_id,data.new_run,data.decision)}
@app.post('/api/withdraw')
async def withdraw(data:WithdrawInput):store.withdraw(data.subject);return {'withdrawn':True}
@app.get('/api/budget')
async def budget():return store.cost()
@app.get('/api/funnel')
async def funnel():
    return store.funnel()

from .workbench import router as workbench_router
app.include_router(workbench_router)

@app.get("/workspace",response_class=HTMLResponse)
async def workspace(request:Request,lang:Literal["zh","en"]="zh"):
    return templates.TemplateResponse(request=request,name="workspace.html",context={"lang":lang})

app.mount("/showcase",StaticFiles(directory=CODE/"public-site",html=True),name="showcase")
