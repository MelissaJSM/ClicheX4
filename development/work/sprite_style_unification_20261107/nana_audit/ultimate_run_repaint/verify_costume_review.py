"""제작 중 전후16몸체 검토판의 실제 canvas와 원표 재생·정지만 검사한다."""
from pathlib import Path
import json,hashlib
from playwright.sync_api import sync_playwright
D=Path(__file__).resolve().parent/'costume_review_v1'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 m=json.loads((D/'manifest.json').read_text('utf8'));assert sha((D/'REVIEW.html').read_bytes())==m['html_sha256'];checks=[];plays=[];errors=[]
 with sync_playwright()as p:
  b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page(viewport={'width':1250,'height':850},device_scale_factor=1);page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda r:r.abort()if r.request.url.startswith(('http:','https:'))else r.continue_());page.goto((D/'REVIEW.html').as_uri());page.evaluate('review.ready');page.evaluate('review.pause()')
  for q in m['frames']:
   page.evaluate('(n)=>review.selectRef(n)',q['ref']);values=page.evaluate('Array.from({length:4},(_,j)=>Array.from(document.getElementById("small"+j).getContext("2d").getImageData(0,0,96,96).data))')
   for j,v in enumerate(values):assert sha(bytes(v))==q['canvas_rgba_sha256'][j];checks.append([q['ref'],j])
  for k,seq in m['cases'].items():
   page.evaluate('(k)=>{review.setCase(k);review.pause()}',k);i=0
   for _ in range(len(seq)*2+1):
    assert page.evaluate('review.state().ref')==seq[i]['ref'];offset=seq[i]['step'];i=i+offset if offset else 0
    if i<0 or i>=len(seq):i=0
    page.evaluate('review.step()')
   page.evaluate('(k)=>{review.setCase(k);review.play()}',k);start=page.evaluate('review.state()');page.wait_for_timeout(700);end=page.evaluate('review.state()');assert end['draws']>start['draws'];page.evaluate('review.pause()');paused=page.evaluate('review.state()');page.wait_for_timeout(180);assert paused==page.evaluate('review.state()');plays.append({'case':k,'draw_delta':end['draws']-start['draws'],'paused_exact':True})
  for n in(0,1,3,25,27,31):page.evaluate('(n)=>review.selectRef(n)',n);page.screenshot(path=str(D/f'headless_{n:03}.png'))
  version=b.version;b.close()
 assert not errors
 r={'passed':True,'html_sha256':m['html_sha256'],'canvas_exact':checks,'canvas_count':len(checks),'original_table_relative_steps_two_cycles':True,'play_pause':plays,'browser':'Edge headless','version':version,'network_allowed':False,'page_errors':errors,'native_packed':False,'runtime_verified':False,'scope':'비사격16 후보의 전후의상과 원대기 canvas68개. 실제 EXE 표8/38 및 별도 수동 연결.60호출/초 가정이며 게임 이벤트/발사/물리는 실행하지 않았다.'};(D/'verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'canvas':len(checks),'play_pause':len(plays)}))
if __name__=='__main__':main()
