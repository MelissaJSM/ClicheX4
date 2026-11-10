"""격리된 headless 브라우저에서 표 재생/정지와 모든 native canvas를 대조."""
from pathlib import Path
import sys,json,hashlib
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent/'body_cycle_v2'
def main():
 m=json.loads((D/'manifest.json').read_text('utf8'));checks=[];errors=[]
 with sync_playwright()as p:
  b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page(viewport={'width':1240,'height':700});page.on('pageerror',lambda e:errors.append(str(e)));page.goto((D/'REVIEW.html').as_uri());page.evaluate('window.review.ready');page.evaluate('review.pause()')
  for q in m['frames']:
   n=q['ref'];page.evaluate('(n)=>review.selectRef(n)',n)
   for j in range(3):
    data=page.evaluate('(j)=>Array.from(document.getElementById("small"+j).getContext("2d").getImageData(0,0,96,72).data)',j);h=hashlib.sha256(bytes(data)).hexdigest();assert h==q['hashes'][j],(n,j,h,q['hashes'][j]);checks.append([n,j,h])
  page.evaluate('review.setCase(Object.keys(review.cases)[3]);review.play()');before=page.evaluate('review.state()');page.wait_for_timeout(2700);after=page.evaluate('review.state()');assert after['draws']>before['draws']+10
  page.evaluate('review.pause()');paused=page.evaluate('review.state()');page.wait_for_timeout(200);assert page.evaluate('review.state()')==paused
  page.screenshot(path=str(D/'headless_paused.png'));b.close()
 assert not errors,errors
 result={'passed':True,'canvas_comparisons':len(checks),'checks':checks,'continuous_preview_advanced':after['draws']-before['draws'],'trace_during_run':after['trace'][len(before['trace']):],'pause_stable':True,'javascript_errors':errors,'scope':'Headless canvas pixels and running timeline verified. No game input, no physical movement and no actual gameplay art approval.','native_packed':False,'runtime_verified':False};(D/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'passed':True,'canvas_checks':len(checks),'advanced':result['continuous_preview_advanced']}))
if __name__=='__main__':main()
