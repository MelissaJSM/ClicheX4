"""Headless canvas/timer checks; does not claim emulator or live art approval."""
from pathlib import Path
import sys,json,hashlib
from playwright.sync_api import sync_playwright
D=Path(__file__).resolve().parent;O=D/'native_cycle_v1'
def need(v,s):
 if not v:raise ValueError(s)
def main():
 m=json.loads((O/'manifest.json').read_text('utf8'));checks=0
 with sync_playwright()as p:
  browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':1660,'height':850},device_scale_factor=1);page.goto((O/'REVIEW.html').resolve().as_uri());page.evaluate('window.review.ready');page.evaluate('window.review.pause()')
  for q in m['frames']:
   page.evaluate('(n)=>window.review.selectRef(n)',q['ref'])
   actual=page.evaluate('Array.from({length:4},(_,i)=>Array.from(document.getElementById("small"+i).getContext("2d").getImageData(0,0,96,72).data))')
   for j,r in enumerate(actual):need(hashlib.sha256(bytes(r)).hexdigest()==q['canvas_rgba_sha256'][j],f'Native canvas {q["ref"]}/{j}');checks+=1
  cases=page.evaluate('Object.keys(window.review.cases)');timeline=[]
  for name in cases:
   page.evaluate('(s)=>{window.review.setCase(s);window.review.pause()}',name);seq=m['cases'][name]
   for step,q in enumerate(seq):
    s=page.evaluate('window.review.state()');need(s['index']==step and s['ref']==q['ref'],f'Step {name}/{step}');timeline.append([name,step,q['ref']]);page.evaluate('window.review.step()')
  page.evaluate('(s)=>{window.review.setCase(s);window.review.play()}',cases[0]);before=page.evaluate('window.review.state()');page.wait_for_timeout(450);running=page.evaluate('window.review.state()');need(running['draws']>before['draws']+2,'Continuous timer');page.evaluate('window.review.pause()');paused=page.evaluate('window.review.state()');page.wait_for_timeout(150);need(page.evaluate('window.review.state()')==paused,'Pause exact');page.screenshot(path=str(O/'headless_review.png'));browser.close()
 out={'passed':True,'candidate_arc_sha256':m['candidate_arc_sha256'],'html_sha256':m['html_sha256'],'native_canvas_checks':checks,'timeline_steps':len(timeline),'timeline':timeline,'play_draws_before':before['draws'],'play_draws_after':running['draws'],'pause_stable_ms':150,'runtime_verified':False,'scope':'headless 원본 시간표 그림 표시/재생/정지 검증. 실제 게임 입력·실기 및 동작 미술 수용이 아님.'};(O/'verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({k:out[k]for k in('passed','native_canvas_checks','timeline_steps')}))
if __name__=='__main__':main()
