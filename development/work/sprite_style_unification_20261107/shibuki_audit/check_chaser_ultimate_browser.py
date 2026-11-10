"""체이서 원표12개와 두폼 재추출canvas를 호출별 비교하는 오프라인 검사."""
from pathlib import Path
import sys,json,base64,io
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
D=H/'chaser_ultimate_sequence01'

def timeline(seq):
    result=[];pos=0
    while True:
        step=seq['steps'][pos]
        if step['relative_step']==0:
            result.extend([step['frame']]*6);return result
        result.extend([step['frame']]*step['duration_calls_uninterrupted']);pos+=step['relative_step']

def main():
    need(not (D/'browser_verification.json').exists(),'Fresh browser result')
    report=json.loads((D/'report.json').read_text('utf8'));errors=[];network=[];rows=[];screens=[]
    expected={name:np.array(Image.open(D/name).convert('RGBA')) for name in report['native_pngs']}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context(offline=True,viewport={'width':1240,'height':720});page=context.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:network.append(r.url) if not r.url.startswith(('file:','data:')) else None)
        page.goto((D/'REVIEW.html').resolve().as_uri());page.wait_for_function('window.review && review.ready()')
        for seq in report['sequences']:
            aid=seq['id'];page.evaluate('(id)=>review.reset(id)',aid);trace=[]
            for call,ref in enumerate(timeline(seq)):
                if call:page.evaluate('review.step()')
                state=page.evaluate('review.state()');need(state['ref']==ref,f'Order mismatch {aid}/{call}')
                blob=base64.b64decode(page.evaluate("canvas.toDataURL('image/png')").split(',',1)[1])
                actual=np.array(Image.open(io.BytesIO(blob)).convert('RGBA'))
                for i,form in enumerate(report['forms']):
                    need(np.array_equal(actual[:,i*96:(i+1)*96],expected[f'{form}_{ref:03}_native.png']),f'Canvas mismatch {aid}/{call}/{form}')
                trace.append(state)
                if (aid,call) in ((66,0),(66,2),(66,12),(75,0),(75,8),(75,12)):
                    p=D/f'browser_id{aid}_call{call:03}.png';page.screenshot(path=str(p));screens.append({'path':p.name,'sha256':sha(p.read_bytes())})
            need(trace[-1]['holding'] and not trace[-1]['playing'],'Terminal external-state hold failed')
            rows.append({'id':aid,'calls_checked':len(trace),'canvas_form_checks':len(trace)*2,'trace':trace})
        page.evaluate('review.reset(66)');page.locator('#play').click();page.wait_for_function('review.state().total >= 4')
        page.locator('#play').click();paused=page.evaluate('review.state()');need(not paused['playing'],'Pause failed')
        page.wait_for_timeout(120);need(page.evaluate('review.state()')==paused,'Pause advanced');browser.close()
    need(not errors and not network,'Browser error/network')
    write(D/'browser_verification.json',{'passed':True,'html_sha256':sha((D/'REVIEW.html').read_bytes()),
        'native_table_report_sha256':sha((D/'report.json').read_bytes()),'offline':True,'errors':errors,'external_requests':network,
        'cases':rows,'screenshots':screens,'timed_play_then_pause':paused,
        'scope':'실제원표12개의 호출별2폼canvas/원순서·끝점유지·재생정지 검사.60호출/초 가정이며 외부상태/차량객체/물리/음향/실기는 아님.',
        'continuous_video_actually_watched_by_model':False,'runtime_verified':False})
    print(json.dumps({'passed':True,'canvas_form_checks':sum(r['canvas_form_checks'] for r in rows),
        'sha256':sha((D/'browser_verification.json').read_bytes())}))

if __name__=='__main__':main()
