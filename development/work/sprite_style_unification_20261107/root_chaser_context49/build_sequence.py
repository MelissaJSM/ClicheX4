"""실제 원표를 사용한 체이서 합성 재생. 에뮬레이터 실기와 구분한다."""
from pathlib import Path
import base64, gzip, hashlib, io, json, struct, sys
import numpy as np
from PIL import Image,ImageDraw
from probe_body import draw,r,v,b
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.export_x_consistency import Archive
from scripts.build_sprite_style_album import zero_palettes,zero_image
from scripts.prepare_riko_ui import entry
sha=lambda b:hashlib.sha256(b).hexdigest()
files={};asset_inputs={}
for tag,project,stem,num in [('br','ver_buki_riko','shibuki_riko',31),('rn','ver_rin_nana','rin_nana',43)]:
    p=ROOT/f'out/{project}/sprite_style_unification_20261107_v{num}/{stem}.bin'
    with p.open('rb') as f:
        disc=DiscReader(f,p.stat().st_size);fs={q['path']:q for q in disc.inspect()['files']}
        files[tag]={name:disc.read(fs[name]['lba'],fs[name]['size']) for name in ('/SLUS_005.61;1','/ARC/ST05_00.ARC;1')}
    assert sha(files[tag]['/SLUS_005.61;1'])=='93a8f0cab28034bd7d5b93fe4362c7c56c8c2bfba5ccb764e7bf547a02ae1616'
