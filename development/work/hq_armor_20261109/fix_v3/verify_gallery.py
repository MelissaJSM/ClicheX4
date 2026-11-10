"""Check the offline review in an isolated, headless browser; never control ePSXe."""
import base64, hashlib, html, io, json, re, subprocess, sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];F=ROOT/'work/hq_armor_20261109/fix_v3'
OUT=ROOT/'out/illustration_review_20261109'
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from src.psx_disc import file_hash

source=OUT/'일러스트_모음집.html';text=source.read_text('utf8')
manifest=json.loads((OUT/'manifest.json').read_text('utf8'))
assert '/*PAYLOAD*/' not in text
data=json.loads(text.split('const data=',1)[1].split(', $=s=>',1)[0])
assert len(data['cards'])==80 and manifest['total_images']==572
for card in data['cards']:
    assert len(card['frames'])==len(card['labels'])==len(card['size'])==len(card['files'])
    for uri,size,name in zip(card['frames'],card['size'],card['files']):
        raw=base64.b64decode(uri.split(',',1)[1]);assert (OUT/name).read_bytes()==raw
        with Image.open(io.BytesIO(raw))as im:assert list(im.size)==size and im.mode=='RGBA'
assert not re.findall(r'(?:src|href)=["\']https?://',text)
# Confirm that the actual selected executables omit zero map words before
# dereferencing attributes, matching the corrected background preview helper.
instructions=[]
for ptr in data['sources']:
    game=(ROOT/ptr['cue']).with_suffix('.bin');assert file_hash(game)==ptr['sha256']
    exe=read_disc(game,['SLUS_005.61'])[0]['SLUS_005.61']
    b=exe[0x80026b98-0x80010000+2048:0x80026ba8-0x80010000+2048]
    assert b.hex()=='00004794000000003a00e01000000000',b.hex()
    instructions.append({'mode':ptr['mode'],'address':'0x80026B98','bytes':b.hex(),'behavior':'lhu a3; beqz a3 skips map word zero'})

test=r'''
<script>
(async()=>{
const results=[];function check(v,n){if(!v)throw Error(n);results.push(n)}
try{
check(document.querySelectorAll('.card').length===80,'all 80 cards');
const images=cards.flatMap(c=>c.frames).map(src=>{const i=new Image();i.src=src;return i});
$('#character').value='나나';$('#category').value='헌터베이스';render();
check(document.querySelectorAll('.card').length===18,'Nana HQ 18 states');
const card=cards.find(c=>c.char==='나나'&&c.category==='헌터베이스'&&c.state==='포스 풀세트');
check(Boolean(card),'full Force card exists');
let el=[...document.querySelectorAll('.card')].find(e=>e.querySelector('.badge').textContent.startsWith(card.id));
el.querySelector('.tools select').value='11';el.querySelector('.tools select').onchange();
check(el.querySelector('.caption').textContent.includes('12 / 12'),'last frame');
el.querySelectorAll('.tools button')[1].click();check(indices[card.id]===0,'frame wrap');
$('#zoom').value='3';render();
el=[...document.querySelectorAll('.card')].find(e=>e.querySelector('.badge').textContent.startsWith(card.id));
check(el.querySelector('.stage img').style.width==='480px','integer nearest scale');
const ta=el.querySelector('textarea');ta.value='test review note';ta.oninput();
check(JSON.parse(localStorage.getItem('cliche-illustrations-20261109'))[card.id]==='test review note','notes persist');
delete notes[card.id];save();
$('#character').value='리코';$('#category').value='타이틀·획득';render();
check(document.querySelectorAll('.card').length===1,'combined character and category filter');
check(document.querySelector('.tools select').options.length===3,'three source copies');
$('#character').value='전체';$('#category').value='전체';$('#zoom').value='2';render();
const output=document.createElement('pre');output.id='test-result';document.body.append(output);
const poll=setInterval(()=>{if(images.every(i=>i.complete&&i.naturalWidth>0)){clearInterval(poll);check(true,'all 572 embedded PNGs load');output.textContent=JSON.stringify({passed:true,checks:results})}},50);
}catch(e){const output=document.createElement('pre');output.id='test-result';output.textContent=JSON.stringify({passed:false,error:String(e),checks:results});document.body.append(output)}
})();
</script>
'''
testfile=F/'browser_test.html';testfile.write_text(text.replace('</html>',test+'</html>'),'utf8')
browser=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-win64/chrome-headless-shell.exe'
cmd=[str(browser),'--headless','--disable-gpu','--no-first-run','--disable-background-networking','--disable-component-update',
     '--user-data-dir='+str(F/'browser_profile'),'--window-size=1440,1100','--virtual-time-budget=6000',
     '--screenshot='+str(OUT/'gallery_browser.png'),'--dump-dom',testfile.as_uri()]
proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
(F/'browser_stderr.txt').write_bytes(proc.stderr)
dom=proc.stdout.decode('utf8',errors='replace');(F/'browser_dom.html').write_text(dom,'utf8');m=re.search(r'<pre id="test-result">(.+?)</pre>',dom,re.S)
assert m,proc.stderr.decode('utf8',errors='replace')[-1200:]
result=json.loads(html.unescape(m.group(1)));assert result['passed'],result
result.update(groups=80,images=572,embedded_images_equal_original_PNGs=True,network_assets=False,
              native_zero_map_skip=instructions,html_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              emulator_keys_sent=False)
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(result,ensure_ascii=True))
