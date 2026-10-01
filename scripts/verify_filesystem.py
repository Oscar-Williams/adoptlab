"""Real stdio/container contract and isolation checks; all data is synthetic."""
import asyncio
import json
import subprocess
import argparse
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from adoptlab.store import Store
from adoptlab.engine import execute,reverify
from adoptlab.packages import container_args,docker_command,prepare_container_mounts

async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reuse-run');parser.add_argument('--protocol-only',action='store_true');args=parser.parse_args()
    s=Store();profile=s.registered('profile','filesystem-v1')
    config=json.loads((s.root/'filesystem-run.json').read_text())
    if args.reuse_run:
        r=s.get_run(args.reuse_run)
        if r['task_id']!='docs-evidence-01' or r['mode']!='model':raise ValueError('INVALID_REUSE_RUN')
        exp=r['experiment_id']
    else:
        exp=s.experiment('Filesystem real model and isolation')
        r=await execute(s,s.queue(exp,'docs-evidence-01',config['materials'][0],'protocol' if args.protocol_only else 'model'))
    checks=[]
    checks.append({'check':r['mode']+'_task_contract','passed':r['status']=='succeeded','run_id':r['id']})
    checks.append({'check':'independent_reverify','passed':reverify(s,r['id'])['verification']['passed']})
    root=s.root/'filesystem-isolation';(root/'fixtures').mkdir(parents=True,exist_ok=True);(root/'outputs').mkdir(exist_ok=True)
    (root/'fixtures'/'guide.txt').write_text('Synthetic readonly fixture',encoding='utf-8')
    prepare_container_mounts(root)
    name='adoptlab-isolation-check'
    try:
        async with asyncio.timeout(40):
            async with stdio_client(StdioServerParameters(command=docker_command(),args=container_args(profile,root,name),env={})) as streams:
                async with ClientSession(*streams,read_timeout_seconds=timedelta(seconds=10)) as session:
                    await session.initialize()
                    for title,tool,args in [
                        ('outside_allowlist_read','read_text_file',{'path':'/etc/passwd'}),
                        ('input_mount_readonly','write_file',{'path':'/input/guide.txt','content':'overwrite'}),
                        ('path_traversal','read_text_file',{'path':'/input/../etc/passwd'})]:
                        result=await session.call_tool(tool,args);checks.append({'check':title,'passed':result.isError})
                    inspection=json.loads(subprocess.check_output([docker_command(),'inspect',name],text=True))[0]
                    host=inspection['HostConfig'];container=inspection['Config']
                    checks.extend([
                        {'check':'network_disabled','passed':host['NetworkMode']=='none'},
                        {'check':'root_readonly','passed':host['ReadonlyRootfs']},
                        {'check':'nonroot','passed':container['User']=='65534:65534'},
                        {'check':'capabilities_dropped','passed':'ALL' in host['CapDrop']},
                        {'check':'mount_allowlist','passed':{m['Destination'] for m in inspection['Mounts']}=={'/input','/output'} and set(host['Tmpfs'])=={'/tmp'}},
                        {'check':'credentials_not_in_container','passed':not any(x.startswith(('DEEPSEEK_','LANGFUSE_')) for x in container['Env'])}])
    finally:subprocess.run([docker_command(),'rm','-f',name],capture_output=True,timeout=10)
    out={'checks':checks,'passed':all(x['passed'] for x in checks),'experiment_id':exp,'cohort':'automation','human_participants':0}
    (s.root/'filesystem-validation.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out))
    if not out['passed']:raise SystemExit(1)

if __name__=='__main__':asyncio.run(main())
