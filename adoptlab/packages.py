"""Locally registered, immutable task contracts and container profiles."""
import json
import re
import shutil
import subprocess
from pathlib import Path
from .config import digest

ID = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')

def safe_path(root, relative):
    if not isinstance(relative, str) or '\\' in relative or ':' in relative:
        raise ValueError('UNSAFE_PATH')
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise ValueError('UNSAFE_PATH')
    target = (root / p).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('PATH_ESCAPE')
    return target

def validate_task(data):
    allowed = {'id','family','split','profile','instruction','fixtures','rules','steps','expected_error','verifier'}
    if set(data)-allowed or not ID.fullmatch(data.get('id','')):
        raise ValueError('INVALID_TASK_PACKAGE')
    if data.get('split') not in {'exploration','holdout'} or not ID.fullmatch(data.get('profile','')):
        raise ValueError('INVALID_TASK_PACKAGE')
    if not data.get('instruction') or not data.get('family') or not data.get('rules'):
        raise ValueError('TASK_CONTRACT_REQUIRED')
    if len(json.dumps(data)) > 16000:
        raise ValueError('TASK_TOO_LARGE')
    for name, value in data.get('fixtures',{}).items():
        safe_path(Path('.'),name)
        if not isinstance(value,str):raise ValueError('FIXTURE_TEXT_REQUIRED')
    for rule in data['rules']:
        if set(rule)-{'file','op','path','expected','min','max','type'}:raise ValueError('UNKNOWN_RULE_FIELD')
        if rule.get('op') not in {'exists','equals','contains','set_equals','range','type'}:raise ValueError('UNKNOWN_RULE')
        safe_path(Path('.'),rule['file'])
        if not isinstance(rule.get('path',[]),list):raise ValueError('INVALID_RULE_PATH')
        if rule['op']=='range' and not any(k in rule for k in ('min','max')):raise ValueError('RANGE_BOUND_REQUIRED')
    for step in data.get('steps',[]):
        if set(step) != {'tool','arguments'} or not ID.fullmatch(step['tool']) or not isinstance(step['arguments'],dict):raise ValueError('INVALID_REFERENCE_STEP')
    return data

def validate_profile(data):
    if set(data)-{'id','image','version','argv','tools','memory_mb','cpus','pids'}:raise ValueError('UNKNOWN_PROFILE_FIELD')
    if not ID.fullmatch(data.get('id','')):raise ValueError('INVALID_PROFILE_ID')
    # Local image content IDs are immutable too; mutable tags cannot be registered.
    if not re.fullmatch(r'(?:[A-Za-z0-9./:_-]+@)?sha256:[a-f0-9]{64}',data.get('image','')):raise ValueError('PINNED_IMAGE_REQUIRED')
    if not data.get('version') or not isinstance(data.get('argv'),list) or not data['argv'] or any(not isinstance(x,str) for x in data['argv']):raise ValueError('INVALID_PROFILE_COMMAND')
    if not data.get('tools') or any(not ID.fullmatch(x) for x in data['tools']):raise ValueError('TOOL_ALLOWLIST_REQUIRED')
    for key,default,low,high in [('memory_mb',256,64,2048),('cpus',1,.1,2),('pids',64,8,128)]:
        if not low<=data.get(key,default)<=high:raise ValueError('INVALID_RESOURCE_LIMIT')
    return data

def docker_command():
    import os
    from .config import load_credentials
    load_credentials()
    return os.getenv('ADOPTLAB_DOCKER') or shutil.which('docker')

def pinned_image_ready(profile):
    command=docker_command()
    if not command:return False
    try:
        result=subprocess.run([command,'image','inspect',profile['image']],capture_output=True,timeout=10)
        return result.returncode==0
    except (OSError,subprocess.TimeoutExpired):return False

def readiness():
    command=docker_command()
    if not command:return {'ready':False,'reason':'DOCKER_NOT_INSTALLED'}
    try:
        r=subprocess.run([command,'info','--format','{{.OSType}}'],capture_output=True,text=True,timeout=10)
        return {'ready':r.returncode==0 and r.stdout.strip()=='linux','reason':'READY' if r.returncode==0 and r.stdout.strip()=='linux' else 'LINUX_DOCKER_NOT_READY'}
    except (OSError,subprocess.TimeoutExpired):return {'ready':False,'reason':'DOCKER_CHECK_FAILED'}

