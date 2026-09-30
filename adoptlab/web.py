import asyncio
import json
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
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

app=FastAPI(title='AdoptLab',version='0.1.0',lifespan=lifespan)
app.mount('/static',StaticFiles(directory=CODE/'adoptlab'/'static'),name='static')
templates=Jinja2Templates(directory=CODE/'adoptlab'/'templates')
@app.middleware('http')
async def boundary(request,call_next):
    host=request.headers.get('host','')
    if host.split(':')[0] not in {'127.0.0.1','localhost','testserver'}:return JSONResponse({'error':'HOST_DENIED'},status_code=403)
    if request.method in {'POST','PUT','PATCH','DELETE'}:
        origin=request.headers.get('origin')
        if origin and origin!='http://'+host:return JSONResponse({'error':'ORIGIN_DENIED'},status_code=403)
        if request.headers.get('content-type','').split(';')[0]!='application/json':return JSONResponse({'error':'JSON_REQUIRED'},status_code=415)
        if int(request.headers.get('content-length','0'))>20000:return JSONResponse({'error':'BODY_TOO_LARGE'},status_code=413)
        body=await request.body()
        if len(body)>20000:return JSONResponse({'error':'BODY_TOO_LARGE'},status_code=413)
    response=await call_next(request)
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'"
    response.headers['X-Content-Type-Options']='nosniff'
    return response
@app.exception_handler(KeyError)
async def missing(request,e):return JSONResponse({'error':'NOT_FOUND'},status_code=404)
@app.exception_handler(ValueError)
async def invalid(request,e):return JSONResponse({'error':'INVALID_REQUEST'},status_code=400)
@app.exception_handler(RequestValidationError)
async def schema_error(request,e):
    return JSONResponse({'error':'SCHEMA_ERROR','fields':[{'location':list(x['loc']),'type':x['type']} for x in e.errors()]},status_code=422)

class Strict(BaseModel):model_config=ConfigDict(extra='forbid')
class ExperimentInput(Strict):title:str=Field(min_length=1,max_length=100)
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
@app.get('/',response_class=HTMLResponse)
async def home(request:Request,lang:Literal['en','zh']='en',view:Literal['maintainer','developer']='maintainer'):
    return templates.TemplateResponse(request=request,name='index.html',context={'lang':lang,'view':view,'experiments':store.experiments(),'tasks':catalog(),'materials':{m['id']:m['content'] for m in store.materials()}})
@app.post('/api/experiments')
async def experiment(data:ExperimentInput):return {'id':store.experiment(data.title)}
@app.get('/api/experiments')
async def experiments():return store.experiments()
@app.get('/api/tasks')
async def tasks():return [{'id':t['id'],'family':t['family'],'split':t['split']} for t in catalog().values()]
@app.get('/api/materials')
async def materials():return store.materials()
@app.post('/api/materials')
async def material(data:MaterialInput):return store.add_material(data.guide,data.descriptions)
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
@app.post('/api/runs/{id}/cancel')
async def cancel(id):store.cancel(id);return {'cancel_requested':True}
@app.get('/api/runs/{id}/verification')
async def verification(id):return reverify(store,id)
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
