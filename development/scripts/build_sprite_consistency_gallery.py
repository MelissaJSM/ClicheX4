"""Build a self-contained local review index from authenticated sprite exports."""
import json
import os
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out/sprite_consistency_20261105'
NAMES={'riko':'유즈하 리코','shibuki':'텐코 시부키','nana':'하나코 나나','rin':'아오쿠모 린'}
IMAGE_BOUNDS={}

def image_bounds(relative):
    if relative not in IMAGE_BOUNDS:
        with Image.open(OUT/relative) as image:
            if image.size!=(384,384):
                raise ValueError('Unexpected native canvas: '+relative)
            box=image.convert('RGBA').getchannel('A').getbbox()
            IMAGE_BOUNDS[relative]=[v-160 for v in box] if box else None
    return IMAGE_BOUNDS[relative]

def review_link(path):
    target=(ROOT/path).resolve()
    if not target.is_relative_to(ROOT) or not target.is_file():
        raise ValueError('Invalid review link: '+str(path))
    return Path(os.path.relpath(target,OUT)).as_posix()

def normalized(name):
    folder=OUT/name; m=json.loads((folder/'manifest.json').read_text('utf8'))
    def rel(p):
        return (ROOT/p).relative_to(OUT).as_posix() if p.startswith('out/') else f'{name}/{p}'
    frames=[];forms=[]
    if isinstance(m.get('variants'),dict):
        for form,v in m['variants'].items():
            forms.append({'id':form,'label':{'normal':'일반','black':'블랙 변형'}.get(form,form),'idle':f'{name}/{v["idle"]}'})
            for q in m['frames']:
                p=q.get('images',{}).get(form)
                if not p:continue
                frames.append({'id':f'{form}:{q["id"]}','form':form,'ref':q.get('frame'),
                  'bank':q.get('graphics_bank'),'group':q.get('group','unclassified'),
                  'status':q.get('render_status',''),'path':f'{name}/{p}',
                  'bbox':q.get('metrics',{}).get('bbox'),'animation_ids':list({a['id'] for a in q.get('animation_refs',[])})})
    else:
        for f in m['forms']:
            forms.append({'id':f['id'],'label':f.get('label',f['id']),'idle':rel(f['idle_path'])})
        for q in m['frames']:
            if not q.get('path'):continue
            frames.append({**q,'path':rel(q['path'])})
        known={f['id'] for f in forms}
        for form in dict.fromkeys(q['form'] for q in frames):
            if form not in known:
                forms.append({'id':form,'label':{'capsule_fourth':'포스 캡슐 잔상','capsule_ultimate':'얼티밋 캡슐 잔상'}.get(form,form),'idle':forms[0]['idle']})
    supp=json.loads((folder/'supplementary/manifest.json').read_text('utf8'))
    for group,label in [('selection','선택 화면'),('save','저장 화면')]:
        qs=[q for q in supp['frames'] if q['kind']==group]
        if not qs:continue
        forms.append({'id':group,'label':label,'idle':forms[0]['idle']})
        for q in qs:frames.append({'id':q['id'],'form':group,'ref':q.get('frame'),
          'bank':q.get('bank'),'group':group,'path':f'{name}/supplementary/{q["image"]}','status':'static UI reconstruction'})
    for q in frames:
        if not (OUT/q['path']).is_file():raise ValueError('Missing frame '+q['path'])
        q['bbox']=image_bounds(q['path'])
    for f in forms:
        if not (OUT/f['idle']).is_file():raise ValueError('Missing idle '+f['idle'])
        f['idle_bbox']=image_bounds(f['idle'])
    sheets=[p.relative_to(OUT).as_posix() for p in folder.rglob('*.png') if 'sheets' in p.parts or 'sheet' in p.name or 'compare' in p.name]
    revision=OUT/'revised'/name/'mapping.json'
    changes=json.loads(revision.read_text('utf8')) if revision.exists() else {'frames':{}}
    unknown=set(changes.get('frames',{}))-{q['id'] for q in frames}
    if unknown:raise ValueError('Revision IDs missing from baseline: '+str(sorted(unknown)))
    for q in frames:
        revised=changes.get('frames',{}).get(q['id'])
        if revised:
            q['revised_path']=(ROOT/revised).relative_to(OUT).as_posix()
            if not (OUT/q['revised_path']).is_file():raise ValueError('Missing revision '+revised)
            q['revised_bbox']=image_bounds(q['revised_path'])
    for sheet in [*changes.get('sheets',[]),*changes.get('comparison_sheets',[])]:
        path=sheet['path'] if isinstance(sheet,dict) else sheet
        path=review_link(path) if path.startswith(('out/','work/','docs/')) else path
        if not (OUT/path).is_file():raise ValueError('Missing revision sheet '+path)
        sheets.append(path)
    resources=[]
    def resource(label,path):
        if (ROOT/path).is_file():resources.append({'label':label,'path':review_link(path)})
    resource('전체 통일화 보고서','docs/SPRITE_CONSISTENCY_REVIEW.md')
    resource('추출 범위 독립 감사','work/sprite_consistency_20261105/coverage/REPORT.md')
    resource('이 캐릭터 검토 보고서',f'out/sprite_consistency_20261105/{name}/report.json')
    resource('수정본 매핑',f'out/sprite_consistency_20261105/revised/{name}/mapping.json')
    for label,path in changes.get('reports',{}).items():resource(label,path)
    if name=='nana' and changes.get('partial_armor_changes'):
        resource('부분 아머 160조합 보존·교정 근거','work/sprite_consistency_20261105/x/nana_parts_fix/prepared_v2/proposal.json')
        resource('부분 아머 전후 비교','work/sprite_consistency_20261105/x/nana_parts_fix/comparison.png')
    sheets=list(dict.fromkeys(sheets))
    return {'id':name,'label':NAMES[name],'source':m.get('source',{}),'forms':forms,'frames':frames,'sheets':sheets,
            'revisions':changes,'resources':resources,
            'animations':m.get('animations',[]),'manifest':f'{name}/manifest.json'}

