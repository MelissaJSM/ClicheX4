"""원표12와 제트5의 독립호출·PNG·canvas·재생정지를 검사한다."""
from pathlib import Path
import sys,json,io,base64
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
    d=H/'hover_ultimate_sequence01';need(not(d/'browser_verification.json').exists(),'새 검사');r=json.loads((d/'report.json').read_text('utf8'));expected={n:np.array(Image.open(d/n).convert('RGBA'))for n in r['native_pngs']};errors=[];network=[];traces=[];checks=0
    with sync_playwright()as pw:
        b=pw.chromium.launch(channel='msedge',headless=True);c=b.new_context(offline=True,viewport={'width':1280,'height':900});p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda q:network.append(q.url)if not q.url.startswith(('file:','data:'))else None);p.goto((d/'REVIEW.html').resolve().as_uri());p.wait_for_function('window.review&&review.ready()')
        for name,case in r['cases'].items():
            steps=case['steps'];p.evaluate('id=>review.select(id)',name);pos=elapsed=0;trace=[];calls=120 if case['kind']=='player' else 12
            for call in range(calls):
                if call:
                    elapsed+=1
                    if elapsed>=steps[pos]['duration']:pos+=steps[pos]['relative'];elapsed=0
                    p.evaluate('review.step()')
                state=p.evaluate('review.state()');need((state['id'],state['pos'],state['elapsed'],state['ref'])==(name,pos,elapsed,steps[pos]['frame']),'원순서/호출 불일치');actual=np.array(Image.open(io.BytesIO(base64.b64decode(p.evaluate("canvas.toDataURL('image/png')").split(',',1)[1]))).convert('RGBA'))
                for i,n in enumerate(steps[pos]['images']):need(np.array_equal(actual[:,i*192:(i+1)*192],expected[n]),'canvas RGBA 불일치');checks+=1
                trace.append(state)
            traces.append({'case':name,'calls':calls,'trace':trace})
        p.evaluate('review.reset()');p.locator('#play').click();p.wait_for_function('review.state().total>=5');p.locator('#play').click();paused=p.evaluate('review.state()');p.wait_for_timeout(120);need(p.evaluate('review.state()')==paused and not paused['playing'],'정지 오류');b.close()
    need(not errors and not network,'외부요청/오류');write(d/'browser_verification.json',{'passed':True,'html_sha256':sha((d/'REVIEW.html').read_bytes()),'native_table_report_sha256':sha((d/'report.json').read_bytes()),'source_script_sha256':sha(Path(__file__).read_bytes()),'offline':True,'cases':len(traces),'calls':sum(v['calls']for v in traces),'canvas_checks':checks,'traces':traces,'timed_play_pause':paused,'errors':errors,'external_requests':network,'runtime_verified':False,'scope':'원표12의각120호출/제트5의각12호출과canvas3000. 독립상대분기·PNG·재생정지만 검사하며 실제호버전환/총탄이동/상태조건/효과색/물리실행과 구분.'});print(json.dumps({'passed':True,'cases':len(traces),'canvas_checks':checks}))
if __name__=='__main__':main()
