"""Automated product workflow, explicitly excluded from human adoption."""
import json
import re
import os
from playwright.sync_api import sync_playwright, expect
from adoptlab.config import RUNTIME
from adoptlab.store import Store

def main():
    out=RUNTIME/'output'/'playwright';out.mkdir(parents=True,exist_ok=True)
    errors=[]
    url=os.getenv('ADOPTLAB_BROWSER_URL','http://127.0.0.1:8766')
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1080})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url+'/?source=automation&campaign=browser_check')
        subject=page.evaluate("localStorage.getItem('adoptlab-subject')")
        page.locator('#title').fill('Automated product workflow')
        page.get_by_role('button',name='Create',exact=True).click()
        expect(page.locator('#experiment')).to_have_value(re.compile('.+'))
        exp=page.locator('#experiment').input_value()
        page.locator('#run').click();expect(page.locator('#status')).to_have_text('succeeded',timeout=40000)
        first=json.loads(page.locator('#result').inner_text())['id']
        page.locator('#feedback').fill('The guide should explain integer cents and the independent verifier.')
        with page.expect_response(lambda r:r.url.endswith('/api/feedback')) as response:
            page.locator('#send-feedback').click()
        expect(page.locator('#result')).to_contain_text(response.value.json()['id'])
        feedback=json.loads(page.locator('#result').inner_text())['id']
        page.locator('.material-editor summary').click()
        page.locator('#material-guide').fill(page.locator('#material-guide').input_value()+' Check that both files are written, including an empty result.')
        with page.expect_response(lambda r:r.url.endswith('/api/materials') and r.request.method=='POST') as response:
            page.locator('#save-material').click()
        material_id=response.value.json()['id']
        expect(page.locator('#material')).to_have_value(material_id)
        with page.expect_response(lambda r:r.url.endswith('/runs') and r.request.method=='POST') as response:
            page.locator('#run').click()
        expect(page.locator('#result')).to_contain_text(response.value.json()['id'])
        expect(page.locator('#status')).to_have_text('succeeded',timeout=40000)
        second=json.loads(page.locator('#result').inner_text())['id']
        assert second!=first
        page.locator('#new-run').fill(second);page.locator('#decision').fill('Add explicit cents, timezone and error handling guidance; retain identical backend capabilities.')
        with page.expect_response(lambda r:r.url.endswith('/api/revisions')) as response:
            page.locator('#revision').click()
        expect(page.locator('#result')).to_contain_text(response.value.json()['id'])
        assert 'id' in json.loads(page.locator('#result').inner_text())
        page.locator('#verify').click();expect(page.locator('#result')).to_contain_text('manifest_matches_db')
        assert json.loads(page.locator('#result').inner_text())['verification']['passed']
        page.screenshot(path=str(out/'maintainer-en.png'),full_page=True)
        page.goto(url+'/?lang=zh&view=developer')
        assert page.get_by_role('heading',name='完成你的首次任务').is_visible()
        page.screenshot(path=str(out/'developer-zh.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.screenshot(path=str(out/'developer-mobile.png'),full_page=True)
        browser.close()
    s=Store()
    with s.connect() as c:
        subjects=[r[0] for r in c.execute("SELECT DISTINCT subject FROM runs WHERE experiment_id IN (SELECT id FROM experiments WHERE title='Automated product workflow')")]
        for sub in subjects:
            c.execute("UPDATE runs SET cohort='automation' WHERE subject=?",(sub,))
            c.execute("UPDATE events SET cohort='automation' WHERE subject=?",(sub,))
    report={'passed':not errors,'page_errors':errors,'workflow':['create','run A','feedback','immutable material revision','run new version','verified revision','independent reverify','English','Chinese','mobile'],
            'experiment_id':exp,'cohort':'automation','browser':'installed Edge','human_participants':0}
    (out/'browser-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
