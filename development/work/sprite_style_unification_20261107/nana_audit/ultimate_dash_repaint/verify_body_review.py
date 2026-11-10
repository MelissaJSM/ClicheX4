"""소유 폴더의 미패킹 검토 HTML을 headless로 검사; 게임과 GUI 무접근."""
from pathlib import Path
import sys,json,hashlib
from playwright.sync_api import sync_playwright
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D.parent/'native_restore'))
from preview_restore import write,digest,need
def main():
 d=D/'before_bodies_review_v1';meta=json.loads((d/'manifest.json').read_text('utf8'));checks=[];playchecks=[];errors=[]
 with sync_playwright()as p:
  browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':1280,'height':640},device_scale_factor=1);page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda route:route.abort()if route.request.url.startswith(('http:','https:'))else route.continue_());page.goto((d/'REVIEW.html').resolve().as_uri());page.evaluate('review.ready');page.evaluate('review.pause()')
  for q in meta['frames']:
   page.evaluate('(n)=>review.selectRef(n)',q['ref']);arrays=page.evaluate('()=>Array.from({length:3},(_,j)=>Array.from(document.getElementById("small"+j).getContext("2d").getImageData(0,0,96,80).data))')
   for j,values in enumerate(arrays):
    actual=hashlib.sha256(bytes(values)).hexdigest();need(actual==q['canvas_rgba_sha256'][j],f'Canvas {q["ref"]}/{j}');checks.append([q['ref'],j,actual])
  for name,seq in meta['cases'].items():
   page.evaluate('(k)=>{review.setCase(k);review.pause()}',name);expected=0
   for _ in range(len(seq)*2+1):
    state=page.evaluate('review.state()');need(state['ref']==seq[expected]['ref'],'Order');offset=seq[expected]['step'];expected=expected+offset if offset else 0
    if expected<0 or expected>=len(seq):expected=0
    page.evaluate('review.step()')
   page.evaluate('(k)=>{review.setCase(k);review.play()}',name);start=page.evaluate('review.state()');page.wait_for_timeout(max(650,round(seq[0]['calls']/60*1000)+120));end=page.evaluate('review.state()');need(end['draws']>start['draws'],'Playback');page.evaluate('review.pause()');paused=page.evaluate('review.state()');page.wait_for_timeout(180);need(paused==page.evaluate('review.state()'),'Pause');playchecks.append({'name':name,'draw_delta':end['draws']-start['draws'],'paused_exact':True})
  for n in(71,75,94):page.evaluate('(n)=>review.selectRef(n)',n);page.screenshot(path=str(d/f'headless_{n:03}.png'))
  version=browser.version;browser.close()
 need(not errors,'Browser errors');write(d/'verification.json',{'passed':True,'html_sha256':digest(d/'REVIEW.html'),'canvas_checks':len(checks),'checks':checks,'two_relative_step_cycles':True,'play_pause_checks':playchecks,'browser':'Edge headless','version':version,'network_permitted':False,'native_packed':False,'runtime_verified':False,'limits':meta['limits'],'errors':errors});print(json.dumps({'passed':True,'canvas':len(checks),'play_pause':len(playchecks)}))
if __name__=='__main__':main()
