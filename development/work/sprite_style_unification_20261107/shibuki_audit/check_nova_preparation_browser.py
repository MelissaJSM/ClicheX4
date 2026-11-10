"""원표106의100호출을 픽셀·상대분기로 검사. 게임 이벤트는 실행하지 않는다."""
from pathlib import Path
import sys,json,io,base64
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
    d=H/'nova_base_sequence01';need(not(d/'browser_verification.json').exists(),'새 검사');r=json.loads((d/'report.json').read_text('utf8'));steps=r['sequences'][0]['steps'];expected={n:np.array(Image.open(d/n).convert('RGBA'))for n in r['native_pngs']};errors=[];network=[];trace=[];pos=elapsed=0
    with sync_playwright()as pw:
        b=pw.chromium.launch(channel='msedge',headless=True);c=b.new_context(offline=True,viewport={'width':1280,'height':900});p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda q:network.append(q.url)if not q.url.startswith(('file:','data:'))else None);p.goto((d/'REVIEW.html').resolve().as_uri());p.wait_for_function('window.review&&review.ready()')
        for call in range(100):
            if call:
                elapsed+=1
                if elapsed>=steps[pos]['duration_calls_uninterrupted']:pos+=steps[pos]['relative_step'];elapsed=0
                p.evaluate('review.step()')
            state=p.evaluate('review.state()');ref=steps[pos]['frame'];need((state['pos'],state['elapsed'],state['ref'])==(pos,elapsed,ref),'원순서/호출 불일치');actual=np.array(Image.open(io.BytesIO(base64.b64decode(p.evaluate("canvas.toDataURL('image/png')").split(',',1)[1]))).convert('RGBA'))
            for i,form in enumerate(r['forms']):need(np.array_equal(actual[:,i*192:(i+1)*192],expected[f'{form}_{ref:03}_native.png']),'canvas RGBA 불일치')
            trace.append(state)
        p.evaluate('review.reset()');p.locator('#play').click();p.wait_for_function('review.state().total>=5');p.locator('#play').click();paused=p.evaluate('review.state()');p.wait_for_timeout(120);need(p.evaluate('review.state()')==paused and not paused['playing'],'정지 오류');b.close()
    need(not errors and not network,'외부요청/오류');write(d/'browser_verification.json',{'passed':True,'html_sha256':sha((d/'REVIEW.html').read_bytes()),'native_table_report_sha256':sha((d/'report.json').read_bytes()),'offline':True,'calls':100,'canvas_form_checks':200,'trace':trace,'timed_play_pause':paused,'errors':errors,'external_requests':network,'runtime_verified':False,'scope':'원표106의 상대분기·100호출·양폼canvas200·재생정지. 실제조건/노바이동/원래효과 이벤트 실행과 구분.'});print(json.dumps({'passed':True,'calls':100,'canvas_form_checks':200}))
if __name__=='__main__':main()
