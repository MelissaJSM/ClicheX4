"""오프라인 Edge에서 원시간표 재생·정지와 ARC 재추출 PNG의 canvas 일치를 검사한다."""
from pathlib import Path
import sys,json,hashlib
from playwright.sync_api import sync_playwright
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path.insert(0,str(D.parent/'native_restore'))
from preview_restore import write,digest,need
def main():
 d=D/'native_cycle_v1';meta=json.loads((d/'manifest.json').read_text('utf8'));checks=[];playchecks=[];errors=[]
 with sync_playwright()as p:
  browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':1850,'height':780},device_scale_factor=1)
  page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda route:route.abort()if route.request.url.startswith(('http:','https:'))else route.continue_())
  page.goto((d/'REVIEW.html').resolve().as_uri());page.evaluate('review.ready');page.evaluate('review.pause()')
  for q in meta['frames']:
   page.evaluate('(n)=>review.selectRef(n)',q['ref'])
   arrays=page.evaluate('()=>Array.from({length:6},(_,j)=>Array.from(document.getElementById("small"+j).getContext("2d").getImageData(0,0,96,80).data))')
   for j,values in enumerate(arrays):
    actual=hashlib.sha256(bytes(values)).hexdigest();need(actual==q['canvas_rgba_sha256'][j],f'Canvas {q["ref"]}/{j}');checks.append([q['ref'],j,actual])
  for name,seq in meta['cases'].items():
   page.evaluate('(k)=>{review.setCase(k);review.pause()}',name)
   expected_index=0
   for _ in range(len(seq)*2+1):
    state=page.evaluate('review.state()');need(state['ref']==seq[expected_index]['ref'],'Relative-step order')
    offset=seq[expected_index]['step'];expected_index=expected_index+offset if offset else 0
    if expected_index<0 or expected_index>=len(seq):expected_index=0
    page.evaluate('review.step()')
   page.evaluate('(k)=>{review.setCase(k);review.play()}',name);start=page.evaluate('review.state()');page.wait_for_timeout(650);end=page.evaluate('review.state()');need(end['draws']>start['draws'],'Playback did not progress')
   page.evaluate('review.pause()');paused=page.evaluate('review.state()');page.wait_for_timeout(180);still=page.evaluate('review.state()');need(paused==still,'Paused state changed');playchecks.append({'name':name,'draw_delta':end['draws']-start['draws'],'paused_exact':True})
  page.evaluate('review.selectRef(52)');page.screenshot(path=str(d/'headless_052.png'));page.evaluate('review.selectRef(39)');page.screenshot(path=str(d/'headless_039.png'));version=browser.version;browser.close()
 need(not errors,'Browser errors');write(d/'verification.json',{'passed':True,'html_sha256':digest(d/'REVIEW.html'),'candidate_arc_sha256':meta['candidate_arc_sha256'],'canvas_native_checks':len(checks),'all_frames_exact':checks,'relative_step_two_cycles':True,'play_pause_checks':playchecks,'browser':'Edge headless','version':version,'network_requests_permitted':False,'page_errors':errors,'runtime_verified':False,'scope':'실제 시간표 유지시간과 상대스텝을 사용하는 오프라인 canvas 검토. 이벤트 분기·충돌·입력·총알·게임 실기는 미실행.'});print(json.dumps({'passed':True,'canvas':len(checks),'play_pause':len(playchecks)}))
if __name__=='__main__':main()
