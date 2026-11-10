"""Build a portable single HTML sprite album; game inputs and baseline exports stay read-only."""
import base64
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import build_sprite_consistency_gallery as gallery
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive, GROUPS, GROUP_NAMES
from src.psx_disc import file_hash

OUT=ROOT/'out/sprite_consistency_20261105'
WORK=ROOT/'work/sprite_consistency_20261105/zero/album'
PLAYBACK=ROOT/'work/sprite_consistency_20261105/playback/manifest.json'
EXPECTED={'ver_buki_riko':'5a57b31c7a4410d697183a01b2246a28344c847cefb331d27aad56135e7a924d',
          'ver_rin_nana':'de818d585fe1a4455d9b07551f3161b24357e3a1a2343d84102628a1fde55679'}
POOL={};PNG_HASHES={};RGBA_CACHE={};FILE_CACHE={}


def sha(data):return hashlib.sha256(data).hexdigest()


def embedded_json(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')


def pooled_png(data):
    digest=sha(data)
    if digest not in PNG_HASHES:
        key='i'+str(len(POOL));PNG_HASHES[digest]=key
        POOL[key]='data:image/png;base64,'+base64.b64encode(data).decode('ascii')
    return PNG_HASHES[digest]


def pooled_file(relative):
    path=(OUT/relative).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():raise ValueError('Invalid image path '+relative)
    if path not in FILE_CACHE:FILE_CACHE[path]=pooled_png(path.read_bytes())
    return FILE_CACHE[path]


def pooled_image(image):
    image=image.convert('RGBA');digest=sha(image.tobytes())
    if digest not in RGBA_CACHE:
        stream=io.BytesIO();image.save(stream,format='PNG',optimize=True)
        RGBA_CACHE[digest]=pooled_png(stream.getvalue())
    return RGBA_CACHE[digest]


def bounds(image):
    box=image.getchannel('A').getbbox()
    return [v-160 for v in box] if box else None


def latest_partial(character):
    mode,stem=('ver_buki_riko','shibuki_riko') if character=='shibuki' else ('ver_rin_nana','rin_nana')
    pointer=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'))
    source=ROOT/pointer['build']/(stem+'.bin')
    if pointer['sha256']!=EXPECTED[mode] or file_hash(source)!=EXPECTED[mode]:raise ValueError('Latest BIN mismatch')
    assets,_=read_disc(source,('PL00_U.ARC',));arc=Archive(assets['PL00_U.ARC']);frames=[];preserved=0
    for ref in range(237):
        group=next(k for k,values in GROUPS.items() if ref in values)
        frame={'id':f'partial_fourth_{ref:03}','form':'partial_fourth','ref':ref,'bank':0,'group':group,
               'label':GROUP_NAMES[group],'status':'rendered','layers':{},'bbox':None}
        try:
            union=np.zeros((384,384),bool)
            for name,pb,start in (('base',0,0),('legs',8,16),('head',5,16),('body',6,16),('arm1',7,16),('arm2',7,32)):
                indices,_=arc.layer(ref,pb);im=arc.rgba(indices,start)
                frame['layers'][name]=pooled_image(im);union|=np.asarray(im)[:,:,3]>0
            yy,xx=np.nonzero(union)
            if len(xx):frame['bbox']=[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)]
            else:frame['status']='blank'
            # Independent composition check against the established source renderer for all 32 choices.
            for arm in (1,2):
                for mask in range(16):
                    im=arc.rgba(arc.layer(ref,0)[0])
                    for bit,pb,start in ((8,8,16),(1,5,16),(4,7,32 if arm==2 else 16),(2,6,16)):
                        if mask&bit:im.alpha_composite(arc.rgba(arc.layer(ref,pb)[0],start))
                    assert im.tobytes()==arc.composite(ref,mask,arm)[0].tobytes()
                    preserved+=1
        except (ValueError,IndexError) as error:
            if ref not in (105,*range(175,183)):raise
            frame.update(status='unreconstructed',layers={},reason='이전 VRAM/예약 참조: 독립 몸체 복원 불가',bbox=None)
        frames.append(frame)
    return frames,{'project':mode,'bin':source.relative_to(ROOT).as_posix(),'sha256':EXPECTED[mode],
                  'pl00_sha256':sha(assets['PL00_U.ARC']),'valid_compositions_checked':preserved,
                  'unreconstructed_refs':[105,*range(175,183)],'runtime_verified':False}


