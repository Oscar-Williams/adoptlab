"""Check filenames and content without printing matched secrets."""
import argparse
import re
import subprocess
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--staged',action='store_true');parser.add_argument('--history',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    cmd=['git','diff','--cached','--name-only','--diff-filter=ACMR'] if args.staged else ['git','ls-files','--cached','--others','--exclude-standard']
    files=subprocess.check_output(cmd,cwd=root,text=True).splitlines();bad=[]
    from dotenv import dotenv_values
    from adoptlab.config import RUNTIME
    secrets=[]
    for env_path in [RUNTIME.parent/'private'/'.env',root/'.env']:
        secrets.extend(v.encode() for k,v in dotenv_values(env_path).items()
                       if any(part in k.upper() for part in ['KEY','SECRET','TOKEN','PASSWORD']) and v and len(v)>=8)
    pattern=re.compile(r'(?:sk-(?:lf-)?[A-Za-z0-9_-]{20,}|pk-lf-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
    for name in files:
        p=root/name
        if p.name.startswith('.env') and p.name!='.env.example' or p.suffix.lower() in {'.pdf','.docx','.db','.sqlite','.sqlite3','.p12','.pfx'}:
            bad.append((name,'private_file'));continue
        if args.staged:
            data=subprocess.check_output(['git','show',':'+name],cwd=root)
        elif p.is_file():data=p.read_bytes()
        else:continue
        s=data.decode('utf-8',errors='ignore')
        if pattern.search(s):bad.append((name,'credential_pattern'))
        if any(secret in data for secret in secrets):bad.append((name,'private_credential_value'))
        if re.search(r'[A-Z]:[\\/](?:Agent_Related|Users)[\\/]',s):
            bad.append((name,'personal_absolute_path'))
    if args.history:
        objects=subprocess.check_output(['git','rev-list','--objects','--all'],cwd=root,text=True).splitlines()
        checked=0
        process=subprocess.Popen(['git','cat-file','--batch'],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        for entry in objects:
            oid,_,name=entry.partition(' ')
            process.stdin.write((oid+'\n').encode());process.stdin.flush()
            header=process.stdout.readline().decode().split()
            if len(header)!=3:raise RuntimeError('GIT_OBJECT_READ_FAILED')
            data=process.stdout.read(int(header[2]));process.stdout.read(1)
            if header[1]!='blob':continue
            checked+=1
            if pattern.search(data.decode('utf-8',errors='ignore')) or any(secret in data for secret in secrets):
                bad.append((oid[:12]+' '+name,'historical_credential'))
        process.stdin.close();process.stdout.close()
        if process.wait()!=0:raise RuntimeError('GIT_OBJECT_SCAN_FAILED')
        print('History credential scan:',checked,'unique blobs')
    for name,reason in bad:print(reason+': '+name)
    print('Public-tree scan:',len(files),'files;',len(bad),'findings')
    raise SystemExit(bool(bad))

if __name__=='__main__':main()
