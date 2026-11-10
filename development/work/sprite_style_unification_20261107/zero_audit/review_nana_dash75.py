"""Read only sibling HTML, capture exact native browser frames for art review."""
from pathlib import Path
import json,hashlib,base64,io
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[3];O=Path(__file__).parent/'nana_dash75_review';O.mkdir(exist_ok=True)
P=ROOT/'work/sprite_style_unification_20261107/nana_audit/dash_repaint/body_cycle_v1/REVIEW.html'
errors=[];external=[];captures=[]
with sync_playwright() as p:
 browser=p.chromium.launch(channel='msedge',headless=True)
 context=browser.new_context(viewport={'width':1250,'height':970},device_scale_factor=1,offline=True)
 page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:external.append(r.url) if not r.url.startswith(('file:','data:','blob:')) else None)
 page.goto(P.as_uri(),wait_until='load');page.wait_for_function('Object.keys(frames).length===Object.keys(data).length&&frames[75]?.length===2');page.evaluate('run=false;speed.value="1";index=0;elapsed=0;draw()')
 sequence=page.evaluate('sequence');assert [v['ref'] for v in sequence]==[71,75,73]
 for i,q in enumerate(sequence):
  page.evaluate('(n)=>{index=n;draw()}',i)
  page.screenshot(path=str(O/f'frame_{q["ref"]:03}.png'))
  for side in(0,1):
   uri=page.locator(f'#small{side}').evaluate('c=>c.toDataURL("image/png")');im=Image.open(io.BytesIO(base64.b64decode(uri.split(',')[1]))).convert('RGBA');assert im.size==(96,72)
   im.save(O/f'{q["ref"]:03}_{side}.png');captures.append({'ref':q['ref'],'side':side,'canvas':[96,72],'smoothing':page.locator(f'#small{side}').evaluate('c=>c.getContext("2d").imageSmoothingEnabled')})
 context.close();browser.close()
sheet=Image.new('RGB',(2*768,3*(576+32)),(180,192,199));draw=ImageDraw.Draw(sheet)
for row,ref in enumerate((71,75,73)):
 for side in(0,1):
  im=Image.open(O/f'{ref:03}_{side}.png').convert('RGBA').resize((768,576),Image.Resampling.NEAREST);sheet.paste(im,(side*768,row*608+32),im);draw.text((side*768+8,row*608+8),f'{ref} '+('before'if side==0 else'new'),fill=(20,25,30))
sheet.save(O/'comparison_8x.png')
result={'source':str(P.relative_to(ROOT)),'source_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'headless_offline_edge':True,'errors':errors,'external_requests':external,'sequence':sequence,'captures':captures,'actual_gameplay':False,'art_review_pending':True}
(O/'capture.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');assert not errors and not external and all(not q['smoothing']for q in captures);print(json.dumps({'output':str(O),'errors':errors}))
