from pathlib import Path
import hashlib,json
from playwright.sync_api import sync_playwright
O=Path(__file__).parent/'final_endpoint_audit01'
p=O/'ZERO_UI_HQ_SUPPLEMENT.html'
errors=[];external=[]
with sync_playwright() as pw:
    b=pw.chromium.launch(channel='msedge',headless=True)
    c=b.new_context(offline=True,viewport={'width':1440,'height':1000})
    page=c.new_page()
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:external.append(r.url) if not r.url.startswith(('file:','data:')) else None)
    page.goto(p.resolve().as_uri())
    page.wait_for_function('document.images.length===8 && [...document.images].every(i=>i.complete && i.naturalWidth>0)')
    images=page.evaluate('''[...document.images].map(i=>({alt:i.alt,width:i.width,naturalWidth:i.naturalWidth,height:i.height,naturalHeight:i.naturalHeight,embedded:i.src.startsWith('data:image/png;base64,'),pixelated:getComputedStyle(i).imageRendering==='pixelated'}))''')
    assert all(v['width']==v['naturalWidth'] and v['height']==v['naturalHeight'] and v['embedded'] and v['pixelated'] for v in images)
    page.screenshot(path=str(O/'browser_top.png'))
    page.locator('nav a[href="#rin"]').click()
    assert page.evaluate('location.hash')=='#rin'
    page.screenshot(path=str(O/'browser_rin.png'))
    assert not errors and not external
    b.close()
r={'passed':True,'html_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'offline':True,'embedded_pngs':8,'unscaled_integer_sheet_pixels':True,'images':images,'page_errors':errors,'external_requests':external,'hash_navigation_checked':'rin','game_access':False}
(O/'browser_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'images':8,'html_sha256':r['html_sha256']}))
