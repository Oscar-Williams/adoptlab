"""Build a pinned upstream source and register its offline container profile."""
import json
import subprocess
import tarfile
import hashlib
import argparse
from pathlib import Path
from adoptlab.config import RUNTIME
from adoptlab.store import Store

COMMIT='f46d9578190b476b3501923ea8977d899e8db2cb'
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base-registry',choices=['docker.io/library','public.ecr.aws/docker/library'],default='docker.io/library');args=parser.parse_args()
    source=RUNTIME.parent/'upstream'/('mcp-servers-'+COMMIT)
    source.parent.mkdir(parents=True,exist_ok=True)
    archive=source.parent/(COMMIT+'.tar.gz')
    if not source.exists():
        subprocess.run(['curl','--fail','--retry','2','--location','--output',str(archive),'https://codeload.github.com/modelcontextprotocol/servers/tar.gz/'+COMMIT],check=True)
        with tarfile.open(archive) as tar:tar.extractall(source.parent,filter='data')
        extracted=source.parent/('servers-'+COMMIT)
        extracted.rename(source)
    archive_hash=hashlib.sha256(archive.read_bytes()).hexdigest() if archive.exists() else None
    original=(source/'src/filesystem/Dockerfile').read_text(encoding='utf-8')
    base_pins={}
    for tag in ['22.12-alpine','22-alpine']:
        reference=args.base_registry+'/node:'+tag
        subprocess.run(['docker','pull',reference],check=True)
        pin=json.loads(subprocess.check_output(['docker','image','inspect',reference,'--format','{{json .RepoDigests}}'],text=True))[0]
        base_pins[tag]=pin
        original=original.replace('FROM node:'+tag+' AS','FROM '+pin+' AS')
    dockerfile=source.parent/(COMMIT+'.Dockerfile')
    original=original.replace('RUN --mount=type=cache,target=/root/.npm npm install','RUN npm install --ignore-scripts --legacy-peer-deps --cache /tmp/adoptlab-npm && npm run build')
    original=original.replace('npm ci --ignore-scripts --omit-dev','npm ci --ignore-scripts --omit-dev --legacy-peer-deps')
    dockerfile.write_text(original+'\nCOPY LICENSE /app/UPSTREAM_LICENSE\n',encoding='utf-8')
    subprocess.run(['docker','build','-t','adoptlab-filesystem:v1','-f',str(dockerfile),'.'],cwd=source,check=True)
    image=subprocess.check_output(['docker','image','inspect','adoptlab-filesystem:v1','--format','{{.Id}}'],text=True).strip()
    profile={'id':'filesystem-v1','image':image,'version':COMMIT,'argv':['/input','/output'],'tools':['read_text_file','write_file'],'memory_mb':256,'cpus':1,'pids':64}
    store=Store();store.register('profile',profile)
    store.register('task',json.loads((ROOT/'examples'/'filesystem-task.json').read_text(encoding='utf-8')))
    material=store.add_material('Read the supplied reference and use write_file to save the required JSON. Use /input for sources and /output for results. Preserve exact citation names.',{'read_text_file':'Read UTF-8 text from /input.','write_file':'Write a JSON string to /output/evidence.json.'},name='Filesystem guide v1',reason='Explicit input/output paths and independent field contract.')
    config={'title':'Filesystem integration','mode':'protocol','tasks':['docs-evidence-01'],'materials':[material['id']],'trials':1}
    path=store.root/'filesystem-run.json';path.write_text(json.dumps(config,indent=2),encoding='utf-8')
    evidence={'registered':True,'commit':COMMIT,'archive_sha256':archive_hash,'base_images':base_pins,'image':image,'config':str(path),'build_note':'Upstream source unchanged. Dockerfile pins bases, uses legacy-peer-deps with explicit build and retains transition license; generated dependency lock retained inside image.'}
    (store.root/'filesystem-source.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print(json.dumps(evidence))

if __name__=='__main__':main()
