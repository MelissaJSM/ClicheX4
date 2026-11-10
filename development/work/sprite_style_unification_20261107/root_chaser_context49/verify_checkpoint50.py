from pathlib import Path
import hashlib,json
from playwright.sync_api import sync_playwright
O=Path(__file__).resolve().parent;ROOT=O.parents[2];out=ROOT/'out/sprite_style_unification_20261107/runtime_checkpoint50';p=out/'REVIEW.html';errors=[];requests=[]
with sync_playwright()as pw:
    browser=pw.chromium.launch(headless=True,channel='msedge');page=browser.new_page(viewport={'width':1280,'height':900});page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url));page.goto(p.as_uri());page.locator('details').evaluate_all('(xs)=>xs.forEach(x=>x.open=true)');page.locator('img').evaluate_all('(xs)=>xs.forEach(x=>x.loading="eager")');page.wait_for_function('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)');images=page.locator('img').count();links=page.locator('a').evaluate_all('(xs)=>xs.map(x=>x.href)');page.screenshot(path=str(out/'review_page_check.png'));browser.close()
assert images==21 and not errors and all(x.startswith('file:')for x in requests)
for target in links:
    from urllib.parse import unquote,urlparse
    path=Path(unquote(urlparse(target).path).lstrip('/'));assert path.is_file(),str(path)
r={'images_loaded':images,'local_links_checked':len(links),'page_errors':errors,'network_requests':False,'input_files_changed':False,'html_sha256':hashlib.sha256(p.read_bytes()).hexdigest()};(out/'browser_check.json').write_text(json.dumps(r,indent=2)+'\n','utf8')
s=O/'checkpoint50_summary.json';j=json.loads(s.read_text('utf8'));j['unchanged_art_boards_actually_viewed']=True;j['unchanged_art_observation']='기존 그림의 대기 대비 세부 묘사 차이가 남아 있어 미완료 분류 유지';j['browser_check']={'path':(out/'browser_check.json').relative_to(ROOT).as_posix(),'sha256':hashlib.sha256((out/'browser_check.json').read_bytes()).hexdigest()};s.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(r))
