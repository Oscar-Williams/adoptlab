"""Use a pinned, unmodified MCPMark checkout through a narrow adapter."""
import hashlib
import os
import sys
import subprocess
import zipfile
from pathlib import Path
import httpx
from .config import RUNTIME

COMMIT='cd45b7f57923b9b3985467f5139927575f83141c'
def baseline(checkout:Path):
    actual=subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
    if actual!=COMMIT:raise ValueError('UPSTREAM_COMMIT_MISMATCH')
    sys.path.insert(0,str(checkout))
    from src.mcp_services.filesystem.filesystem_state_manager import FilesystemStateManager
    from src.mcp_services.filesystem.filesystem_task_manager import FilesystemTask,FilesystemTaskManager
    base=RUNTIME/'upstream-fixtures';base.mkdir(parents=True,exist_ok=True)
    url='https://storage.mcpmark.ai/filesystem/desktop.zip'
    archive=base/'desktop.zip'
    if not archive.exists():
        with httpx.Client(timeout=30,follow_redirects=True) as client:
            response=client.get(url);response.raise_for_status()
        if len(response.content)>10_000_000:raise ValueError('UPSTREAM_FIXTURE_TOO_LARGE')
        archive.write_bytes(response.content)
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            dest=(base/member.filename).resolve()
            if not dest.is_relative_to(base.resolve()) or member.file_size>10_000_000:raise ValueError('UNSAFE_ARCHIVE')
        z.extractall(base)
    os.environ['FILESYSTEM_TEST_ROOT']=str(base)
    taskroot=checkout/'tasks'/'filesystem'/'standard'/'desktop'/'project_management'
    task=FilesystemTask(taskroot/'description.md',taskroot/'verify.py','filesystem','desktop','project_management')
    manager=FilesystemStateManager(test_root=base/'desktop')
    if not manager.initialize() or not manager.set_up(task):raise ValueError('UPSTREAM_STATE_FAILED')
    root=Path(task.test_directory)
    if not root.resolve().is_relative_to(checkout.resolve()):raise ValueError('UNEXPECTED_BACKUP_ROOT')
    before=hashlib.sha256(archive.read_bytes()).hexdigest()
    outputs=root/'organized_projects'
    for folder in ['experiments/ml_projects','experiments/data_analysis','learning/resources','learning/progress_tracking','personal/entertainment','personal/collections']:(outputs/folder).mkdir(parents=True,exist_ok=True)
    # Deterministic reference workflow, independent of the original verifier.
    for file in list(root.rglob('*')):
        if not file.is_file() or file.is_relative_to(outputs):continue
        dest=None
        if file.suffix=='.py':dest='experiments/ml_projects'
        elif file.suffix=='.csv':dest='experiments/data_analysis'
        elif file.suffix=='.md':
            if 'music' in file.name:dest='personal/collections'
            elif any(word in file.name for word in ['gaming','entertainment','travel_bucket']):dest='personal/entertainment'
            else:dest='learning/resources'
        if dest:
            target=outputs/dest/file.name
            if target.exists():raise ValueError('UPSTREAM_FILENAME_COLLISION')
            file.rename(target)
    lines=['# Project structure','']
    for d in sorted(p for p in outputs.rglob('*') if p.is_dir()):
        lines.append(f"{d.relative_to(outputs).as_posix()}: {len([f for f in d.iterdir() if f.is_file()])} files")
    (outputs/'project_structure.md').write_text('\n'.join(lines)+'\nPython experiments, CSV analysis, learning resources, entertainment plans and music collections.',encoding='utf-8')
    verified=FilesystemTaskManager(tasks_root=checkout/'tasks',task_suite='standard').run_verification(task)
    report={'commit':actual,'fixture_sha256':before,'task':'desktop__project_management','mode':'deterministic_reference_workflow',
            'passed':verified.returncode==0,'verifier_returncode':verified.returncode,'output':verified.stdout,'error':verified.stderr,
            'boundary':'This reproduces upstream setup/isolation/verification; it is not an upstream LLM benchmark score.'}
    (RUNTIME/'upstream-baseline.json').write_text(__import__('json').dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report
