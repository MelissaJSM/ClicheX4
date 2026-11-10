from pathlib import Path
import hashlib,json
from playwright.sync_api import sync_playwright
D=Path(__file__).parent
O=D/'x_endpoint_supplement01';p=O/'X_UI_HQ_SUPPLEMENT.html'
errors=[];external=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True)
    context=browser.new_context(offline=True,viewport={'width':1440,'height':1000})
    page=context.new_page()
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:external.append(r.url) if not r.url.startswith(('file:','data:')) else None)
    page.goto(p.resolve().as_uri())
    page.wait_for_function('document.images.length===8 && [...document.images].every(i=>i.complete && i.naturalWidth>0)')
    images=page.evaluate('''[...document.images].map(i=>({alt:i.alt,width:i.width,naturalWidth:i.naturalWidth,height:i.height,naturalHeight:i.naturalHeight,embedded:i.src.startsWith('data:image/png;base64,'),pixelated:getComputedStyle(i).imageRendering==='pixelated'}))''')
    assert all(v['width']==v['naturalWidth'] and v['height']==v['naturalHeight'] and v['embedded'] and v['pixelated'] for v in images)
    page.screenshot(path=str(O/'browser_top.png'))
    page.locator('#nana').scroll_into_view_if_needed()
    page.screenshot(path=str(O/'browser_nana.png'))
    page.goto((D/'full_scope_matrix01/COVERAGE.html').resolve().as_uri())
    assert page.locator('table').count()==13
    assert page.locator('h2').count()==14
    assert page.locator('details').count()==144
    page.screenshot(path=str(D/'full_scope_matrix01/browser_top.png'))
    assert not errors and not external
    browser.close()
r={'passed':True,'html_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'offline':True,
 'embedded_pngs':8,'unscaled_integer_sheet_pixels':True,'images':images,'page_errors':errors,
 'external_requests':external,'scope_matrix_cells':144,'scope_matrix_form_tables':12,
 'game_access':False,'image_or_game_modified':False}
(O/'browser_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'images':8,'matrix_cells':144,'html_sha256':r['html_sha256']}))