def container_args(profile,root,name):
    validate_profile(profile)
    return ['run','--rm','-i','--pull=never','--name',name,'--network=none','--read-only',
            '--cap-drop=ALL','--security-opt=no-new-privileges','--user=65534:65534',
            '--memory='+str(profile.get('memory_mb',256))+'m','--cpus='+str(profile.get('cpus',1)),
            '--pids-limit='+str(profile.get('pids',64)), '--tmpfs=/tmp:rw,noexec,nosuid,size=16m',
            '--mount',f'type=bind,src={(root/"fixtures").resolve()},dst=/input,readonly',
            '--mount',f'type=bind,src={(root/"outputs").resolve()},dst=/output',
            profile['image'],*profile['argv']]

def prepare_container_mounts(root):
    """Keep the host run private while allowing UID 65534 in its output bind."""
    import os
    if os.name!='posix':return
    # The private ancestor blocks other host users; sticky output permits only
    # the isolated container to create artifacts without root/chown privileges.
    root.chmod(0o700)
    (root/'outputs').chmod(0o1777)
    (root/'fixtures').chmod(0o755)
    for path in (root/'fixtures').rglob('*'):
        if path.is_symlink():raise ValueError('FIXTURE_LINK_DENIED')
        path.chmod(0o755 if path.is_dir() else 0o444)

def verify_rules(task,root):
    checks=[];artifacts={}
    for rule in task['rules']:
        label=rule['file']+':'+'.'.join(map(str,rule.get('path',[])))+':'+rule['op'];passed=False
        try:
            target=safe_path(root/'outputs',rule['file'])
            if target.stat().st_size>1000000:raise ValueError('ARTIFACT_TOO_LARGE')
            text=target.read_text(encoding='utf-8');artifacts[rule['file']]=digest(text)
            if rule['op']=='exists':passed=True
            else:
                value=json.loads(text) if rule.get('path') or rule['file'].endswith('.json') else text
                for segment in rule.get('path',[]):value=value[segment]
                op=rule['op'];expected=rule.get('expected')
                if op=='equals':passed=value==expected
                elif op=='contains':passed=expected in value
                elif op=='set_equals':passed=sorted(map(digest,value))==sorted(map(digest,expected))
                elif op=='range':passed=isinstance(value,(int,float)) and not isinstance(value,bool) and rule.get('min',float('-inf'))<=value<=rule.get('max',float('inf'))
                elif op=='type':passed=type(value).__name__==rule['type']
        except (OSError,ValueError,KeyError,IndexError,TypeError):pass
        checks.append({'rule':label,'passed':passed})
    return {'passed':all(x['passed'] for x in checks),'kind':'rules','reason':'contract_passed' if all(x['passed'] for x in checks) else 'rule_failed','checks':checks,'artifact_hash':digest(artifacts)}

def verify_task(store,task,root,extensions=False):
    result=verify_rules(task,root)
    if task.get('verifier'):
        if not extensions:raise ValueError('TRUSTED_VERIFIER_REQUIRES_EXPLICIT_POST_OR_CLI')
        import os,sys
        meta=store.verifier(task['verifier'])
        script=store.root/'verifiers'/(task['verifier']+'.py')
        if digest(script.read_text(encoding='utf-8'))!=meta['hash']:raise ValueError('VERIFIER_CONTENT_CHANGED')
        env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','TEMP','TMP'}}
        try:
            p=subprocess.run([sys.executable,'-I',str(script),str((root/'outputs').resolve())],env=env,capture_output=True,timeout=10)
            value=json.loads(p.stdout) if len(p.stdout)<10000 else None
            passed=p.returncode==0 and isinstance(value,dict) and value.get('passed') is True
        except (OSError,subprocess.TimeoutExpired,ValueError):passed=False
        result['checks'].append({'rule':'trusted_extension:'+task['verifier'],'passed':passed})
        result['passed']=result['passed'] and passed
        result['reason']='contract_passed' if result['passed'] else 'rule_failed'
        result['extension_hash']=meta['hash']
    return result
