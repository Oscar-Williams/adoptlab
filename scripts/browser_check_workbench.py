"""Edge behavior and layout verification; no automated check counts as a user."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from adoptlab.config import RUNTIME, CODE

PAGES=['overview','environment','catalog','task','experiment','comparison','history','run','materials','feedback','release','developer','observations','showcase']

def main():
    base=os.getenv('ADOPTLAB_BROWSER_URL','http://127.0.0.1:8780')
    out=RUNTIME/'output/edge';out.mkdir(parents=True,exist_ok=True)
    evidence=json.loads((CODE/'runtime/v04-validation.json').read_text())
    errors=[];checks=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+'/workspace')
        page.evaluate('(s)=>{localStorage.setItem("adoptlab-v04-experiment",s.exp);localStorage.setItem("adoptlab-v04-run",s.run)}',{'exp':evidence['experiment_id'],'run':evidence['cases'][2]['new_run']})
        for lang in ['zh','en']:
            page.goto(base+'/workspace?lang='+lang)
            expect(page.locator('#navigation a')).to_have_count(14)
            for key in PAGES:
                page.locator('#navigation a[href="#'+key+'"]').click()
                expect(page.locator('#content h2').first).to_be_visible()
                assert 'Cannot display yet' not in page.locator('#content').inner_text()
                assert '暂时无法显示' not in page.locator('#content').inner_text()
                page.screenshot(path=str(out/(lang+'-'+key+'-1440.png')),full_page=True)
                checks.append({'language':lang,'page':key,'width':1440,'rendered':True})
        # The exact example is imported, field-validated and registered through the new editor.
        page.goto(base+'/workspace?lang=zh#task')
        expect(page.locator('#content h2')).to_have_text('定义可独立验收的任务')
        page.get_by_text('导入JSON任务包',exact=True).click()
        task=json.loads((CODE/'examples/document-config-task.json').read_text())
        task['id']='docs-config-ui-v04'
        page.get_by_label('任务包JSON',exact=True).fill(json.dumps(task))
        page.get_by_role('button',name='载入编辑器（不登记）',exact=True).click()
        expect(page.get_by_label('Task ID',exact=True)).to_have_value(task['id'])
        paths=page.get_by_label('JSON路径',exact=True)
        paths.first.fill('invalid-json')
        page.get_by_role('button',name='预检契约',exact=True).click()
        expect(page.locator('#notice')).not_to_be_empty()
        assert page.get_by_role('button',name='预检契约',exact=True).is_enabled()
        paths.first.fill(json.dumps(task['rules'][0]['path']))
        page.get_by_role('button',name='预检契约',exact=True).click()
        expect(page.get_by_text('预检通过，可登记不可变任务。',exact=True)).to_be_visible()
        page.get_by_role('button',name='预检并登记',exact=True).click()
        expect(page.locator('#notice')).to_contain_text(task['id'])
        # Enqueue the editor-created contract using its matching material. No model requests.
        exp=page.request.post(base+'/api/experiments',data={'title':'Editor-created contract acceptance'}).json()['id']
        material=evidence['report']['runs'][-1]['material']
        result=page.request.post(base+'/api/experiments/'+exp+'/batch',data={'tasks':[task['id']],'materials':[material],'mode':'protocol','trials':1})
        assert result.ok,result.text()
        rid=result.json()['run_ids'][0]
        page.evaluate('(s)=>{localStorage.setItem("adoptlab-v04-experiment",s.exp);localStorage.setItem("adoptlab-v04-run",s.run)}',{'exp':exp,'run':rid})
        page.goto(base+'/workspace?lang=zh#run')
        expect(page.locator('#run-context')).to_have_value(rid)
        expect(page.locator('#content')).to_contain_text(task['id'])
        expect(page.locator('.badge.status')).to_have_text('succeeded',timeout=60000)
        page.reload();expect(page.locator('#run-context')).to_have_value(rid)
        expect(page.locator('.badge.status')).to_have_text('succeeded',timeout=60000)
        page.get_by_role('button',name='独立复验产物',exact=True).click()
        expect(page.locator('#notice')).to_contain_text('artifact_hash_matches')
        for width in [1024,390]:
            page.set_viewport_size({'width':width,'height':900})
            for lang in ['zh','en']:
                page.goto(base+'/workspace?lang='+lang+'#developer')
                expect(page.locator('#content h2')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                page.screenshot(path=str(out/(lang+'-developer-'+str(width)+'.png')),full_page=True)
                page.goto(base+'/showcase/workbench.html')
                expect(page.locator('#actual table')).to_be_visible()
                if lang=='en':page.locator('#language').click()
                for i in range(3):
                    page.locator('#cases button').nth(i).click()
                    for step in range(6):
                        page.locator('#steps button').nth(step).click()
                        expect(page.locator('#step-title')).not_to_be_empty()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                page.screenshot(path=str(out/(lang+'-public-'+str(width)+'.png')),full_page=True)
                checks.append({'language':lang,'width':width,'developer':True,'public_cases':3,'public_steps':18})
        page.keyboard.press('Tab')
        assert page.evaluate('document.activeElement.tagName') in ['A','BUTTON']
        report=page.request.get(base+'/showcase/workbench-evidence.json')
        assert report.ok and len(report.json()['cases'])==3
        browser.close()
    assert not errors,errors
    result={'browser':'Microsoft Edge','automated_only':True,'human_sessions':0,'checks':checks,'page_errors':errors,'editor_contract_run':rid}
    (out/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'browser':'Edge','pages':28,'responsive_paths':8,'editor_contract':rid,'errors':len(errors)}))

if __name__=='__main__':main()
