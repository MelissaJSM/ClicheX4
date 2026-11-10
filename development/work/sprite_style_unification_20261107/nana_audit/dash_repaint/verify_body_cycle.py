"""로컬 검토 HTML의 후보 이미지/재생/정지 동작. 게임 실행 검사가 아니다."""
from pathlib import Path
import json,hashlib,base64,io
from PIL import Image
import numpy as np
from playwright.sync_api import sync_playwright
D=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    folder=D/'body_cycle_v1';proof=[];errors=[]
    with sync_playwright()as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':1100,'height':900});page.on('pageerror',lambda e:errors.append(str(e)));page.goto((folder/'REVIEW.html').as_uri());page.wait_for_function('Object.keys(frames).length===12 && document.querySelector("#status").textContent.includes("ref")');page.evaluate('run=false;index=0;elapsed=0;draw()')
        names=page.evaluate('Object.keys(cases)')
        for name in names:
            page.select_option('#which',label=name);length=page.evaluate('sequence.length');results=[]
            for k in range(length):
                actual=page.evaluate('''k=>{index=k;draw();return {ref:sequence[k].ref,calls:sequence[k].calls,pixels:[0,1].map(s=>Array.from(document.getElementById('small'+s).getContext('2d').getImageData(0,0,96,72).data)),uris:data[sequence[k].ref]}}''',k)
                for side in range(2):
                    expected=np.asarray(Image.open(io.BytesIO(base64.b64decode(actual['uris'][side].split(',')[1]))).convert('RGBA')).copy();expected[expected[:,:,3]==0,:3]=0;got=np.array(actual['pixels'][side],np.uint8).reshape(72,96,4);assert np.array_equal(got,expected),(name,k,side)
                results.append({'ref':actual['ref'],'calls':actual['calls'],'canvas_native_rgba_exact':True})
            proof.append({'name':name,'steps':results})
        page.select_option('#which',label=names[0]);page.select_option('#speed','1');page.evaluate('run=true;index=0;elapsed=0;draw()');page.wait_for_timeout(500);advance=page.evaluate('last>0 && run && elapsed>=0');page.click('#play');state=page.evaluate('({index,elapsed,run})');page.wait_for_timeout(100);assert page.evaluate('({index,elapsed,run})')==state
        page.click('#step');assert page.evaluate('index')==(state['index']+1)%3;page.screenshot(path=str(folder/'browser_review.png'),full_page=True);browser.close()
    assert not errors
    result={'passed':True,'html_sha256':sha((folder/'REVIEW.html').read_bytes()),'cases':proof,'native_pixel_exact_steps':sum(len(q['steps'])for q in proof),'animation_running':advance,'pause_and_step_verified':True,'console_errors':errors,'scope':'Headless 브라우저의 후보PNG/프레임순서/정지동작 검사. 실제 게임·새 ARC·미술수용 검사가 아니다.','clock_assumption':'60 calls/sec'};(folder/'browser_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'passed':True,'steps':result['native_pixel_exact_steps']}))
if __name__=='__main__':main()
