"""새BIN 재생판56스텝의 실제 브라우저 캔버스와 재생을 확인한다."""
from pathlib import Path
import json,hashlib,base64,io,sys
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from src.psx_disc import file_hash
D=ROOT/'out/sprite_style_unification_20261107/resumed51'
def main():
 meta=json.loads((D/'manifest.json').read_text('utf8'));assert file_hash(D/'REVIEW.html')==meta['html_sha256'];errors=[];network=[];checked=[];plays=[]
 with sync_playwright()as p:
  b=p.chromium.launch(channel='msedge',headless=True);c=b.new_context(offline=True,viewport={'width':1100,'height':800});page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:network.append(r.url)if not r.url.startswith(('file:','data:','blob:'))else None);page.goto((D/'REVIEW.html').as_uri());page.wait_for_function('window.ready===true');data=page.evaluate('DATA')
  for ci,case in enumerate(data):
   for si,s in enumerate(case['steps']):
    page.evaluate('([c,s])=>showFrame(c,s)',[ci,si]);actual=bytes(page.evaluate('Array.from(ctx.getImageData(0,0,512,256).data)'));src=Image.open(io.BytesIO(base64.b64decode(s['image'].split(',')[1]))).convert('RGBA');expected=np.array(src.resize((512,256),Image.Resampling.NEAREST));expected[expected[:,:,3]==0]=0;assert actual==expected.tobytes(),(case['id'],si);checked.append([case['id'],si,s['ref']])
   page.evaluate('c=>showFrame(c,0)',ci);page.locator('#play').click();page.wait_for_timeout(1800 if case['id']=='nana_93'else 180);shown=page.evaluate('window.shown');plays.append({'case':case['id'],'observed_step':shown['step'],'ref':shown['ref']});assert shown['step']!=0 or case['id']=='shibuki_2';page.evaluate('run=false')
  page.evaluate('showFrame(5,4)');page.screenshot(path=str(D/'browser.png'));version=b.version;b.close()
 assert not errors and not network
 report={'passed':True,'html_sha256':meta['html_sha256'],'manifest_sha256':file_hash(D/'manifest.json'),'browser':version,'canvas_steps_exact':len(checked),'form_images_exact':2*len(checked),'checks':checked,'play_checks':plays,'page_errors':errors,'network_requests':network,'gameplay_verified':False};(D/'browser_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'steps':len(checked),'play':len(plays)}))
if __name__=='__main__':main()
