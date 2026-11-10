from pathlib import Path
import json,hashlib,base64,io
from PIL import Image
import numpy as np
from playwright.sync_api import sync_playwright
D=Path(__file__).resolve().parent/'ground_boots_cycle03';proof=[];errors=[];requests=[]
with sync_playwright()as p:
 browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':1100,'height':900},offline=True)
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url)if not r.url.startswith(('file:','data:','blob:'))else None)
 page.goto((D/'REVIEW.html').as_uri());page.wait_for_function('document.querySelector("#status").textContent.includes("ref")');page.evaluate('run=false;index=elapsed=0;draw()')
 names=page.evaluate('Object.keys(cases)')
 for palette in('normal','black'):
  page.select_option('#palette',palette)
  for name in names:
   page.select_option('#which',label=name);length=page.evaluate('sequence.length');results=[]
   for k in range(length):
    actual=page.evaluate('''k=>{index=k;draw();return {ref:sequence[k].ref,calls:sequence[k].calls,pixels:[0,1].map(s=>Array.from(document.getElementById('small'+s).getContext('2d').getImageData(0,0,96,80).data)),uris:data[palette.value][sequence[k].ref]}}''',k)
    for side in range(2):
     expected=np.asarray(Image.open(io.BytesIO(base64.b64decode(actual['uris'][side].split(',')[1]))).convert('RGBA')).copy();expected[expected[:,:,3]==0,:3]=0
     assert np.array_equal(np.array(actual['pixels'][side],np.uint8).reshape(80,96,4),expected),(palette,name,k,side)
    results.append({'ref':actual['ref'],'calls':actual['calls'],'pixels_exact':True})
   page.evaluate('advance()');assert page.evaluate('index===selected.loop')
   proof.append({'palette':palette,'name':name,'steps':results,'native_loop_entry_exact':True})
 page.select_option('#palette','normal');page.select_option('#which',label=names[0]);page.select_option('#speed','1');page.evaluate('run=true;index=elapsed=0;draw()');page.wait_for_timeout(500);assert page.evaluate('last>0 && run');page.click('#play');state=page.evaluate('({index,elapsed,run})');page.wait_for_timeout(100);assert page.evaluate('({index,elapsed,run})')==state
 page.click('#step');current_length=page.evaluate('sequence.length');assert page.evaluate('index')==(state['index']+1 if state['index']+1<current_length else page.evaluate('selected.loop'))
 page.screenshot(path=str(D/'browser_review.png'),full_page=True);browser.close()
assert not errors and not requests
result={'passed':True,'html_sha256':hashlib.sha256((D/'REVIEW.html').read_bytes()).hexdigest(),'cases':proof,'native_pixel_exact_steps':sum(len(q['steps'])for q in proof),'pause_and_step_verified':True,'console_errors':errors,'network_requests':requests,'runtime_verified':False,'scope':'Offline packed pixels, actual sequence bytes and loop entries; no game logic/events.'}
(D/'browser_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'passed':True,'steps':result['native_pixel_exact_steps']}))
