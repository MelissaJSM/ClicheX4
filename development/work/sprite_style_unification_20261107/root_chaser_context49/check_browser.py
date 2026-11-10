from pathlib import Path
import base64,hashlib,io,json,re
from PIL import Image,ImageOps
import numpy as np
from playwright.sync_api import sync_playwright
O=Path(__file__).resolve().parent;ROOT=O.parents[2]
html=ROOT/'out/sprite_style_unification_20261107/chaser_context49/CHASE_RIDER_REVIEW.html'
raw=html.read_text('utf8');data=json.JSONDecoder().raw_decode(raw.split('const DATA=',1)[1])[0]
def decode(s):return Image.open(io.BytesIO(base64.b64decode(s.split(',',1)[1]))).convert('RGBA')
images={f:{r:decode(s)for r,s in refs.items()}for f,refs in data['riders'].items()}
bodies={f:{r:decode(s)for r,s in refs.items()}for f,refs in data['bodies'].items()}
errors=[];requests=[];screens=[];checked=0;states=0;pair_seen=set()
with sync_playwright()as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True)
    context=browser.new_context(offline=True,viewport={'width':1120,'height':1090},device_scale_factor=1)
    page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url)if not r.url.startswith(('file:','data:'))else None)
    page.goto(html.resolve().as_uri());page.wait_for_function('window.ready===true')
    for i,tl in enumerate(data['timelines']):
        for tick in range(32):
            key=(tl['bike'][tick],tl['x'][tick],tl['zero'][tick])
            if key in pair_seen:continue
            pair_seen.add(key)
            page.evaluate('([s,t])=>showPair(s,t)',[i,tick]);assert page.evaluate('window.renderedTick')==tick
            outputs=page.locator('canvas').evaluate_all('(cs)=>cs.map(c=>c.toDataURL())')
            for f,src in zip(data['forms'],outputs):
                expect=Image.alpha_composite(bodies[f['body']][str(tl['bike'][tick])],images[f['key']][str(tl[f['type']][tick])])
                assert np.array_equal(np.array(decode(src)),np.array(expect)),(f['key'],i,tick)
                checked+=1
            states+=1
    for i,tick,mirror in ((3,4,False),(4,12,False),(8,10,False),(11,8,True)):
        page.evaluate('([s,t,m])=>showPair(s,t,m)',[i,tick,mirror])
        if mirror:
            tl=data['timelines'][i];outputs=page.locator('canvas').evaluate_all('(cs)=>cs.map(c=>c.toDataURL())')
            for f,src in zip(data['forms'],outputs):
                expect=ImageOps.mirror(Image.alpha_composite(bodies[f['body']][str(tl['bike'][tick])],images[f['key']][str(tl[f['type']][tick])]))
                assert np.array_equal(np.array(decode(src)),np.array(expect));checked+=1
        p=O/f'browser_sequence{i:02}_tick{tick:02}_mirror{int(mirror)}.png';page.screenshot(path=str(p),full_page=True);screens.append(p.name)
    page.evaluate('showPair(3,0,false)');page.locator('#play').click();page.wait_for_function('window.renderedTick>=4');page.locator('#play').click()
    paused=page.evaluate('window.renderedTick');page.wait_for_timeout(100);assert page.evaluate('window.renderedTick')==paused
    page.evaluate('showPair(3,30,false)');page.locator('#play').click();page.wait_for_function('window.renderedTick===31');page.wait_for_timeout(100);assert page.evaluate('window.renderedTick')==31
    browser.close()
assert not errors and not requests
report={'passed':True,'html_sha256':hashlib.sha256(html.read_bytes()).hexdigest(),'unique_pose_pairs':states,'canvas_composites_equal':checked,'mirrored_forms_checked':12,'external_requests':requests,'errors':errors,'play_pause_and_terminal_hold':True,'screenshots':screens,'screenshots_actually_viewed':False,'runtime_verified':False}
(O/'browser_verification.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
print(json.dumps(report))
