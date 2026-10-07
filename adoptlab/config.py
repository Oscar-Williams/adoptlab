import hashlib
import json
import os
from pathlib import Path
from dotenv import load_dotenv

CODE = Path(__file__).resolve().parents[1]
_workspace = CODE.parents[1] / 'runtime' / 'adoptlab'
_default = _workspace if (CODE.parent.name=='implementation') else Path.home()/'.local'/'share'/'adoptlab'
RUNTIME = Path(os.getenv("ADOPTLAB_RUNTIME", str(_default))).resolve()
def load_credentials():
    load_dotenv(RUNTIME.parent / "private" / ".env", override=False)
    load_dotenv(CODE / ".env", override=False)

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def doctor(target=None, runtime=RUNTIME):
    load_credentials()
    import sys
    import importlib.metadata
    from .packages import readiness
    if target is not None:
        if target not in {'builtin','filesystem','model'}:raise ValueError('UNKNOWN_DOCTOR_TARGET')
        import tempfile
        versions={}
        for package in ['mcp','fastapi','httpx','jinja2','uvicorn','python-dotenv']:
            try:versions[package]=importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:versions[package]=None
        try:
            runtime.mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryFile(dir=runtime) as probe:probe.write(b'readiness')
            writable=True
        except OSError:writable=False
        checks=[{'id':'python','required':True,'passed':sys.version_info>=(3,11),'action':'Use Python 3.11 or newer.'},
                {'id':'dependencies','required':True,'passed':all(versions.values()),'action':'Run python -m pip install -e . in the project environment.'},
                {'id':'runtime','required':True,'passed':writable,'action':'Set ADOPTLAB_RUNTIME to a writable directory on your data drive, then restart AdoptLab.'},
                {'id':'isolated_environment','required':False,'passed':sys.prefix!=sys.base_prefix or (Path(sys.prefix)/'conda-meta').exists(),'action':'Use a separate Conda or venv environment for AdoptLab.'}]
        if target=='filesystem':
            checks.append({'id':'docker','required':True,'passed':readiness()['ready'],'action':'Start Linux Docker, then register the pinned Filesystem profile and task using the task-package tutorial.'})
            import sqlite3
            profiles=[];registered=False
            if (runtime/'adoptlab.db').exists():
                try:
                    with sqlite3.connect((runtime/'adoptlab.db').as_uri()+'?mode=ro',uri=True) as c:
                        profiles=[json.loads(r[0]) for r in c.execute("SELECT content FROM registry WHERE kind='profile'") if {'read_text_file','write_file'}.issubset(json.loads(r[0]).get('tools',[]))]
                        task_profiles={json.loads(r[0]).get('profile') for r in c.execute("SELECT content FROM registry WHERE kind='task'")}
                        profiles=[p for p in profiles if p['id'] in task_profiles]
                        registered=bool(profiles)
                except sqlite3.Error:pass
            checks.append({'id':'filesystem_registration','required':True,'passed':registered,'action':'Register a pinned Filesystem profile and its matching task. Use new IDs when rebuilding an existing profile.'})
            from .packages import pinned_image_ready
            checks.append({'id':'pinned_image','required':True,'passed':any(pinned_image_ready(p) for p in profiles),'action':'Prepare the pinned image locally; if rebuilding changes its digest, register a new profile and task version.'})
        if target=='model':
            checks.extend([{'id':'model_key','required':True,'passed':bool(os.getenv('DEEPSEEK_API_KEY')),'action':'Configure DEEPSEEK_API_KEY in your private local .env.'},
                           {'id':'model_support','required':True,'passed':os.getenv('DEEPSEEK_MODEL','deepseek-flash')=='deepseek-flash','action':'Use the supported deepseek-flash model and verify frozen experiment pricing.'}])
        return {'target':target,'ready':all(c['passed'] for c in checks if c['required']),'python':sys.version.split()[0],
                'checks':checks,'dependencies':versions,'gpu_required':False,
                'optional_capabilities':{'docker':'Required for external container tasks.','model':'Private credentials required for paid inference.','langfuse':'Optional tracing; first-task runs locally without cloud submission.'}}
    return {"python": sys.version.split()[0], "isolated": sys.prefix != sys.base_prefix or (Path(sys.prefix)/"conda-meta").exists(),
            "external_mcp":readiness(),
            "dependencies": {p: importlib.metadata.version(p) for p in ["mcp", "fastapi", "httpx"]},
            "deepseek_configured": bool(os.getenv("DEEPSEEK_API_KEY")),
            "prices_configured": all(os.getenv(k) for k in ["ADOPTLAB_INPUT_PRICE_CNY", "ADOPTLAB_OUTPUT_PRICE_CNY"]),
            "langfuse_configured": all(os.getenv(k) for k in ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]),
            "gpu_required": False, "runtime": str(RUNTIME)}
