"""원표3/40의 각호출을 독립 시간선/실제 재추출 PNG와 대조한다."""
from pathlib import Path
import json,sys,base64,io
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
from native_pose_pack import need,sha,write
D=H/'ultimate_return_sequence01'
def timeline(sequence,total):
 steps=sequence['steps'];result=[];pos=0
 while len(result)<=total:
  s=steps[pos]
  if s['relative_step']==0:result.extend([s['frame']]*(total+1-len(result)));break
  result.extend([s['frame']]*s['duration_calls_uninterrupted']);pos+=s['relative_step']
 return result[:total+1]
def main():
 need(not(D/'browser_verification.json').exists(),'Fresh check');report=json.loads((D/'report.json').read_text('utf8'));errors=[];network=[];rows=[];screens=[];expected_images={name:np.array(Image.open(D/name).convert('RGBA'))for name in report['native_pngs']}
 with sync_playwright()as pw:
  browser=pw.chromium.launch(channel='msedge',headless=True);context=browser.new_context(offline=True,viewport={'width':1150,'height':850});p=context.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:network.append(r.url)if not r.url.startswith(('file:','data:'))else None);p.goto((D/'REVIEW.html').resolve().as_uri());p.wait_for_function('window.review && review.ready()')
  for sequence in report['sequences']:
   aid=sequence['id'];expected=timeline(sequence,40);p.evaluate('(id)=>review.reset(id)',aid);trace=[]
   for call,ref in enumerate(expected):
    if call:p.evaluate('review.step()')
    state=p.evaluate('review.state()');need(state['ref']==ref,f'Wrong native order {aid}/{call}');data=base64.b64decode(p.evaluate("canvas.toDataURL('image/png')").split(',',1)[1]);actual=np.array(Image.open(io.BytesIO(data)).convert('RGBA'))
    for x,form in ((0,'before'),(96,'after')):need(np.array_equal(actual[:,x:x+96],expected_images[f'{form}_{ref:03}_native.png']),f'Canvas raster mismatch {aid}/{call}/{form}')
    trace.append(state)
    if (aid,call)in ((3,3),(3,8),(40,12)):
     f=D/f'browser_id{aid}_call{call:03}.png';p.screenshot(path=str(f));screens.append({'path':f.name,'sha256':sha(f.read_bytes())})
   need(trace[-1]['holding']and not trace[-1]['playing'],'Self branch hold policy failed');rows.append({'id':aid,'calls_checked':len(trace),'canvas_forms_checked':len(trace)*2,'trace':trace})
  p.evaluate('review.reset(3)');p.locator('#play').click();p.wait_for_function('review.state().total >= 3');p.locator('#play').click();paused=p.evaluate('review.state()');need(not paused['playing']and paused['total']<15,'Pause did not stop before terminal');p.wait_for_timeout(120);need(p.evaluate('review.state()')==paused,'Paused state advanced');browser.close()
 need(not errors and not network,'Browser errors/network');write(D/'browser_verification.json',{'passed':True,'html_sha256':sha((D/'REVIEW.html').read_bytes()),'native_table_report_sha256':sha((D/'report.json').read_bytes()),'offline':True,'external_requests':network,'errors':errors,'cases':rows,'timed_play_then_pause_state':paused,'screenshots':screens,'scope':'원표3/40의 호출별 양폼 실제canvas 픽셀·자기분기 유지·재생/정지 검사.60호출/초는 표시검토 가정.실제게임/외부상태/물리/효과객체/소리 재현 아님.','continuous_video_actually_watched_by_model':False,'runtime_verified':False});print(json.dumps({'passed':True,'canvas_checks':sum(r['canvas_forms_checked']for r in rows),'screenshots':len(screens),'sha256':sha((D/'browser_verification.json').read_bytes())}))
if __name__=='__main__':main()