def build_data():
    characters=[];sources={};main_count=changed_count=0
    for name in gallery.NAMES:
        original=gallery.normalized(name);manifest=json.loads((OUT/name/'manifest.json').read_text('utf8'))
        frames=[]
        for f in original['frames']:
            q={key:f.get(key) for key in ('id','form','ref','bank','group','status','bbox','revised_bbox','usage','palette_scope','animation_ids') if f.get(key) is not None}
            q['path']=pooled_file(f['path'])
            if f.get('revised_path'):q['revised_path']=pooled_file(f['revised_path']);changed_count+=1
            frames.append(q)
        forms=[{'id':f['id'],'label':f['label'],'idle':pooled_file(f['idle']),'idle_bbox':f.get('idle_bbox')} for f in original['forms']]
        main_count+=len(frames)
        partial=[]
        if name in ('shibuki','nana'):
            partial,source=latest_partial(name);sources[name]=source
            forms.append({'id':'partial_fourth','label':'포스 부분 파츠 · 16조합/팔2종','idle':forms[1]['idle'],
                          'idle_bbox':partial[0]['bbox']})
            frames.extend(partial)
        revisions=original.get('revisions',{})
        # Review sheets are optional embedded evidence; raw old partial-mask sheets are not used.
        sheets=[]
        for item in [*revisions.get('sheets',[]),*revisions.get('comparison_sheets',[])]:
            path=item['path'] if isinstance(item,dict) else item
            relative=(ROOT/path).relative_to(OUT).as_posix()
            sheets.append({'label':Path(path).name,'path':pooled_file(relative)})
        missing=[{'bank':q.get('graphics_bank'),'frame':q.get('frame'),'reason':q.get('render_status')}
                 for q in manifest['frames'] if q.get('render_status')=='partial_vram_requires_previous_texture']
        characters.append({'id':name,'label':original['label'],'forms':forms,'frames':frames,'sheets':sheets,
           'partial':partial,'missing':missing,'revised_count':sum(bool(q.get('revised_path')) for q in frames),
           'coverage':manifest.get('coverage',{}),'resources':[],
           'notes':['동작마다 자동 확대·축소하거나 중심을 맞추지 않습니다.',
                    '일반/블랙은 비트맵 공유와 실제 팔레트 차이를 유지합니다.',
                    '피격·전기·별도 효과의 CLUT/반투명은 정지 미리보기와 실제 장면이 다를 수 있습니다.',
                    '캡슐은 인덱스 가시화용 중성 팔레트입니다. 실기 색상 검증이 아닙니다.',
                    '부분 파츠는 최신 BIN의 레이어를 합성합니다. 과거 부분 파츠 시트를 사용하지 않습니다.']})
    if main_count!=4510 or changed_count!=77:raise ValueError(f'Unexpected authenticated collection size: {main_count}/{changed_count}')
    return characters,sources


def lean_playback(manifest):
    result={'characters':{},'limitations':manifest.get('limitations',[]),'sources':manifest.get('sources',{})}
    for mode,expected in EXPECTED.items():
        if manifest['sources'][mode]['bin_sha256']!=expected:raise ValueError('Playback/source BIN mismatch')
    for name,character in manifest['characters'].items():
        result['characters'][name]={'forms':{}}
        for form,content in character['forms'].items():
            animations=[]
            for animation in content['animations']:
                keep=('id','label','group','recommended','loop_to_position','terminal_position','terminal_policy','simulation_only','limitations')
                item={key:animation.get(key) for key in keep}
                item['steps']=[{key:step.get(key) for key in ('position','frame_id','duration_calls','event','reason')} for step in animation['steps']]
                animations.append(item)
            result['characters'][name]['forms'][form]={'animations':animations}
    return result


