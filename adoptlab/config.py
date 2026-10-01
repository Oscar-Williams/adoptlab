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

def doctor():
    load_credentials()
    import sys
    import importlib.metadata
    from .packages import readiness
    return {"python": sys.version.split()[0], "isolated": sys.prefix != sys.base_prefix or (Path(sys.prefix)/"conda-meta").exists(),
            "external_mcp":readiness(),
            "dependencies": {p: importlib.metadata.version(p) for p in ["mcp", "fastapi", "httpx"]},
            "deepseek_configured": bool(os.getenv("DEEPSEEK_API_KEY")),
            "prices_configured": all(os.getenv(k) for k in ["ADOPTLAB_INPUT_PRICE_CNY", "ADOPTLAB_OUTPUT_PRICE_CNY"]),
            "langfuse_configured": all(os.getenv(k) for k in ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]),
            "gpu_required": False, "runtime": str(RUNTIME)}
