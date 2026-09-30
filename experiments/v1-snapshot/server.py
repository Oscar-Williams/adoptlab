"""Private stdio MCP process. It receives one isolated run root, never a key."""
import os
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from .contract import safe_path, normalize, ContractError
from .tasks import MATERIALS
from .config import digest

def build(root:Path, variant='A'):
    server=FastMCP('adoptlab_records_mcp')
    desc=MATERIALS[variant]['descriptions']
    def respond(fn):
        try:return fn()
        except ContractError as e:return {"error":e.code,"help":"Check input schema, integer cents, timezone and relative paths; correct invalid data before retrying."}
        except (OSError,ValueError):return {"error":"READ_ERROR","help":"Use a listed JSON fixture and valid JSON contents."}
    @server.tool(description=desc['list_fixture_files'],annotations={"readOnlyHint":True,"openWorldHint":False})
    def list_fixture_files()->dict:
        return {"files":sorted(p.name for p in (root/'fixtures').glob('*.json'))}
    @server.tool(description=desc['read_records'],annotations={"readOnlyHint":True,"openWorldHint":False})
    def read_records(path:str)->dict:
        def read():
            f=safe_path(root/'fixtures',path)
            if f.stat().st_size>1000000:raise ContractError('INPUT_TOO_LARGE')
            return {"records":json.loads(f.read_text(encoding='utf-8'))}
        return respond(read)
    @server.tool(description=desc['normalize_filter_records'],annotations={"readOnlyHint":True,"openWorldHint":False})
    def normalize_filter_records(records:list[dict[str,str]], min_cents:int)->dict:
        return respond(lambda:normalize(records,min_cents))
    @server.tool(description=desc['write_outputs'],annotations={"readOnlyHint":False,"destructiveHint":False,"idempotentHint":True,"openWorldHint":False})
    def write_outputs(result:list[dict], summary:dict)->dict:
        def write():
            obj={'result':result,'summary':summary}
            if len(json.dumps(obj))>1000000:raise ContractError('OUTPUT_TOO_LARGE')
            for name,data in obj.items():
                p=safe_path(root/'outputs',name+'.json')
                p.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True),encoding='utf-8')
            return {"written":["result.json","summary.json"],"hash":digest(obj)}
        return respond(write)
    return server

def main():
    build(Path(os.environ['ADOPTLAB_RUN_ROOT']),os.getenv('ADOPTLAB_MATERIAL','A')).run(transport='stdio')

if __name__=='__main__':main()
