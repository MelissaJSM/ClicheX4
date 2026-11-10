"""오프라인 원순서 검토기의 호출별 픽셀/말단유지/실시간 재생을 검사한다."""
from pathlib import Path
import json,base64,io,sys
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
from native_pose_pack import need,sha,write
D=H/'ultimate_ladder_shot_sequence01'
def main():
    need(not(D/'browser_verification.json').exists(),'Fresh verification');errors=[];external=[];rows=[];screens=[]
    with sync_playwright()as pw:
        b=pw.chromium.launch(channel='msedge',headless=True);ctx=b.new_context(offline=True,viewport={'width':1100,'height':720});p=ctx.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:external.append(r.url)if not r.url.startswith(('file:','data:'))else None);p.goto((D/'REVIEW.html').resolve().as_uri());p.wait_for_function('window.review && review.ready()')
        for aid,initial in[(92,None),(93,8),(93,17)]:
            if initial is not None:p.locator('#initial').fill(str(initial))
            p.evaluate('(id)=>review.reset(id)',aid);hist=[];total=20 if aid==92 else initial+8
            for call in range(total+1):
                if call:p.evaluate('review.step()')
                state=p.evaluate('review.state()');expected=150 if (call<5 or call>=8) else 155
                if aid==93:expected=150 if call<initial or call>=initial+4 else 155
                need(state['ref']==expected,f'Wrong order {aid}/{call}');encoded=p.evaluate("c.toDataURL('image/png')").split(',',1)[1];actual=np.array(Image.open(io.BytesIO(base64.b64decode(encoded))).convert('RGBA'))
                for x,form in[(0,'before'),(64,'after')]:want=np.array(Image.open(D/f'{form}_{expected}_native.png').convert('RGBA'));need(np.array_equal(actual[:,x:x+64],want),'Canvas differs')
                hist.append(state)
                if aid==92 and call in(0,5,8):
                    q=D/f'browser_call_{call:02}.png';p.screenshot(path=str(q));screens.append({'path':q.relative_to(H.parents[2]).as_posix(),'sha256':sha(q.read_bytes())})
            need(hist[-1]['holding']and not hist[-1]['playing'],'Terminal not held');rows.append({'id':aid,'initial_calls_assumption':initial,'calls_inspected':len(hist),'trace':hist,'all_native_pixels_exact':True})
        p.evaluate('review.reset(92)');p.locator('#play').click();p.wait_for_function('review.state().holding',timeout=4000)
        # 마지막 호출은 원말단 프레임 유지이며 파일 시작으로 자동 되감지 않는다.
        terminal=p.evaluate('review.state()');need(terminal['holding']and terminal['ref']==150,'Timed playback terminal');p.wait_for_timeout(120);need(p.evaluate('review.state()')==terminal,'Terminal advanced');b.close()
    need(not errors and not external,'Browser errors/network');write(D/'browser_verification.json',{'passed':True,'html_sha256':sha((D/'REVIEW.html').read_bytes()),'offline':True,'network_requests':external,'errors':errors,'cases':rows,'timed_playback_terminal':terminal,'screenshots':screens,'scope':'원표92 및93의 가정 초기시간8/17에 대해 실제 canvas 표시와 정지 상태 검사. 60calls/s는 검토 가정이며 실기 시간 검증 아님.','continuous_animation_actually_watched_by_model':False});print(json.dumps({'passed':True,'native_canvas_checks':sum(r['calls_inspected']for r in rows)*2,'screens':len(screens)}))
if __name__=='__main__':main()
