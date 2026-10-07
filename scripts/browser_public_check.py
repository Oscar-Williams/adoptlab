"""Public evidence acceptance; no human-participant or inference records."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from adoptlab.config import RUNTIME

def main():
    url=os.getenv('ADOPTLAB_PUBLIC_URL','http://127.0.0.1:8770')
    output=RUNTIME.parent/'release-browser';output.mkdir(exist_ok=True)
    errors=[];checks=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge')
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.on('pageerror',lambda e:errors.append(str(e)))
        response=page.goto(url.rstrip('/')+'/experiments.html');expect(page.locator('#summary')).to_contain_text('model: 130/144')
        if url.startswith('https://'):
            headers=response.all_headers()
            assert "default-src 'self'" in headers['content-security-policy']
            assert headers['x-content-type-options']=='nosniff'
            checks.append('hosted security response headers')
        assert 'v0.3.0' in page.locator('footer').inner_text()
        checks.append('v0.3 product documentation and version')
        assets=page.evaluate("async()=>{const files=['report.json','report-v1.json','tutorial.md','experiment-results.md','experiment-results-v1.md','competitive.md','v02-validation.md','review-results.md','LICENSE.txt','product-prd.md','product-prd.zh-CN.md','v03-validation.md'];return await Promise.all(files.map(async name=>{const r=await fetch(name);return {name,status:r.status,bytes:(await r.text()).length}}))}")
        assert all(a['status']==200 and a['bytes']>0 for a in assets)
        checks.append('all report/document/license downloads available')
        page.locator('#mode').select_option('protocol');expect(page.locator('#summary')).to_contain_text('protocol: 48/48')
        page.locator('#mode').select_option('model');page.locator('#material').select_option('AA')
        expect(page.locator('#summary')).to_contain_text('model: 23/36')
        page.locator('#split').select_option('held_out');expect(page.locator('#summary')).to_contain_text('model: 6/18')
        checks.append('separate mode/material/split denominators')
        for _ in range(3):page.locator('#demo-next').click()
        pair=json.loads(page.locator('#demo-evidence').inner_text())
        assert pair['conditions_matched'] and not pair['before']['passed'] and pair['after']['passed']
        assert pair['before']['condition']==pair['after']['condition'] and pair['before']['responder']==pair['after']['responder']
        checks.append('condition-matched saved comparison')
        page.locator('#version').select_option('report-v1.json');expect(page.locator('#summary')).to_contain_text('model: 57/72')
        expect(page.locator('#demo-next')).to_be_disabled();checks.append('historical v1 retained without unsupported pairing')
        page.locator('#version').select_option('report.json');expect(page.locator('#summary')).to_contain_text('model: 130/144')
        original=page.evaluate("async()=>await (await fetch('report.json')).json()")
        for scenario in ['mismatch','unknown']:
            modified=json.loads(json.dumps(original))
            for i,row in enumerate(modified['cases']):
                if scenario=='mismatch':row['condition']=format(i,'064x')
                elif not row['passed']:row['responder']=None
            page.route('**/report.json',lambda route,request:route.fulfill(json=modified))
            page.locator('#retry-report').click();expect(page.locator('#demo-evidence')).to_contain_text('no failed pair')
            expect(page.locator('#demo-next')).to_be_disabled()
            page.unroute('**/report.json');checks.append(scenario+' pair rejected')
        page.route('**/report.json',lambda route:route.abort())
        page.locator('#retry-report').click();expect(page.locator('#summary')).to_contain_text('Evidence unavailable')
        expect(page.locator('#cases tr')).to_have_count(0);checks.append('failed reload clears stale results')
        page.unroute('**/report.json');page.locator('#retry-report').click();expect(page.locator('#summary')).to_contain_text('model: 130/144')
        page.locator('#language').click();expect(page.locator('#retry-report')).to_have_text('重新加载证据')
        page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(output/'public-mobile-zh.png'),full_page=True);checks.append('Chinese mobile and reload recovery')
        browser.close()
    result={'passed':not errors,'checks':checks,'page_errors':errors,'source':'browser_automation','human_participants':0}
    (output/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