PAGE=r'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cliché X4 스프라이트 통일화 작업판</title>
<style>
:root{color-scheme:dark;--bg:#242d3b;--cell:322px}*{box-sizing:border-box}
body{margin:0;background:#121923;color:#e5ebf4;font:15px 'Malgun Gothic',sans-serif}
header{padding:24px 28px 12px}h1{font-size:24px;margin:0 0 12px}h2{font-size:18px}h3{font-size:15px;margin:4px 0 8px}
p{line-height:1.65;max-width:1000px;color:#b9c7d7}a{color:#a4d7ff}button,select,input{font:inherit}
button,select{background:#29384b;color:inherit;border:1px solid #506074;border-radius:5px;padding:8px;cursor:pointer}
button:disabled{opacity:.45;cursor:default}button.active{background:#407f83}
.toolbar{position:sticky;top:0;z-index:2;background:#15202ef5;padding:12px 28px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.toolbar label{white-space:nowrap}.layout{display:grid;grid-template-columns:330px minmax(0,1fr);gap:20px;padding:20px 28px}
aside{position:sticky;top:140px;align-self:start;min-width:0}section{min-width:0}
.canvas-scroll{overflow:auto;max-width:100%}canvas{image-rendering:pixelated;max-width:none;flex-shrink:0;background:var(--bg);border:1px solid #43506a}
#cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(var(--cell),1fr));gap:10px;overflow:auto}
.card{background:#1b2635;border:1px solid #38465c;border-radius:5px;padding:8px;overflow:auto}
.card.changed{border-color:#62b6a9}.card.selected{outline:2px solid #bbdfeb;outline-offset:-2px}
.card canvas{display:block;margin:auto}.card small{display:block;overflow-wrap:anywhere;color:#bac8d8;padding:6px 0}
.card button{font-size:12px;padding:4px}.badge{color:#8ee4cf}.paging{display:flex;justify-content:center;gap:15px;padding:18px}
#detail{margin:10px 0;color:#b9c7d7;line-height:1.5;overflow-wrap:anywhere}.warn{color:#f8ce86}
summary{cursor:pointer;padding:10px}details img{max-width:100%;image-rendering:pixelated}footer{padding:24px}
#revisionPanel{border:1px solid #43506a;background:#182433;margin:0 0 18px;padding:8px}
.revision-pair{display:flex;gap:18px;overflow:auto;padding:4px}.revision-pair>div{flex:0 0 auto}
#revisionNote{margin:4px 8px 8px}.empty{padding:30px;border:1px dashed #53677d;color:#b9c7d7}
#error{color:#ffb5b5;padding:0 28px}small{line-height:1.5}
#resources{padding:12px 28px;display:flex;gap:8px 20px;flex-wrap:wrap;background:#182433}
#revisionSummary{padding:0 28px;margin:12px 0;color:#b9c7d7}
@media(max-width:800px){.layout{grid-template-columns:minmax(0,1fr)}aside{position:static}header,.toolbar,.layout{padding:16px}}
</style>
<header><h1>Cliché X4 · 스프라이트 통일화 작업판</h1>
<p>최신 적용 BIN에서 추출한 도트를 캐릭터·의상·동작별로 모았습니다. 대기와 동작, 수정 전·후를 같은 원점과 정수 배율로 비교합니다. 등장·승리·귀환·특수기·탑승·선택·저장 화면도 포함합니다.</p>
<p class="warn">정적 복원과 수정 후보를 보는 작업판입니다. 게임 실행 영상이나 모든 프레임의 수정 완료를 뜻하지 않습니다. 웅크린 자세를 서 있는 자세 높이로 늘리지 않습니다. 부분 갱신·별도 효과의 색상과 타이밍은 각 manifest의 제약을 확인해 주세요.</p></header>
<div class="toolbar"><span id="characters"></span><select id="form" aria-label="의상"></select><select id="group" aria-label="동작"></select>
<label><input id="showRevised" type="checkbox" checked>수정본 보기</label><label><input id="changedOnly" type="checkbox">변경 프레임만</label>
<label>배율 <select id="zoom"><option>1</option><option>2</option><option selected>3</option><option>4</option></select></label>
<label><input id="flip" type="checkbox">좌우 반전</label><label><input id="guides" type="checkbox" checked>기준선</label>
<label>배경 <input id="background" type="color" value="#242d3b"></label></div>
<div id="error" role="status"></div>
<nav id="resources" aria-label="검토 근거"></nav><p id="revisionSummary"></p>
<main class="layout"><aside><h2 id="idleTitle">대기 기준</h2><div class="canvas-scroll"><canvas id="idle"></canvas></div>
<p id="count"></p><a id="manifest">좌표·팔레트·참조 근거</a><div id="detail">프레임을 선택해 비교하세요.</div>
<div class="canvas-scroll"><canvas id="compare"></canvas></div><p><button id="blink">대기 ↔ 선택 비교</button></p>
<small>검수용으로 번갈아 표시합니다. 게임 애니메이션 속도가 아닙니다.</small></aside>
<section><details id="revisionPanel" open><summary>선택한 프레임 · 수정 전 / 수정 후</summary><p id="revisionNote"></p>
<div class="revision-pair"><div><h3>수정 전</h3><canvas id="before"></canvas><p><a id="beforePNG" target="_blank">원본 크기 PNG</a></p></div>
<div><h3 id="afterTitle">수정 후</h3><canvas id="after"></canvas><p><a id="afterPNG" target="_blank">원본 크기 PNG</a></p></div></div></details>
<div id="cards"></div><div class="paging"><button id="prev">이전</button><span id="page"></span><button id="next">다음</button></div>
<details><summary>한눈에 보는 전체 비교 시트</summary><div id="sheets"></div></details></section></main>
<footer>게임 데이터·저장 파일을 수정하지 않는 로컬 작업판. 개별 PNG는 투명 배경 384×384, 원점 (160,160). 캔버스는 1·2·3·4배 정수배이며 공간이 좁으면 스크롤합니다. 프레임마다 크기나 원점을 자동으로 바꾸지 않습니다.</footer>
<script>
const DATA=__DATA__;
const $=id=>document.getElementById(id),cache=new Map();
let char=DATA[0],page=0,chosen=null,timer=null,toggle=false,subset=[],windowBox=[-45,-50,55,40];
function pic(path){
  if(!cache.has(path)){const image=new Image();image.src=path;cache.set(path,image)}
  return cache.get(path);
}
function selectedPath(frame){return $('showRevised').checked&&frame.revised_path?frame.revised_path:frame.path}
function draw(cv,path,scale=+$('zoom').value){
  const [x,y,r,b]=windowBox,w=r-x,h=b-y,flipped=$('flip').checked,guides=$('guides').checked;
  const token=(cv._drawToken||0)+1;cv._drawToken=token;
  cv.width=w*scale;cv.height=h*scale;
  cv.dataset.path=path||'';cv.dataset.loaded='false';cv.dataset.scale=scale;cv.dataset.viewport=JSON.stringify(windowBox);
  const ctx=cv.getContext('2d');ctx.imageSmoothingEnabled=false;
  ctx.fillStyle=$('background').value;ctx.fillRect(0,0,cv.width,cv.height);
  if(!path)return;
  const image=pic(path),go=()=>{
    if(cv._drawToken!==token)return;
    ctx.save();if(flipped){ctx.translate(cv.width,0);ctx.scale(-1,1)}
    ctx.drawImage(image,160+x,160+y,w,h,0,0,w*scale,h*scale);ctx.restore();
    if(guides){ctx.strokeStyle='#7896ad66';ctx.lineWidth=1;ctx.beginPath();const gx=(flipped?r:-x)*scale;
      ctx.moveTo(gx,0);ctx.lineTo(gx,cv.height);ctx.moveTo(0,-y*scale);ctx.lineTo(cv.width,-y*scale);ctx.stroke()}
    cv.dataset.loaded='true';
  };
  if(image.complete&&image.naturalWidth)go();
  else{image.addEventListener('load',go,{once:true});image.addEventListener('error',()=>{
    if(cv._drawToken===token){cv.dataset.loaded='error';$('error').textContent='이미지를 읽지 못했습니다: '+path}
  },{once:true})}
}
function stopBlink(){if(timer)clearInterval(timer);timer=null;toggle=false;$('blink').textContent='대기 ↔ 선택 비교'}
function selectCharacter(id){
  stopBlink();char=DATA.find(c=>c.id===id);
  $('form').replaceChildren(...char.forms.map(f=>new Option(f.label,f.id)));
  document.querySelectorAll('#characters button').forEach(b=>b.classList.toggle('active',b.dataset.id===id));
  $('manifest').href=char.manifest;changeForm();renderSheets();
  $('resources').replaceChildren(...char.resources.map(r=>{const a=document.createElement('a');a.href=r.path;a.textContent=r.label;a.target='_blank';return a}));
  const revised=char.frames.filter(f=>f.revised_path).length,partial=char.revisions.partial_armor_changes?.length||0;
  $('revisionSummary').textContent='수집 이미지 '+char.frames.length+'개 · 수정 비교 '+revised+'개'+
    (partial?' · 부분 파츠 '+partial+'조합은 별도 전후 비교/근거 링크로 확인합니다. 기본·전체 장착 PNG가 같아도 부분 조합은 달라질 수 있습니다.':'');
}
function changeForm(){
  const groups=[...new Set(char.frames.filter(f=>f.form===$('form').value).map(f=>f.group))];
  $('group').replaceChildren(new Option('전체 동작',''),...groups.map(g=>new Option(g,g)));
  if(!$('changedOnly').checked&&groups.includes('idle'))$('group').value='idle';
  page=0;chosen=null;render();
}
function choose(frame){
  stopBlink();chosen=frame;updateChosen();
  document.querySelectorAll('.card').forEach(card=>card.classList.toggle('selected',card.dataset.id===chosen?.id));
}
function updateChosen(){
  $('blink').disabled=!chosen;$('revisionPanel').hidden=!chosen;
  if(!chosen){for(const id of ['compare','before','after'])draw($(id),null);$('detail').textContent='이 조건에 해당하는 프레임이 없습니다.';return}
  draw($('compare'),selectedPath(chosen));draw($('before'),chosen.path);draw($('after'),chosen.revised_path||chosen.path);
  $('detail').textContent=chosen.id+' · '+chosen.group+' · '+(chosen.revised_path?($('showRevised').checked?'수정본 표시':'수정 전 표시'):'변경 없음')+
    (chosen.animation_ids?.length?' · 애니메이션 '+chosen.animation_ids.join(', '):'');
  $('revisionNote').textContent=chosen.id+(chosen.revised_path?' — 두 이미지는 같은 배율·원점입니다.':' — 이 프레임은 변경하지 않았습니다. 양쪽 모두 기존 도트입니다.');
  $('afterTitle').textContent=chosen.revised_path?'수정 후':'현재 · 변경 없음';
  $('beforePNG').href=chosen.path;$('afterPNG').href=chosen.revised_path||chosen.path;
}
function renderSheets(){
  $('sheets').replaceChildren();
  for(const path of char.sheets){const d=document.createElement('details'),s=document.createElement('summary'),im=document.createElement('img');
    s.textContent=path;im.loading='lazy';im.src=path;d.append(s,im);$('sheets').append(d)}
}
function render(){
  stopBlink();$('error').textContent='';
  const form=char.forms.find(f=>f.id===$('form').value);
  const formFrames=char.frames.filter(f=>f.form===form.id);
  subset=formFrames.filter(f=>(!$('group').value||f.group===$('group').value)&&(!$('changedOnly').checked||f.revised_path));
  const boxes=[form.idle_bbox,...subset.flatMap(f=>[f.bbox,f.revised_bbox])].filter(b=>Array.isArray(b)&&b.length===4);
  windowBox=[Math.max(-160,Math.min(-45,...boxes.map(b=>b[0]-3))),Math.max(-160,Math.min(-50,...boxes.map(b=>b[1]-3))),
    Math.min(224,Math.max(55,...boxes.map(b=>b[2]+3))),Math.min(224,Math.max(40,...boxes.map(b=>b[3]+3)))];
  document.documentElement.style.setProperty('--cell',((windowBox[2]-windowBox[0])*(+$('zoom').value)+22)+'px');
  draw($('idle'),form.idle);$('idleTitle').textContent=char.label+' · 대기 기준';
  $('count').textContent=subset.length+'개 표시 / 이 의상 '+formFrames.length+'개 · 수정 '+formFrames.filter(f=>f.revised_path).length+'개';
  const pages=Math.max(1,Math.ceil(subset.length/48));page=Math.max(0,Math.min(page,pages-1));
  $('page').textContent=(page+1)+' / '+pages;$('prev').disabled=page===0;$('next').disabled=page===pages-1;
  const visible=subset.slice(page*48,page*48+48);
  if(!chosen||!visible.some(f=>f.id===chosen.id))chosen=visible[0]||null;
  $('cards').replaceChildren();
  for(const f of visible){
    const box=document.createElement('article');box.className='card'+(f.revised_path?' changed':'')+(chosen?.id===f.id?' selected':'');box.dataset.id=f.id;
    const c=document.createElement('canvas');draw(c,selectedPath(f));
    const small=document.createElement('small');small.textContent=f.id+' · '+f.group+(f.status?' · '+f.status:'');
    const btn=document.createElement('button');btn.textContent='이 프레임 비교';btn.onclick=()=>choose(f);
    const link=document.createElement('a');link.href=selectedPath(f);link.textContent=' PNG';link.target='_blank';
    box.append(c,small,btn,link);
    if(f.revised_path){const badge=document.createElement('small');badge.className='badge';badge.textContent=$('showRevised').checked?'수정본':'수정 전 · 수정본 있음';box.append(badge)}
    $('cards').append(box);
  }
  if(!visible.length){const empty=document.createElement('p');empty.className='empty';empty.textContent='이 조건에 해당하는 프레임이 없습니다. 변경 프레임 필터나 동작 선택을 바꿔 주세요.';$('cards').append(empty)}
  updateChosen();
}
for(const c of DATA){const b=document.createElement('button');b.textContent=c.label;b.dataset.id=c.id;b.onclick=()=>selectCharacter(c.id);$('characters').append(b)}
$('form').onchange=changeForm;$('group').onchange=()=>{page=0;chosen=null;render()};
['zoom','flip','guides','background','showRevised'].forEach(id=>$(id).onchange=render);
$('changedOnly').onchange=()=>{if($('changedOnly').checked)$('group').value='';page=0;chosen=null;render()};
$('prev').onclick=()=>{page--;render()};$('next').onclick=()=>{page++;render()};
$('blink').onclick=()=>{
  if(timer){stopBlink();updateChosen();return}if(!chosen)return;
  const idle=char.forms.find(f=>f.id===$('form').value).idle;
  $('blink').textContent='비교 멈추기';timer=setInterval(()=>{toggle=!toggle;draw($('compare'),toggle?idle:selectedPath(chosen))},650);
};
selectCharacter(char.id);
</script></html>
'''

def main():
    data=[normalized(name) for name in NAMES]
    payload=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
    (OUT/'index.html').write_text(PAGE.replace('__DATA__',payload),'utf8')
    (OUT/'gallery_manifest.json').write_text(json.dumps({'characters':[{k:v for k,v in d.items() if k not in ('frames','animations','sheets')} for d in data],
        'image_references':{d['id']:len(d['frames']) for d in data},
        'revised_references':{d['id']:sum(bool(f.get('revised_path')) for f in d['frames']) for d in data},
        'validated_native_canvases':len(IMAGE_BOUNDS),'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({d['id']:len(d['frames']) for d in data}))

if __name__=='__main__':main()