ALBUM_JS=r'''
const ASSETS=__ASSETS__,PLAYBACK=__PLAYBACK__;
const PARTIAL_ORDER=[[8,'legs'],[1,'head'],[4,'arm'],[2,'body']];
let paintObserver=null,animationTimer=null,animationStep=0,animationCurrent=null;
function ready(image){return image.complete&&image.naturalWidth?Promise.resolve(image):new Promise((resolve,reject)=>{image.addEventListener('load',()=>resolve(image),{once:true});image.addEventListener('error',reject,{once:true})})}
function pic(path){
  if(!cache.has(path)){
    const image=new Image();cache.set(path,image);
    if(path.startsWith('partial:')){
      const [_,who,ref,maskString,arm]=path.split(':'),mask=+maskString;
      const frame=DATA.find(c=>c.id===who).partial.find(f=>f.ref===+ref);
      if(!frame||frame.status==='unreconstructed'){image.src=ASSETS[EMPTY];return image}
      const keys=[frame.layers.base,...PARTIAL_ORDER.filter(([bit])=>mask&bit).map(([bit,key])=>frame.layers[key==='arm'?'arm'+arm:key])];
      Promise.all(keys.map(k=>ready(pic(k)))).then(images=>{
        const canvas=document.createElement('canvas');canvas.width=canvas.height=384;
        const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;images.forEach(im=>ctx.drawImage(im,0,0));image.src=canvas.toDataURL('image/png');
      }).catch(error=>{$('error').textContent='부분 파츠 이미지 읽기 실패: '+error});
    }else image.src=ASSETS[path];
  }
  return cache.get(path);
}
function selectedPath(frame){
  if(frame.form==='partial_fourth')return `partial:${char.id}:${frame.ref}:${$('armorMask').value}:${$('armorArm').value}`;
  return $('showRevised').checked&&frame.revised_path?frame.revised_path:frame.path;
}
function imageLink(anchor,path){
  anchor.href='#';anchor.onclick=async event=>{event.preventDefault();const image=await ready(pic(path));const link=document.createElement('a');link.href=image.src;link.download=path.replaceAll(':','_')+'.png';link.click()};
}
function selectCharacter(id){
  stopBlink();stopAnimation();char=DATA.find(c=>c.id===id);
  $('form').replaceChildren(...char.forms.map(f=>new Option(f.label,f.id)));
  document.querySelectorAll('#characters button').forEach(b=>b.classList.toggle('active',b.dataset.id===id));
  $('manifest').removeAttribute('href');$('manifest').textContent='원점 (160,160) · 원본 PNG 384×384';
  changeForm();renderSheets();
  $('resources').replaceChildren();const link=document.createElement('a');link.href='#limitations';link.textContent='수집 범위·복원 제약·출처';$('resources').append(link);
  $('revisionSummary').textContent=`수집 ${char.frames.length-char.partial.length}개 · 수정 ${char.revised_count}개`+(char.partial.length?' · 최신 부분 파츠 16조합 × 팔2종 포함':'');
  $('characterNotes').textContent=char.notes.join(' ');
  $('missingRefs').textContent=char.missing.length?'독립 복원하지 않은 참조: '+char.missing.map(f=>`bank${f.bank}/${f.frame}`).join(', '):'X 주 동작 105,175~182는 부분 VRAM/예약 참조로 표시하며 완성된 몸체로 그리지 않습니다.';
}
function changeForm(){
  const groups=[...new Set(char.frames.filter(f=>f.form===$('form').value).map(f=>f.group))];
  $('group').replaceChildren(new Option('전체 동작',''),...groups.map(g=>new Option(GROUP_LABELS[g]||g,g)));
  const partial=$('form').value==='partial_fourth';
  $('changedOnly').disabled=partial;$('showRevised').disabled=partial;if(partial)$('changedOnly').checked=false;
  page=0;chosen=null;$('partialControls').hidden=!partial;render();setupAnimations();
}
function updateChosen(){
  $('blink').disabled=!chosen;$('revisionPanel').hidden=!chosen;
  if(!chosen){for(const id of ['compare','before','after'])draw($(id),null);$('detail').textContent='이 조건에 해당하는 프레임이 없습니다.';return}
  const dynamic=chosen.form==='partial_fourth',path=selectedPath(chosen);
  const beforePath=dynamic?`partial:${char.id}:${chosen.ref}:15:${$('armorArm').value}`:chosen.path;
  draw($('compare'),path);draw($('before'),beforePath);draw($('after'),dynamic?path:chosen.revised_path||chosen.path);
  $('detail').textContent=chosen.id+' · '+(GROUP_LABELS[chosen.group]||chosen.group)+' · '+(dynamic?'현재 파츠 조합':chosen.revised_path?($('showRevised').checked?'수정본 표시':'수정 전 표시'):'현재 도트');
  $('revisionNote').textContent=dynamic?'최신 BIN의 각 의상 레이어를 원래 순서로 합성합니다. 실기 중 임시 armor 필드/CLUT 변경은 별도입니다.':chosen.id+(chosen.revised_path?' — 수정 전·후 같은 원점·배율':' — 이번 작업에서 변경하지 않은 도트입니다.');
  $('afterTitle').textContent=dynamic?'현재 조합':chosen.revised_path?'수정 후':'현재 · 변경 없음';
  $('before').previousElementSibling.textContent=dynamic?'전체 파츠 기준':'수정 전';
  imageLink($('beforePNG'),beforePath);imageLink($('afterPNG'),dynamic?path:chosen.revised_path||chosen.path);
}
function renderSheets(){
  $('sheets').replaceChildren();for(const item of char.sheets){const d=document.createElement('details'),s=document.createElement('summary'),im=document.createElement('img');
    s.textContent=item.label;im.loading='lazy';im.src=ASSETS[item.path];d.append(s,im);$('sheets').append(d)}
}
function render(){
  stopBlink();stopAnimation();if(paintObserver)paintObserver.disconnect();$('error').textContent='';
  const form=char.forms.find(f=>f.id===$('form').value),partial=form.id==='partial_fourth';
  const formFrames=char.frames.filter(f=>f.form===form.id);
  subset=formFrames.filter(f=>(!$('group').value||f.group===$('group').value)&&(!$('changedOnly').checked||f.revised_path));
  const boxes=[form.idle_bbox,...subset.flatMap(f=>[f.bbox,f.revised_bbox])].filter(b=>Array.isArray(b)&&b.length===4);
  windowBox=[Math.max(-160,Math.min(-45,...boxes.map(b=>b[0]-3))),Math.max(-160,Math.min(-50,...boxes.map(b=>b[1]-3))),Math.min(224,Math.max(55,...boxes.map(b=>b[2]+3))),Math.min(224,Math.max(40,...boxes.map(b=>b[3]+3)))];
  const scale=+$('zoom').value,w=(windowBox[2]-windowBox[0])*scale,h=(windowBox[3]-windowBox[1])*scale;
  document.documentElement.style.setProperty('--cell',(w+22)+'px');
  draw($('idle'),partial?`partial:${char.id}:0:${$('armorMask').value}:${$('armorArm').value}`:form.idle);$('idleTitle').textContent=char.label+' · 대기 기준';
  $('count').textContent=`${subset.length}개 전체 연속 표시 / ${formFrames.length}개`;
  if(!chosen||!subset.some(f=>f.id===chosen.id))chosen=subset[0]||null;
  $('cards').replaceChildren();
  paintObserver=new IntersectionObserver(entries=>{for(const entry of entries){if(entry.isIntersecting){const cv=entry.target;draw(cv,selectedPath(cv._frame));paintObserver.unobserve(cv)}}},{rootMargin:'400px'});
  const groups=[...new Set(subset.map(f=>f.group))];
  for(const group of groups){
    const section=document.createElement('section');section.className='album-group';const heading=document.createElement('h2');heading.textContent=(GROUP_LABELS[group]||group)+' · '+subset.filter(f=>f.group===group).length;
    const grid=document.createElement('div');grid.className='groupcards';section.append(heading,grid);$('cards').append(section);
    for(const f of subset.filter(q=>q.group===group)){
      const box=document.createElement('article');box.className='card'+(f.revised_path?' changed':'')+(chosen?.id===f.id?' selected':'');box.dataset.id=f.id;
      const cv=document.createElement('canvas');cv.width=cv.height=1;cv.style.width=(w+2)+'px';cv.style.height=(h+2)+'px';cv._frame=f;cv.dataset.frame=f.id;
      const small=document.createElement('small');small.textContent=f.id+(f.status==='unreconstructed'?' · 독립 복원 불가':f.status==='blank'?' · 빈 참조':'');
      const btn=document.createElement('button');btn.textContent='이 프레임 비교';btn.onclick=()=>choose(f);
      const link=document.createElement('a');link.textContent=' PNG';imageLink(link,selectedPath(f));
      box.append(cv,small,btn,link);if(f.revised_path){const badge=document.createElement('small');badge.className='badge';badge.textContent=$('showRevised').checked?'수정본':'수정 전 · 수정본 있음';box.append(badge)}
      if(f.status==='unreconstructed'){const note=document.createElement('small');note.className='warn';note.textContent='이전 VRAM이 필요하므로 완성 도트로 보지 마세요.';box.append(note)}
      grid.append(box);paintObserver.observe(cv);
    }
  }
  if(!subset.length){const empty=document.createElement('p');empty.className='empty';empty.textContent='이 조건에 해당하는 프레임이 없습니다.';$('cards').append(empty)}
  updateChosen();
}
function stopAnimation(){if(animationTimer)clearTimeout(animationTimer);animationTimer=null;if($('playAnimation'))$('playAnimation').textContent='연속 재생'}
function animationsForForm(){
  const form=$('form').value==='partial_fourth'?'fourth':$('form').value;
  return PLAYBACK.characters?.[char.id]?.forms?.[form]?.animations||[];
}
function setupAnimations(){
  stopAnimation();const animations=animationsForForm();$('animationSelect').replaceChildren(...animations.map(a=>new Option(a.label,a.id)));
  $('animationPanel').hidden=!animations.length;animationCurrent=animations.find(a=>a.id===5)||animations.find(a=>a.recommended)||animations[0]||null;
  if(animationCurrent)$('animationSelect').value=String(animationCurrent.id);animationStep=0;showAnimationStep();
}
function showAnimationStep(){
  if(!animationCurrent)return;const step=animationCurrent.steps[animationStep];if(!step)return;
  let frame=step.frame_id?char.frames.find(f=>f.id===step.frame_id):null;
  if(frame&&$('form').value==='partial_fourth')frame=char.partial.find(f=>f.ref===frame.ref);
  draw($('animationCanvas'),frame?selectedPath(frame):EMPTY);
  $('animationState').textContent=`${animationCurrent.label} · step ${step.position} · ${step.duration_calls} 호출 · event ${step.event??0}`+(frame?'':' · '+(step.reason||'이 참조의 몸체는 독립 복원하지 않았습니다.'));
  $('animationLimitations').textContent=(animationCurrent.limitations||[]).join(' ')+(animationCurrent.terminal_policy?' · '+animationCurrent.terminal_policy:'');
}
function advanceAnimation(){
  showAnimationStep();if(!animationCurrent)return;
  const step=animationCurrent.steps[animationStep],delay=Math.max(1,step.duration_calls)*1000/(+$('tickRate').value);
  animationTimer=setTimeout(()=>{
    animationStep++;
    if(animationStep>=animationCurrent.steps.length){
      if(!$('loopAnimation').checked){animationStep=animationCurrent.steps.length-1;stopAnimation();return}
      const at=animationCurrent.steps.findIndex(s=>s.position===animationCurrent.loop_to_position);animationStep=at>=0?at:0;
    }
    advanceAnimation();
  },delay);
}
'''

