"""Role-based browser walkthroughs with actual execution evidence and separate cohorts."""
import json
import os
import time
from datetime import datetime,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from adoptlab.config import RUNTIME
from adoptlab.store import Store

PROFILES=[
    ('M1','SDK maintainer','maintainer','en','task-01','A',1440),
    ('M2','DevRel maintainer','maintainer','zh','task-05','B',1440),
    ('M3','Privacy-conscious team maintainer','maintainer','en','task-11','B',1440),
    ('D1','Python onboarding beginner','developer','en','task-01','A',1440),
    ('D2','Finance API developer','developer','zh','task-05','B',1440),
    ('D3','Error-handling integrator','developer','en','task-11','A',1440),
    ('D4','Mobile documentation reader','developer','zh','task-07','B',390),
    ('D5','Privacy-conscious returning developer','developer','en','task-09','A',1440),
]

def main():
    out=RUNTIME/'output'/'role-review';out.mkdir(parents=True,exist_ok=True)
    records=[];url=os.getenv('ADOPTLAB_BROWSER_URL','http://127.0.0.1:8768');errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',headless=True)
        for code,role,view,lang,task,material,width in PROFILES:
            started=datetime.now(timezone.utc).isoformat();clock=time.perf_counter()
            context=browser.new_context(viewport={'width':width,'height':900});page=context.new_page()
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(f'{url}/?view={view}&lang={lang}&source=role_review&campaign={code}')
            subject=page.evaluate("localStorage.getItem('adoptlab-subject')")
            checks=[]
            if code=='D1':
                page.locator('#experiment').select_option('');page.locator('#run').click()
                expect(page.locator('#message')).to_contain_text('Create or select an experiment')
                checks.append('Missing experiment produces an actionable message')
            page.locator('#title').fill('Role review '+code)
            page.get_by_role('button',name='创建' if lang=='zh' else 'Create',exact=True).click()
            expect(page.locator('#experiment')).not_to_have_value('');exp=page.locator('#experiment').input_value()
            page.locator('#task').select_option(task);page.locator('#material').select_option(material)
            page.locator('#run').click();expect(page.locator('#status')).to_have_text('succeeded',timeout=40000)
            first=json.loads(page.locator('#result').inner_text());run=first['id']
            expected_kind='correct_rejection' if task=='task-11' else 'artifact'
            assert first['result']['verification']['kind']==expected_kind
            if task=='task-11':
                expect(page.locator('#verdict')).to_contain_text('correctly rejected')
                checks.append('Successful invalid-input rejection has explicit explanatory text')
            else:checks.append('Independent artifact acceptance passed')
            page.locator('#compare').click()
            expect(page.locator('#comparison-table')).to_contain_text('human_unverified')
            checks.append('Browser comparison appears in its own cohort')
            if code=='D4':
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.locator('#send-feedback').click()
                expect(page.locator('#message')).to_contain_text('必填')
                checks.append('Mobile page fits viewport and empty feedback shows actionable validation')
            text={'M1':'Need browser execution results in the material comparison.','M2':'Explain currency totals and the meaning of the independent verdict.','M3':'Explain correct rejection and removal of session records.','D1':'Show the first required experiment action before execution.','D2':'Keep currency totals separate and explain integer cents.','D3':'A successful rejection should explicitly state why no output was written.','D4':'Required-field validation should be readable on a narrow viewport.','D5':'Withdraw previous records and start a fresh anonymous session.'}[code]
            page.locator('#feedback').fill(text)
            with page.expect_response(lambda r:r.url.endswith('/api/feedback')) as response:page.locator('#send-feedback').click()
            feedback=response.value.json()['id'];expect(page.locator('#result')).to_contain_text(feedback)
            checks.append('Feedback saved with task/run linkage')
            revision=None
            if code.startswith('M'):
                page.locator('.material-editor summary').click()
                page.locator('#material-guide').fill(page.locator('#material-guide').input_value()+' Review both output artifacts or the expected structured rejection before recording a revision.')
                with page.expect_response(lambda r:r.url.endswith('/api/materials') and r.request.method=='POST') as response:page.locator('#save-material').click()
                version=response.value.json()['id'];expect(page.locator('#material')).to_have_value(version)
                with page.expect_response(lambda r:r.url.endswith('/runs') and r.request.method=='POST') as response:page.locator('#run').click()
                revised=response.value.json()['id'];expect(page.locator('#result')).to_contain_text(revised)
                expect(page.locator('#status')).to_have_text('succeeded',timeout=40000)
                page.locator('#new-run').fill(revised);page.locator('#decision').fill('Clarify acceptance evidence and retain backend/schema parity.')
                with page.expect_response(lambda r:r.url.endswith('/api/revisions')) as response:page.locator('#revision').click()
                revision=response.value.json()['id'];expect(page.locator('#result')).to_contain_text(revision)
                checks.append('Immutable material revision linked to same-task verified execution')
            page.screenshot(path=str(out/(code+'.png')),full_page=True)
            withdrawn=False;new_subject=None
            if code in {'M3','D5'}:
                page.locator('#withdraw').click();expect(page.locator('#verdict')).to_contain_text('new anonymous session')
                new_subject=page.evaluate("localStorage.getItem('adoptlab-subject')");assert new_subject!=subject
                withdrawn=True
                page.locator('#run').click();expect(page.locator('#status')).to_have_text('succeeded',timeout=40000)
                checks.append('Withdraw clears linkage and further execution uses a fresh anonymous session')
            # This runtime only contains the automated review, so classification is isolated.
            s=Store()
            with s.connect() as c:
                for sub in [subject,new_subject]:
                    if sub:
                        c.execute("UPDATE runs SET cohort='automation' WHERE subject=? AND cohort='human_unverified'",(sub,))
                        c.execute("UPDATE events SET cohort='automation' WHERE subject=? AND cohort='human_unverified'",(sub,))
            records.append({'role_id':code,'role':role,'view':view,'language':lang,'first_seen_material':material,'task_id':task,
                'experiment_id':exp,'run_id':run,'feedback_id':feedback,'revision_id':revision,'withdrawn':withdrawn,
                'started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),'automated_elapsed_seconds':round(time.perf_counter()-clock,3),
                'checks':checks,'verdict':first['result']['verification'],'cohort':'automation','independent_human_count':0})
            print(json.dumps({'role':code,'passed':True,'checks':len(checks)}),flush=True);context.close()
        browser.close()
    report={'profiles':records,'page_errors':errors,'passed':not errors,'human_participants':0,'inference_cost_cny':0,'mode':'protocol','interpretation':'Role-based usability review and automated execution; elapsed time measures automation, not human onboarding.'}
    (out/'observations.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    assert not errors

if __name__=='__main__':main()
