"""특수4의 실제 canvas와 원표 다섯 개를 오프라인으로 확인한다."""
from pathlib import Path
import sys,json,hashlib
from playwright.sync_api import sync_playwright
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path.insert(0,str(N/'native_restore'))
from preview_restore import write,digest,need
def main():
 d=D/'native_cycle_v1';meta=json.loads((d/'manifest.json').read_text('utf8'));html=d/'REVIEW.html';w,h=meta['canvas_size'];checks=[];playing=[];errors=[]
 with sync_playwright()as p:
  browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':1950,'height':1100},device_scale_factor=1);page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda route:route.abort()if route.request.url.startswith(('http:','https:'))else route.continue_());page.goto(html.resolve().as_uri());page.evaluate('review.ready');page.evaluate('review.pause()')
  for q in meta['frames']:
   page.evaluate('(n)=>review.selectRef(n)',q['ref']);arrays=page.evaluate('([w,h])=>Array.from({length:6},(_,j)=>Array.from(document.getElementById("small"+j).getContext("2d").getImageData(0,0,w,h).data))',[w,h])
   for j,v in enumerate(arrays):got=hashlib.sha256(bytes(v)).hexdigest();need(got==q['canvas_rgba_sha256'][j],f'Canvas{q["ref"]}/{j}');checks.append([q['ref'],j,got])
  for name,seq in meta['cases'].items():
   page.evaluate('(k)=>{review.setCase(k);review.pause()}',name);i=0
   for _ in range(len(seq)*2+1):
    need(page.evaluate('review.state()')['ref']==seq[i]['ref'],'Relative step');step=seq[i]['step'];i=i+step if step else 0
    if i<0 or i>=len(seq):i=0
    page.evaluate('review.step()')
   page.evaluate('(k)=>{review.setCase(k);review.play()}',name);before=page.evaluate('review.state()');page.wait_for_timeout(1800);after=page.evaluate('review.state()');need(after['draws']>before['draws'],'Playback');page.evaluate('review.pause()');paused=page.evaluate('review.state()');page.wait_for_timeout(180);need(paused==page.evaluate('review.state()'),'Pause');playing.append({'name':name,'draw_delta':after['draws']-before['draws'],'pause_exact':True})
  for n in (95,98):page.evaluate('(n)=>review.selectRef(n)',n);page.screenshot(path=str(d/f'headless_{n:03}.png'))
  version=browser.version;browser.close()
 need(not errors,'Page errors');write(d/'verification.json',{'passed':True,'html_sha256':digest(html),'candidate_arc_sha256':meta['candidate_arc_sha256'],'canvas_native_checks':len(checks),'all_frames_exact':checks,'relative_step_two_cycles':True,'play_pause_checks':playing,'browser':'Edge headless','version':version,'network_requests_permitted':False,'page_errors':errors,'runtime_verified':False,'scope':'원표95/96/97/104/105 오프라인 canvas 재생/정지.60호출/초 가정/원상대스텝이며 실제게임 물리·입력·caller 실행아님. 실제98발사원점 증명으로 세지 않는다.'});print(json.dumps({'passed':True,'canvas':len(checks),'play_pause':len(playing)}))
if __name__=='__main__':main()