LABELS={'idle':'대기','run':'이동 · 이동 사격','jump':'점프','air':'공중','wall':'벽 동작','dash':'대시',
 'ground_saber':'지상 검 공격','air_saber':'공중 검 공격','wall_saber':'벽 검 공격','hurt':'피격','low_hp':'체력 부족',
 'hurt_lowhp':'피격 · 체력 부족','ladder':'사다리','arrival_light':'등장 빛','arrival_body':'등장 · 착지',
 'arrival':'등장 · 준비','victory_return_body':'승리 · 귀환 몸체','return_light':'귀환 빛','victory_teleport':'귀환 · 전송',
 'ride_chaser':'라이드 체이서','ride_armor':'라이드 아머','ride_armor_head':'라이드 아머 탑승 머리',
 'raijingeki_shared':'뇌신격 · 공유 자세','hyouretsuzan':'빙열참','ryuenjin':'용염인','air_spin':'회전 베기',
 'rakuhouha':'낙봉파','rakuhouha_static_body':'낙봉파 내장 몸체','shippuuga':'질풍아','shoot_special':'사격 · 특수 자세',
 'other_action':'승리 · 기타 동작','nova_hover':'노바 · 호버','reserved_or_empty':'부분 갱신 · 예약 참조',
 'capsule_ghost':'캡슐 파츠 잔상','selection':'캐릭터 선택','save':'저장 · 불러오기'}


