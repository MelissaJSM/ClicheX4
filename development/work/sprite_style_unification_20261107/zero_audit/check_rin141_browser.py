from pathlib import Path
import json,hashlib
from playwright.sync_api import sync_playwright
D=Path(__file__).parent/'rin_extension/ground_wall141_review';errors=[];external=[];checks=0
with sync_playwright()as pw:
 b=pw.chromium.launch(channel='msedge',headless=True);c=b.new_context(offline=True,viewport={'width':1100,'height':700});p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:external.append(r.url)if not r.url.startswith(('file:','data:'))else None);p.goto((D/'REVIEW.html').resolve().as_uri());p.wait_for_function("document.getElementById('label').textContent.includes('61')")
 for g,count in [('ground',18),('wall',12)]:
  p.select_option('#group',g)
  for f in ('normal','black'):
   p.select_option('#form',f)
   for i in range(count):
    p.evaluate('(i)=>{at=i;draw()}',i);assert p.evaluate('ctx.imageSmoothingEnabled===false && imgs[group.value][form.value+"_new"][at].complete');assert p.locator('#label').text_content();checks+=1
   p.evaluate('at=6;draw()');p.screenshot(path=str(D/f'{g}_{f}_browser.png'))
 p.locator('#play').click();p.wait_for_timeout(300);assert p.evaluate('playing');p.locator('#play').click();assert not errors and not external;b.close()
j={'passed':True,'frames':checks,'offline':True,'page_errors':errors,'external_requests':external,'canvas_integer_scale':4,'source_origin':[160,160],'html_sha256':hashlib.sha256((D/'REVIEW.html').read_bytes()).hexdigest(),'native_runtime':False}
(D/'browser_verification.json').write_text(json.dumps(j,indent=2)+'\n','utf8');print(json.dumps(j))
