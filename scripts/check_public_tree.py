"""Check filenames and content without printing matched secrets."""
import argparse
import re
import subprocess
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--staged',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    cmd=['git','diff','--cached','--name-only','--diff-filter=ACMR'] if args.staged else ['git','ls-files','--cached','--others','--exclude-standard']
    files=subprocess.check_output(cmd,cwd=root,text=True).splitlines();bad=[]
    pattern=re.compile(r'(?:sk-(?:lf-)?[A-Za-z0-9_-]{20,}|pk-lf-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)')
    for name in files:
        p=root/name
        if p.name.startswith('.env') and p.name!='.env.example' or p.suffix.lower() in {'.pdf','.docx','.db'}:
            bad.append((name,'private_file'));continue
        if args.staged:
            data=subprocess.check_output(['git','show',':'+name],cwd=root)
        elif p.is_file():data=p.read_bytes()
        else:continue
        s=data.decode('utf-8',errors='ignore')
        if pattern.search(s):bad.append((name,'credential_pattern'))
        if re.search(r'[A-Z]:[\\/](?:Agent_Related|Users)[\\/]',s) and not name.startswith('scripts/browser_check'):
            bad.append((name,'personal_absolute_path'))
    for name,reason in bad:print(reason+': '+name)
    print('Public-tree scan:',len(files),'files;',len(bad),'findings')
    raise SystemExit(bool(bad))

if __name__=='__main__':main()