def replace_section(text,start,end,value):
    a=text.index(start);b=text.index(end,a)
    return text[:a]+value+'\n'+text[b:]


def page_html(data,sources,playback,empty):
    html=gallery.PAGE
    html=html.replace('<title>Cliché X4 스프라이트 통일화 작업판</title>','<title>Cliché X4 · 전체 스프라이트 모음집</title>')
    html=html.replace('Cliché X4 · 스프라이트 통일화 작업판','Cliché X4 · 전체 스프라이트 모음집')
    html=html.replace('<option selected>3</option>','<option>3</option>').replace('<option>2</option>','<option selected>2</option>')
    html=html.replace('최신 적용 BIN에서 추출한 도트를 캐릭터·의상·동작별로 모았습니다.','이미지까지 이 파일 안에 담았습니다. 파일 하나만 다른 폴더로 옮겨도 열립니다. 최신 적용 BIN의 도트를 캐릭터·의상·동작별로 모았습니다.')
    html=html.replace('각 manifest의 제약을 확인해 주세요.','하단의 복원 제약을 확인해 주세요.')
    html=html.replace('<div id="error" role="status"></div>',
      '<div id="partialControls" class="toolbar" hidden><label>파츠 <select id="armorMask">'+''.join(f'<option value="{i}"'+(' selected' if i==15 else '')+f'>{i:01X} · '+('없음' if not i else '+'.join(label for bit,label in ((1,'머리'),(2,'몸'),(4,'팔'),(8,'다리'))if i&bit))+'</option>' for i in range(16))+'</select></label><label>팔 <select id="armorArm"><option value="1">arm1</option><option value="2" selected>arm2</option></select></label><span>최신 BIN 레이어 · 고정 마스크 정적 합성</span></div><div id="error" role="status"></div>')
    html=html.replace('<div id="cards"></div><div class="paging"><button id="prev">이전</button><span id="page"></span><button id="next">다음</button></div>',
      '<details id="animationPanel" open><summary>연속 동작 시뮬레이션</summary><select id="animationSelect"></select> <button id="playAnimation">연속 재생</button> <label><input id="loopAnimation" type="checkbox">미리보기 반복</label> <label>호출/초 <select id="tickRate"><option>30</option><option selected>60</option></select></label><p class="warn">원본 시간표의 호출 횟수를 사용한 오프라인 시뮬레이션입니다. 60호출/초는 재생 가정이며, 입력·충돌·이펙트·이벤트에 따른 실제 게임 상태 전환을 재현하지 않습니다.</p><div class="canvas-scroll"><canvas id="animationCanvas"></canvas></div><p id="animationState"></p><small id="animationLimitations"></small></details><div id="cards"></div>')
    html=html.replace('<footer>', '<details id="limitations"><summary>수집 범위 · 복원 제약 · 출처</summary><p id="characterNotes"></p><p id="missingRefs"></p><p>전체 주 수집 이미지4510참조, 이번 수정77이미지 참조입니다. 고유 모션 수와 다릅니다. X 부분 파츠는2캐릭터×237참조×16마스크×팔2종이며 유효228참조씩 최신 레이어로 합성합니다. Zero42~49 및 X105/175~182는 이전 VRAM이 필요한 부분 갱신/예약 참조입니다. 캡슐 잔상은 X당92참조이며 중성 팔레트 미리보기입니다. 선택·저장, 낙봉파 정적 몸체, 추가 피격, 사다리 끝, 등장·승리·귀환·탑승까지 포함했습니다.</p><p>얼티밋 캡슐 전은 재킷, 획득 후는 수영복이며217~230은 획득 후에도 표시mask15를 사용하는 예외를 반영합니다. 원래 타이밍·판정·게임·저장자료를 이 파일이 변경하지 않습니다. 좌우 반전은 픽셀 검수용입니다.</p><pre id="sourceSummary"></pre></details><footer>')
    html=html.replace('</style>', '#cards{display:block}.groupcards{display:grid;grid-template-columns:repeat(auto-fill,minmax(var(--cell),1fr));gap:10px}.album-group{margin:24px 0;overflow:auto}.album-group h2{padding:10px;background:#25384a}.card canvas{box-sizing:border-box}.toolbar[hidden]{display:none}#partialControls{position:static}#animationPanel,#limitations{padding:14px;border:1px solid #43506a;margin:12px 0}#limitations{margin:20px 28px}#sourceSummary{white-space:pre-wrap;overflow-wrap:anywhere}#animationSelect{max-width:100%}</style>')
    # Keep battle-tested same-origin integer canvas drawing and idle comparison.
    html=replace_section(html,'function pic(path){','function draw(cv,', '')
    html=replace_section(html,'function selectCharacter(id){','function choose(frame){', '')
    html=replace_section(html,'function updateChosen(){','for(const c of DATA)', '')
    html=html.replace("$('prev').onclick=()=>{page--;render()};$('next').onclick=()=>{page++;render()};",'')
    injection=ALBUM_JS.replace('__ASSETS__',embedded_json(POOL)).replace('__PLAYBACK__',embedded_json(playback))
    injection+='\nconst EMPTY='+json.dumps(empty)+';\nconst GROUP_LABELS='+json.dumps(LABELS,ensure_ascii=False)+';\n'
    html=html.replace('for(const c of DATA)',injection+'\nfor(const c of DATA)',1)
    html=html.replace('selectCharacter(char.id);',r'''
$('armorMask').onchange=render;$('armorArm').onchange=render;
$('animationSelect').onchange=()=>{stopAnimation();animationCurrent=animationsForForm().find(a=>String(a.id)===$('animationSelect').value);animationStep=0;showAnimationStep()};
$('playAnimation').onclick=()=>{if(animationTimer){stopAnimation();return}if(!animationCurrent)return;animationStep=0;$('playAnimation').textContent='멈추기';advanceAnimation()};
$('tickRate').onchange=()=>{stopAnimation();showAnimationStep()};
$('sourceSummary').textContent=JSON.stringify(__SOURCES__,null,2);
selectCharacter(char.id);
'''.replace('__SOURCES__',embedded_json(sources)))
    html=html.replace("const idle=char.forms.find(f=>f.id===$('form').value).idle;", "const idle=$('form').value==='partial_fourth'?`partial:${char.id}:0:${$('armorMask').value}:${$('armorArm').value}`:char.forms.find(f=>f.id===$('form').value).idle;")
    html=html.replace("cv.dataset.loaded='true';", "cv.dataset.loaded='true';if(['idle','compare'].includes(cv.id)){const wrap=cv.parentElement;wrap.scrollLeft=Math.max(0,(-x*scale)-wrap.clientWidth/2);}")
    html=html.replace('__DATA__',embedded_json(data))
    # No script terminators can escape embedded JSON.
    return html


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--refresh-ui',action='store_true',help='Reuse hash-authenticated embedded pixels; refresh only HTML/player metadata')
    args=parser.parse_args()
    if not PLAYBACK.is_file():raise ValueError('Playback manifest is required before final album generation')
    playback=lean_playback(json.loads(PLAYBACK.read_text('utf8')))
    if args.refresh_ui:
        prior=json.loads((WORK/'build.json').read_text('utf8'));existing=OUT/'ALL_SPRITES.html'
        if file_hash(existing)!=prior['sha256']:raise ValueError('Prior album was changed')
        text=existing.read_text('utf8');decoder=json.JSONDecoder()
        def extracted(marker):return decoder.raw_decode(text[text.index(marker)+len(marker):])[0]
        data=extracted('const DATA=');POOL.update(extracted('const ASSETS='));empty=extracted('const EMPTY=');sources=prior['partial_layer_sources']
        for source in sources.values():
            if file_hash(ROOT/source['bin'])!=source['sha256']:raise ValueError('Cached album BIN changed')
    else:
        data,sources=build_data();empty=pooled_image(Image.new('RGBA',(384,384)))
    html=page_html(data,sources,playback,empty)
    if '__DATA__' in html or '__ASSETS__' in html:raise ValueError('Template not finalized')
    WORK.mkdir(parents=True,exist_ok=True);target=OUT/'ALL_SPRITES.html';target.write_text(html,'utf8')
    report={'file':target.relative_to(ROOT).as_posix(),'sha256':file_hash(target),'bytes':target.stat().st_size,
       'image_pool_entries':len(POOL),'main_references':4510,'revised_references':77,
       'partial_layer_sources':sources,'form_counts':{c['id']:len(c['forms']) for c in data},
       'all_images_embedded':True,'external_image_files_required':False,'native_canvas':[384,384],
       'origin':[160,160],'runtime_verified':False,'game_modified':False}
    report['playback_manifest_sha256']=file_hash(PLAYBACK)
    report['ui_only_refresh_of_authenticated_pixels']=args.refresh_ui
    (WORK/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
