from pathlib import Path
import json,hashlib
from playwright.sync_api import sync_playwright
D=Path(__file__).parent/'rin_extension/ground122_contact_review';errors=[];external=[]
with sync_playwright()as pw:
 b=pw.chromium.launch(channel='msedge',headless=True)
 c=b.new_context(offline=True,viewport={'width':1000,'height':900});p=c.new_page()
 p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:external.append(r.url)if not r.url.startswith(('file:','data:'))else None)
 p.goto((D/'REVIEW.html').resolve().as_uri());p.wait_for_function("document.getElementById('name').textContent.includes('61')")
 checks=0
 for f in ('normal','black'):
  p.select_option('#form',f)
  for i in range(18):
   p.evaluate('(i)=>{at=i;draw()}',i)
   assert p.evaluate("x.imageSmoothingEnabled===false && imgs[form.value][at].complete")
   assert p.locator('#name').text_content();checks+=1
  p.evaluate('at=2;draw()');p.screenshot(path=str(D/f'{f}_browser.png'))
 p.locator('#play').click();p.wait_for_timeout(120);assert p.evaluate('playing');p.locator('#play').click()
 assert not errors and not external
 b.close()
j={'passed':True,'frames':checks,'offline':True,'page_errors':errors,'external_requests':external,'canvas_scale':6,'source_origin':[160,160],'html_sha256':hashlib.sha256((D/'REVIEW.html').read_bytes()).hexdigest(),'native_game_runtime':False}
(D/'browser_verification.json').write_text(json.dumps(j,indent=2)+'\n','utf8');print(json.dumps(j))
