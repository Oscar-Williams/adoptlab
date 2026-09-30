"""Read back exported synthetic observations using the official CLI."""
import json
import os
import subprocess
import shutil
from pathlib import Path
from adoptlab.config import RUNTIME,load_credentials
from adoptlab.tracing import scrub

def main():
    load_credentials();env=os.environ.copy()
    env['LANGFUSE_HOST']=env['LANGFUSE_BASE_URL']
    env['npm_config_cache']=str(RUNTIME.parent/'cache'/'npm')
    trace=json.loads((RUNTIME/'last-langfuse-trace.json').read_text(encoding='utf-8'))
    npx=shutil.which('npx.cmd') or shutil.which('npx')
    if not npx:raise SystemExit('npx is required for official Langfuse CLI readback.')
    args=[npx,'--yes','langfuse-cli','api','observations','list','--trace-id',trace['trace_id'],'--limit','50','--fields','core,basic,io,metadata,model,usage,trace_context','--json']
    r=subprocess.run(args,env=env,capture_output=True,text=True,encoding='utf-8',timeout=60)
    if r.returncode:
        print(json.dumps({'status':'readback_failed','error':scrub(r.stderr)[-400:]}));return
    try:data=json.loads(r.stdout)
    except ValueError:
        print(json.dumps({'status':'unexpected_cli_response'}));return
    # Original readback stays private; no credential data is printed.
    (RUNTIME/'langfuse-readback.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    raw=json.dumps(data)
    keys=[os.getenv(k,'') for k in ['DEEPSEEK_API_KEY','LANGFUSE_SECRET_KEY']]
    leaked=any(v and v in raw for v in keys)
    personal_path=any(s in raw for s in ['F:\\\\Agent_Related','C:\\\\Users','F:/Agent_Related','/home/Oscar'])
    envelope=data.get('body',data)
    items=envelope.get('data',[])
    if isinstance(items,dict):items=items.get('data',[])
    public_scope_count=sum(x.get('metadata',{}).get('scope',{}).get('attributes',{}).get('public_key')==os.getenv('LANGFUSE_PUBLIC_KEY') for x in items)
    summary={'status':'audited' if items else 'awaiting_ingestion','observations':len(items),'types':{},'secret_keys_detected':leaked,'personal_paths_detected':personal_path,
             'sdk_public_routing_identifier_count':public_scope_count,'public_identifier_interpretation':'SDK scope metadata includes the project public identifier; this field stays in private readback and is excluded from public reports.',
             'trace_id':trace['trace_id'],'trace_url':trace['url'],'generation_usage_present':False,'tool_io_present':False}
    for x in items:
        kind=x.get('type','unknown');summary['types'][kind]=summary['types'].get(kind,0)+1
        if kind=='GENERATION' and x.get('usageDetails'):summary['generation_usage_present']=True
        if kind=='TOOL' and x.get('input') is not None and x.get('output') is not None:summary['tool_io_present']=True
    (RUNTIME/'langfuse-audit.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary))

if __name__=='__main__':main()
