"""Automated v0.2 history, external task and saved-evidence browser acceptance."""
import json
import os
from playwright.sync_api import sync_playwright,expect
from adoptlab.config import RUNTIME
from adoptlab.store import Store

def main():
    url=os.getenv('ADOPTLAB_BROWSER_URL','http://127.0.0.1:8767')
    public=os.getenv('ADOPTLAB_PUBLIC_URL','http://127.0.0.1:8770')
    out=RUNTIME/'output'/'v02-browser';out.mkdir(parents=True,exist_ok=True)
    errors=[];checks=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url);page.locator('#title').fill('Automated v02 acceptance');page.locator('#create button').click()
        expect(page.locator('#experiment')).not_to_have_value('');exp=page.locator('#experiment').input_value()
        page.locator('#run').click();expect(page.locator('#status')).to_have_text('succeeded',timeout=30000)
        id=json.loads(page.locator('#result').inner_text())['id'];page.reload();expect(page.locator('#result')).to_contain_text(id);checks.append('run selection restored')
        page.locator('#load-history').click();expect(page.locator('#history-list')).to_contain_text('task-01');checks.append('history visible')
        page.locator('#feedback').fill('Use explicit document source and output paths.');page.locator('#send-feedback').click();expect(page.locator('#result')).to_contain_text('id')
        page.reload();page.locator('#handoff').click();expect(page.locator('#result')).to_contain_text('Use explicit document');checks.append('feedback handoff restored')
        page.locator('#task').select_option('docs-evidence-01');expect(page.locator('#material')).not_to_have_value('A')
        page.locator('#run').click();expect(page.locator('#status')).to_have_text('succeeded',timeout=30000);expect(page.locator('#result')).to_contain_text('evidence.json');checks.append('external container task')
        page.screenshot(path=str(out/'workspace-en.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');checks.append('local mobile bounds')
        page.goto(public);expect(page.locator('#demo-case option')).not_to_have_count(0)
        for _ in range(3):page.locator('#demo-next').click()
        value=json.loads(page.locator('#demo-evidence').inner_text());assert value['before']['passed'] is False and value['after']['passed'] is True
        checks.append('saved paired revision walkthrough')
        page.locator('#language').click();expect(page.locator('#demo-reset')).to_have_text('重置体验')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');checks.append('public bilingual mobile bounds')
        page.screenshot(path=str(out/'public-mobile-zh.png'),full_page=True);browser.close()
    s=Store()
    with s.connect() as c:
        subjects=[r[0] for r in c.execute('SELECT DISTINCT subject FROM runs WHERE experiment_id=?',(exp,))]
        for subject in subjects:
            c.execute("UPDATE runs SET cohort='automation' WHERE subject=?",(subject,));c.execute("UPDATE events SET cohort='automation' WHERE subject=?",(subject,))
    result={'passed':not errors,'checks':checks,'page_errors':errors,'cohort':'automation','human_participants':0}
    (out/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
