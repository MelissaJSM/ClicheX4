"""Validate the final handoff locations and local browser without repeating art tests."""
from pathlib import Path
import hashlib,json,re,sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=ROOT/'out/sprite_style_unification_20261107/final'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(D/'DELIVERY.json');idx=read(D/'SPRITE_INDEX.json');album=D/'ALL_SPRITES_CURRENT.html'
assert sha(album)==r['album_sha256']==read(D/'album_browser_checks.json')['html_sha256']
assert sha(D/'SPRITE_INDEX.json')==r['sprite_index_sha256']
assert len(idx['records'])==4510 and len(idx['partial_layers'])==2736
paths=[]
for f in idx['records']+idx['partial_layers']:
 p=(D/f['path']).resolve();assert p.is_relative_to(D.resolve())and p.is_file();assert sha(p)==f['sha256'];paths.append(p)
assert len(set(paths))==7246
for project,b in r['builds'].items():
 p=read(ROOT/b['pointer']);assert p['sha256']==b['sha256'] and p['cue']==b['cue']and p['implementation_complete']and not p['user_accepted']
 assert sha(ROOT/b['pointer'])==b['pointer_after_sha256']and sha(ROOT/b['backup'])==b['pointer_before_sha256']
 assert sha(ROOT/b['cue'])==b['cue_sha256']
links=[]
for name in('docs/STATUS.md','docs/SPRITE_REMAINING_WORK.md','docs/SPRITE_FINAL_HANDOFF_20261108.md','out/sprite_style_unification_20261107/final/README.md'):
 p=ROOT/name
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text('utf8')):
  if '://'in target or target.startswith('#'):continue
  dest=(p.parent/unquote(target.split('#')[0])).resolve();assert dest.exists(),(name,target);links.append([name,target])
errors=[];remote=[];tabs=[]
with sync_playwright()as pw:
 browser=pw.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':1400,'height':1000});page.context.set_offline(True)
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda q:remote.append(q.url)if not q.url.startswith(('file:','data:','blob:'))else None)
 page.goto(album.as_uri(),wait_until='load');page.wait_for_function('typeof DATA!=="undefined"&&DATA.length===4')
 for c in('riko','shibuki','nana','rin'):
  page.locator(f'#characters button[data-id="{c}"]').dispatch_event('click');page.wait_for_function('(id)=>char.id===id',arg=c);n=page.locator('#cards .card').count();assert n>0;tabs.append({'character':c,'visible_cards':n})
 assert page.evaluate('DATA.reduce((n,c)=>n+c.frames.length-c.partial.length,0)')==4510
 assert page.evaluate('DATA.reduce((n,c)=>n+c.revised_count,0)')==3077
 browser.close()
assert not errors and not remote
proof={'passed':True,'exported_png_sha256_checks':len(paths),'local_links_checked':len(links),'pointers_match_delivery':True,'prior_pointers_backed_up':True,'copied_album_hash_matches_verified_v38':True,'browser_tabs':tabs,'browser_errors':errors,'remote_requests':remote,'actual_gameplay_this_check':False,'new_art_test':False,'links':links}
(D/'HANDOFF_CHECKS.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({k:v for k,v in proof.items()if k!='links'}))
