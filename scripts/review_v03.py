"""Eight role walkthroughs and a unified observation-to-retest ledger."""
import asyncio
import csv
import json
import os
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from adoptlab.config import RUNTIME
from adoptlab.store import Store
from adoptlab.engine import execute,reverify

ROLES=[('M1','AI API maintainer','maintainer','en',1440),('M2','MCP maintainer','maintainer','zh',1440),('M3','Documentation owner','maintainer','en',1440),('D1','New Python developer','developer','en',1440),('D2','Experienced MCP developer','developer','en',1440),('D3','Windows developer','developer','zh',1440),('D4','Container developer','developer','zh',1440),('D5','English documentation reader','developer','en',390)]

def main():
    url=os.getenv('ADOPTLAB_BROWSER_URL','http://127.0.0.1:8783');out=RUNTIME/'output'/'v03-review';out.mkdir(parents=True,exist_ok=True)
    s=Store();observations=[];errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge')
        for code,role,view,lang,width in ROLES:
            context=browser.new_context(viewport={'width':width,'height':900});page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
            started=time.monotonic();page.goto(f'{url}/?lang={lang}&view={view}&source=review_v03&campaign={code}')
            subject=page.evaluate("localStorage.getItem('adoptlab-subject')");checks=[];new_run=None
            if view=='developer':
                expect(page.locator('#first-readiness')).to_contain_text('已就绪' if lang=='zh' else 'Ready',timeout=20000)
                assert page.locator('#create').count()==0
                page.locator('#first-run').click();expect(page.locator('#first-status')).to_have_text('succeeded',timeout=30000)
                run=json.loads(page.locator('#first-details').text_content());checks.append('Single task starts without experiment configuration')
                assert len(s.runs(run['experiment_id']))==1 and run['result']['requests']==0
                page.locator('#first-verify').click();expect(page.locator('#first-verdict')).to_contain_text('复验通过' if lang=='zh' else 're-verification passed');checks.append('Independent artifact verification')
                text='Clarify result.json and summary.json, and the next maintainer action.'
                page.locator('#first-feedback').fill(text);page.locator('#first-send-feedback').click();expect(page.locator('#first-feedback-status')).to_contain_text('已保存' if lang=='zh' else 'Feedback saved')
                page.reload();expect(page.locator('#first-details')).to_contain_text(run['id']);expect(page.locator('#first-feedback-status')).to_contain_text('关联反馈' if lang=='zh' else 'Linked feedback');checks.append('Run and feedback recover after refresh')
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                if code=='D2':
                    (s.root/'runs'/run['id']/'outputs'/'summary.json').write_text('{}')
                    page.locator('#first-verify').click();expect(page.locator('#first-verdict')).to_contain_text('Re-verification failed');checks.append('Tampered output is detected')
                    with page.expect_response(lambda r:r.url.endswith('/runs') and r.request.method=='POST') as response:page.locator('#first-run').click()
                    new_run=response.value.json()['id'];expect(page.locator('#first-details')).to_contain_text(new_run);expect(page.locator('#first-status')).to_have_text('succeeded',timeout=30000);checks.append('Explicit new run succeeds')
                if code=='D3':
                    page.locator('#first-feedback').fill('password=fixture-only');page.locator('#first-send-feedback').click();expect(page.locator('#first-message')).to_contain_text('移除');checks.append('Sensitive feedback blocked')
                if code=='D4':
                    response=page.request.get(url+'/api/doctor?target=filesystem');assert response.status==200
                    assert response.json()['ready'];checks.append('Registered external container prerequisites ready')
                    page.locator('#first-handoff').click();expect(page.locator('#result')).to_contain_text(run['id'])
                    page.locator('#task').select_option('docs-evidence-01');expect(page.locator('#material')).not_to_have_value('B')
                    with page.expect_response(lambda r:r.url.endswith('/runs') and r.request.method=='POST') as response:page.locator('#run').click()
                    new_run=response.value.json()['id'];expect(page.locator('#result')).to_contain_text(new_run);expect(page.locator('#status')).to_have_text('succeeded',timeout=30000)
                    checks.append('Official Filesystem container task accepted')
                if code=='D5':
                    page.locator('#first-doctor').focus();page.keyboard.press('Enter');expect(page.locator('#first-readiness')).to_contain_text('Ready');checks.append('Keyboard and mobile path')
                page.screenshot(path=str(out/(code+'.png')),full_page=True)
                if code=='D1':
                    page.locator('#first-handoff').click();expect(page.locator('#result')).to_contain_text(run['id']);expect(page.locator('#message')).to_contain_text(text);checks.append('Maintainer receives exact run and feedback')
            else:
                page.locator('#title').fill('v03 '+code);page.locator('#create button').click();expect(page.locator('#experiment')).not_to_have_value('')
                if code=='M2':
                    page.locator('#task').select_option('docs-evidence-01');expect(page.locator('#material')).not_to_have_value('B')
                else:page.locator('#material').select_option('B')
                page.locator('#run').click();expect(page.locator('#status')).to_have_text('succeeded',timeout=30000)
                run=json.loads(page.locator('#result').inner_text())
                page.locator('#feedback').fill('Explain output acceptance and first-task handoff.');page.locator('#send-feedback').click();expect(page.locator('#result')).to_contain_text('id')
                page.locator('.material-editor summary').click();page.locator('#material-name').fill(code+' acceptance guidance');page.locator('#material-reason').fill('Link first-task feedback to independently checked outputs.')
                if code=='M2':
                    page.locator('#load-parent').click();expect(page.locator('#material-descriptions')).to_have_value(re.compile('read_text_file'))
                page.locator('#material-guide').fill(page.locator('#material-guide').input_value()+' Inspect result.json and summary.json using independent re-verification.')
                with page.expect_response(lambda r:r.url.endswith('/api/materials') and r.request.method=='POST') as response:page.locator('#save-material').click()
                mid=response.value.json()['id'];expect(page.locator('#material')).to_have_value(mid)
                with page.expect_response(lambda r:r.url.endswith('/runs') and r.request.method=='POST') as response:page.locator('#run').click()
                expect(page.locator('#result')).to_contain_text(response.value.json()['id']);expect(page.locator('#status')).to_have_text('succeeded',timeout=30000)
                new_run=json.loads(page.locator('#result').inner_text())['id'];page.locator('#new-run').fill(new_run);page.locator('#decision').fill('Changed material, same task and independently accepted outputs.')
                page.locator('#revision').click();expect(page.locator('#result')).to_contain_text('id');checks.extend(['Immutable material revision','Comparable verified retest','Feedback-to-revision lineage'])
                page.screenshot(path=str(out/(code+'.png')),full_page=True)
            with s.connect() as c:
                c.execute("UPDATE runs SET cohort='automation' WHERE subject=?",(subject,));c.execute("UPDATE events SET cohort='automation' WHERE subject=?",(subject,))
            observations.append({'id':code,'role':role,'source':'codex_simulation','goal':'First successful MCP task and revision handoff','starting_condition':f'{lang}, {width}px, fresh browser context','path':' → '.join(checks),'result':'passed','friction':'See linked product issue ledger','assistance':'Codex operated the UI','evidence':code+'.png; run '+run['id'],'severity':'verified workflow','revision':'v0.3 first-task UI and target doctor','retest':new_run or run['id'],'automated_elapsed_seconds':round(time.monotonic()-started,3)})
            context.close();print(json.dumps({'role':code,'checks':len(checks),'passed':True}),flush=True)
        browser.close()
    # CLI and failure checks share this observation ledger.
    for task_id in ['task-11','task-01']:
        exp=s.experiment('v03 contract check');r=asyncio.run(execute(s,s.queue(exp,task_id,'B')));assert reverify(s,r['id'])['verification']['passed']
    report={'version':'0.3.0','source':'codex_simulation','records':observations,'page_errors':errors,'human_participants':0,'observed_human_sessions':0,'passed':not errors}
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with (out/'observations.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=observations[0].keys());w.writeheader();w.writerows(observations)
    print(json.dumps({'passed':not errors,'roles':len(observations),'page_errors':errors}))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
