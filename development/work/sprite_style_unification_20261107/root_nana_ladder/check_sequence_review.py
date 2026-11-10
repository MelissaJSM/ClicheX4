"""Check offline canvas pixels and native order, not game physics."""
from pathlib import Path
import sys,json,base64,io,hashlib
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
D=Path(__file__).resolve().parent/'native_sequence01';ROOT=D.parents[3];H=D.parent.parent/'shibuki_audit';sys.path[:0]=[str(ROOT),str(H)]
from check_shibuki_hurt_browser import timeline
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 assert not (D/'browser_verification.json').exists();report=json.loads((D/'report.json').read_text('utf8'));errors=[];network=[];rows=[]
 counts={27:115,28:125,29:120,30:110,31:75,32:75,92:25,93:110}
 expected_images={name:np.array(Image.open(D/name).convert('RGBA')) for name in report['native_pngs']}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='msedge',headless=True);ctx=browser.new_context(offline=True,viewport={'width':1150,'height':850});p=ctx.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:network.append(r.url) if not r.url.startswith(('file:','data:')) else None);p.goto((D/'REVIEW.html').as_uri());p.wait_for_function('window.review && review.ready()')
  for s in report['sequences']:
   aid=s['id'];expected=timeline(s,counts[aid]);p.evaluate('(id)=>review.reset(id)',aid);trace=[]
   for call,ref in enumerate(expected):
    if call:p.evaluate('review.step()')
    state=p.evaluate('review.state()');assert state['ref']==ref,(aid,call,state)
    data=base64.b64decode(p.evaluate("canvas.toDataURL('image/png')").split(',',1)[1]);actual=np.array(Image.open(io.BytesIO(data)).convert('RGBA'))
    for x,form in ((0,'base'),(96,'fourth')):assert np.array_equal(actual[:,x:x+96],expected_images[f'{form}_{ref:03}_native.png']),(aid,call,form)
    trace.append(state)
   assert trace[-1]['holding']==(aid in (92,93))
   rows.append({'id':aid,'canvas_checks':len(trace)*2,'trace':trace})
  p.evaluate('review.reset(31)');p.locator('#play').click();p.wait_for_function('review.state().total >= 70',timeout=5000);p.locator('#play').click();paused=p.evaluate('review.state()');assert not paused['playing'];p.wait_for_timeout(120);assert p.evaluate('review.state()')==paused
  p.screenshot(path=str(D/'browser_ladder31.png'));browser.close()
 assert not errors and not network
 (D/'browser_verification.json').write_text(json.dumps({'passed':True,'html_sha256':sha((D/'REVIEW.html').read_bytes()),'native_report_sha256':sha((D/'report.json').read_bytes()),'cases':rows,'timed_play_pause':paused,'errors':errors,'external_requests':network,'offline':True,'runtime_verified':False,'continuous_animation_actually_watched_by_model':False},ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'passed':True,'canvas_checks':sum(r['canvas_checks'] for r in rows)}))
if __name__=='__main__':main()