exe=files['br']['/SLUS_005.61;1'];off=lambda a:a-0x80010000+2048
assert exe==files['rn']['/SLUS_005.61;1']
stage=files['br']['/ARC/ST05_00.ARC;1'];assert stage==files['rn']['/ARC/ST05_00.ARC;1']
texture=entry(stage,0x10102);parts=entry(stage,10)
signature=v[5,384:400].copy().tobytes();signature_at=texture.find(signature);tex_at=signature_at-5*128
assert tex_at==0  # Stage texture resource 0; another resource duplicates this row.
parts_sig=r[0x1ba31c:0x1ba31c+64];parts_at=parts.find(parts_sig)
assert parts_at>=0 and parts.find(parts_sig,parts_at+1)<0
# All referenced bike texels and parts must be the current, unmodified stage bytes.
for n in range(13):
    h=struct.unpack_from('<I',r,0x1ba31c+4*n)[0]
    start=(h>>16)*4;size=(h&65535)*4
    assert r[0x1ba31c+start:0x1ba31c+start+size]==parts[parts_at+start:parts_at+start+size]
    for k in range(h&65535):
        fl,t,x,y=struct.unpack_from('<BBbb',r,0x1ba31c+start+4*k);assert fl&3==0
        yy,xx=(t//16)*16,(t%16)*4
        for dy in range(16):
            assert v[yy+dy,384+xx:388+xx].tobytes()==texture[tex_at+(yy+dy)*128+xx*2:tex_at+(yy+dy)*128+xx*2+8],(n,t,dy)

def sequence(table,n):
    address=struct.unpack_from('<I',exe,off(table)+4*n)[0];i=0;seen=set();steps=[]
    while i not in seen:
        assert 0<=i<128;seen.add(i);t,e,rel,ref=struct.unpack_from('<bbbB',exe,off(address)+4*i)
        assert t>0;steps.append({'index':i,'ticks':t,'event':e,'relative':rel,'ref':ref});i+=rel
    end=off(address)+max(q['index']for q in steps)*4+4
    assert exe[off(address):end]==r[address&0x1fffff:(address&0x1fffff)+end-off(address)]
    return {'address':hex(address),'steps':steps,'loop_to':i}

seqs={'bike':{n:sequence(0x800f8fc4,n) for n in range(12)},'zero':{n:sequence(0x8011aff0,n) for n in range(65,77)}}
xold=json.loads((W/'zero_audit/shibuki_chaser_sequences01/report.json').read_text('utf8'))
seqs['x']={q['id']:{'address':q['address'],'steps':[{'index':s['position'],'ticks':s['duration_ticks'],'event':s['event'],'relative':s['relative_step'],'ref':s['frame']}for s in q['steps']],'loop_to':q['loop_to']}for q in xold['animations']}
for q in seqs['x'].values():
    for step in q['steps']:
        z=struct.unpack_from('<bbbB',exe,off(int(q['address'],16))+step['index']*4)
        assert z==(step['ticks'],step['event'],step['relative'],step['ref'])

def walk(seq,length):
    steps={q['index']:q for q in seq['steps']};i=0;out=[]
    while len(out)<length:
        q=steps[i];out.extend([q['ref']]*q['ticks']);i+=q['relative']
    return out[:length]
# These pairings follow actual bike's set_animation/player animation-setter calls.
selector_tables={hex(a):list(exe[off(a):off(a)+4]) for a in (0x800f9100,0x800f9104,0x800f9108,0x800f910c,0x800f9110,0x800f9114)}
pairs=[(0,65),(1,67),(2,69),(3,66),(4,68),(5,70),(6,71),(8,72),(10,73),(7,74),(9,75),(11,76)]
for body_table,rider_table in ((0x800f9100,0x800f910c),(0x800f9104,0x800f9110),(0x800f9108,0x800f9114)):
    for pair in zip(selector_tables[hex(body_table)][:3],selector_tables[hex(rider_table)][:3]):assert pair in pairs
timelines=[{'bike_animation':bike,'rider_animation':rider,'bike':walk(seqs['bike'][bike],32),'x':walk(seqs['x'][rider],32),'zero':walk(seqs['zero'][rider],32)}for bike,rider in pairs]
arcs={};images={};forms=[]
def dataurl(im):
    buf=io.BytesIO();im.save(buf,format='PNG');return 'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
for character,tag,zero in [('shibuki','br_v31',False),('nana','rn_v43',False),('riko','br_v31',True),('rin','rn_v43',True)]:
    plan=json.loads((W/f'staging_{tag}.json').read_text('utf8'))
    for form in (('normal','black') if zero else ('base','fourth','ultimate_before','ultimate_after')):
        name='PL01_U.ARC' if zero else 'PL02_U.ARC' if form.startswith('ultimate') else 'PL00_U.ARC'
        src=plan['resources'][name];blob=(ROOT/src['path']).read_bytes();assert sha(blob)==src['after'];asset_inputs[src['path']]=sha(blob)
        key=f'{character}/{form}';form_images={};refs=sorted({ref for tl in timelines for ref in tl['zero' if zero else 'x']})
        if zero:pal=zero_palettes(blob)
        else:a=Archive(blob)
        for ref in refs:
            im=zero_image(blob,character,{'id':f'{form}:b1_{ref:03}','form':form,'bank':1,'ref':ref},pal) if zero else a.composite(ref,15 if form in ('fourth','ultimate_before')else 0)[0]
            form_images[str(ref)]=dataurl(im.crop((96,96,224,224)))
        images[key]=form_images;forms.append({'key':key,'type':'zero'if zero else'x','body':'zero'if zero else'x'})
body_images={name:{str(n):dataurl(draw(n,384,0,clut)) for n in range(13)}for name,clut in [('x',0x7848),('zero',0x784a)]}
payload={'forms':forms,'riders':images,'bodies':body_images,'timelines':timelines}
out=ROOT/'out/sprite_style_unification_20261107/chaser_context49';out.mkdir(exist_ok=True)
html='''<!doctype html><meta charset="utf-8"><title>체이서 연결부 검토</title>
<style>body{background:#151d27;color:#eef3ff;font:15px sans-serif;margin:20px}select,button{font:inherit;margin:4px;padding:8px}.grid{display:grid;grid-template-columns:repeat(4,256px);gap:12px}canvas{image-rendering:pixelated;background:#26313f;width:256px;height:256px}p{max-width:1050px}</style>
<h2>네 캐릭터 체이서 연결부 · BR31 / RN43</h2><p>원게임 차량·탑승자 프레임표를 함께 시작한 정적 합성 재생입니다. 실제 게임 실행이 아니며, 호출 시점 차이·월드 이동·배경·실제 GPU 가림 순서는 재현하지 않습니다. 1틱을 1/60초로 표시합니다.</p>
<select id="seq"></select><button id="play">일시정지</button><button id="restart">처음부터</button><button id="step">1틱 진행</button><button id="flip">좌우 반전</button><span id="tick"></span><div class="grid" id="grid"></div>
<script>const DATA=__DATA__;let t=0,playing=true,flip=false,last=0;const all={};const tasks=[];
function img(key,src){const im=new Image();all[key]=im;tasks.push(new Promise((ok,fail)=>{im.onload=ok;im.onerror=fail;im.src=src}));}
for(const [f,refs]of Object.entries(DATA.riders))for(const [r,src]of Object.entries(refs))img(f+'/'+r,src);
for(const [f,refs]of Object.entries(DATA.bodies))for(const [r,src]of Object.entries(refs))img('bike/'+f+'/'+r,src);
DATA.timelines.forEach((q,i)=>seq.add(new Option('차량 '+q.bike_animation+' / 탑승자 '+q.rider_animation,i)));
const cvs=DATA.forms.map(f=>{const el=document.createElement('div');el.innerHTML='<div>'+f.key+'</div><canvas width="128" height="128"></canvas>';grid.append(el);return el.querySelector('canvas')});
function draw(){let q=DATA.timelines[seq.selectedIndex];DATA.forms.forEach((f,i)=>{let c=cvs[i].getContext('2d');c.clearRect(0,0,128,128);c.save();if(flip){c.translate(128,0);c.scale(-1,1)}c.drawImage(all['bike/'+f.body+'/'+q.bike[t]],0,0);c.drawImage(all[f.key+'/'+q[f.type][t]],0,0);c.restore()});tick.textContent='틱 '+t+' / 31';window.renderedTick=t;}
seq.onchange=()=>{t=0;draw()};play.onclick=()=>{playing=!playing;play.textContent=playing?'일시정지':'재생'};restart.onclick=()=>{t=0;draw()};step.onclick=()=>{playing=false;t=Math.min(31,t+1);draw()};document.getElementById('flip').onclick=()=>{flip=!flip;draw()};
Promise.all(tasks).then(()=>{window.ready=true;draw();function frame(now){if(playing&&now-last>=1000/60){t=Math.min(31,t+1);last=now;draw();if(t===31){playing=false;play.textContent='재생'}}requestAnimationFrame(frame)}requestAnimationFrame(frame)});
window.showPair=(index,tick,mirror=false)=>{playing=false;seq.selectedIndex=index;t=tick;flip=mirror;draw()};
</script>'''.replace('__DATA__',json.dumps(payload,separators=(',',':')))
(out/'CHASE_RIDER_REVIEW.html').write_text(html,'utf8')
report={'gameplay_verified':False,'rider_forms':12,'timelines':12,'simulation_ticks_per_timeline':32,'source_state_sha256':sha(b),'current_EXE_sha256':sha(exe),'current_stage_sha256':sha(stage),'BR_RN_stage_equal':True,'vehicle_texture_current_stage_offset':tex_at,'vehicle_parts_current_stage_offset':parts_at,'vehicle_parts_13_and_all_referenced_texels_equal_current_discs':True,'rider_inputs':asset_inputs,'sequence_tables':seqs,'selector_tables':selector_tables,'pairings':pairs,'html':(out/'CHASE_RIDER_REVIEW.html').relative_to(ROOT).as_posix(),'html_sha256':sha(html.encode()),'game_files_modified':False,'user_state_modified':False,'actually_viewed':False,'limitations':['원표 duration 기반의 같은 시작점 합성이다. 실제 update 순서와 호출 지연을 실행하지 않는다.','모든 셀은 차량 아래/플레이어 위로 합성한다. 실제 그리기 순서가 다를 때의 가림은 별도 대상.','선택표 밖의 별도 복귀 호출7/75는 상태 전환으로 중단될 수 있어 이12표 재생에 포함하지 않았다.']}
(O/'sequence_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'forms':12,'sequences':12,'static_scene_tiles_checked':True,'html':report['html']}))
