"""실제 EXE의 X 표33..37과 새 피격13 재추출을 연결한 표시 시뮬레이션."""
from pathlib import Path
import sys,json,struct,base64,io
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,SOURCE,SOURCE_SHA
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page,digest

def main():
    o=H/'hurt_base_sequence01';need(not o.exists(),'Fresh sequence review')
    p=H/'prepared_hurt_base01/PL00_U.ARC';data=p.read_bytes();need(sha(data)=='87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b','Candidate changed');a=Archive(data)
    qpath=ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json';metadata=json.loads(qpath.read_text('utf8'));seqs=[s for s in metadata['animations']if s['id']in range(33,38)]
    need(digest(SOURCE)==SOURCE_SHA,'Wrong executable source');files,_=read_disc(SOURCE,('SLUS_005.61',));exe=files['SLUS_005.61'];load=struct.unpack_from('<I',exe,0x18)[0]
    def at(addr):return int(addr,16)-load+0x800
    table=at(metadata['table_address']);checks=[]
    for seq in seqs:
        ptr=struct.unpack_from('<I',exe,table+4*seq['id'])[0];need(ptr==int(seq['address'],16),'Native table pointer changed')
        for s in seq['steps']:
            b=exe[at(s['address']):at(s['address'])+4];need(b.hex()==s['bytes'],'Native step changed');duration,event,relative,frame=struct.unpack('<bbbB',b);need((duration,event,relative,frame)==(s['duration_signed'],s['event_signed'],s['relative_step'],s['frame']),'Metadata mismatch');need((duration&255 or 256)==s['duration_calls_uninterrupted'],'Timer unit mismatch')
        checks.append({'id':seq['id'],'pointer':hex(ptr),'steps':len(seq['steps']),'all_bytes_exact':True})
    o.mkdir();images={};native_files={}
    refs=sorted({s['frame']for seq in seqs for s in seq['steps']})
    for form,mask in(('base',0),('fourth',15)):
        for n in refs:
            im=a.composite(n,mask)[0];cut=im.crop((112,112,208,208));need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]),'Native crop clips body/effect');buf=io.BytesIO();cut.save(buf,format='PNG');blob=buf.getvalue();images[f'{form}_{n}']='data:image/png;base64,'+base64.b64encode(blob).decode();f=o/f'{form}_{n:03}_native.png';f.write_bytes(blob);native_files[f.name]=sha(blob)
        for seq in seqs:
            if seq['id']not in(33,34,35):continue
            pics=[(f'ID{seq["id"]} p{s["position"]}: ref{s["frame"]} {s["duration_calls_uninterrupted"]}call jump{s["relative_step"]:+}',a.composite(s['frame'],mask)[0])for s in seq['steps']]
            page(pics,a.composite(0,mask)[0],o/f'{form}_id{seq["id"]}_ordered.png',cols=4,scale=4)
    payload={'sequences':seqs,'images':images}
    html='''<!doctype html><meta charset="utf-8"><title>시부키 피격 원순서 검토</title><style>body{background:#1d222c;color:#eee;font:16px sans-serif}canvas{width:960px;height:480px;image-rendering:pixelated}button,select{font:inherit}p{max-width:1000px}</style><h1>새 피격13 원표 재생 검토</h1><p>왼쪽 기본·오른쪽 포스. 실제 EXE 표33..37의 순서·상대분기·프레임 유지 호출수를 따르는 표시 시뮬레이션입니다. 60호출/초는 검토 가정입니다. 게임의 이동·충돌·넉백·무적 깜빡임·소리·상태 종료 조건은 재현하지 않습니다.</p><select id="anim">__OPTIONS__</select><button id="restart">처음</button><button id="play">재생/정지</button><button id="tick">1호출</button><p id="status"></p><canvas id="canvas" width="192" height="96"></canvas><p>109는 원PL00 정책대로 기본106의 실루엣입니다.235/236은 원시부키 오라 뒤에 새234를 그립니다. 원표의 자기분기는 검토기에서 화면 유지로 표시하며, 외부상태에 따른 실제 피격 지속시간을 뜻하지 않습니다.</p><script>const DATA=__DATA__;const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;const ims={};let ready=false,state={id:33,pos:0,elapsed:0,total:0,playing:false,holding:false};function steps(){return DATA.sequences.find(s=>s.id===state.id).steps}function draw(){if(!ready)return;const s=steps()[state.pos];ctx.clearRect(0,0,192,96);ctx.drawImage(ims['base_'+s.frame],0,0);ctx.drawImage(ims['fourth_'+s.frame],96,0);document.getElementById('status').textContent=`ID${state.id} p${state.pos} ref${s.frame} ${state.elapsed}/${s.duration_calls_uninterrupted} total${state.total} ${state.holding?'HOLD':''}`;}function reset(id=+anim.value){state={id,pos:0,elapsed:0,total:0,playing:false,holding:DATA.sequences.find(s=>s.id===id).steps[0].relative_step===0};draw()}function step(){if(state.holding)return;state.total++;state.elapsed++;const s=steps()[state.pos];if(state.elapsed>=s.duration_calls_uninterrupted){state.pos+=s.relative_step;state.elapsed=0;if(steps()[state.pos].relative_step===0){state.holding=true;state.playing=false}}draw()}anim.onchange=()=>reset();restart.onclick=()=>reset();play.onclick=()=>{if(!state.holding)state.playing=!state.playing};tick.onclick=()=>step();window.review={reset,step,ready:()=>ready,state:()=>({...state,ref:steps()[state.pos].frame})};Promise.all(Object.entries(DATA.images).map(([k,v])=>new Promise(resolve=>{let i=new Image();i.onload=()=>{ims[k]=i;resolve()};i.src=v}))).then(()=>{ready=true;reset()});let prior=0,acc=0;function loop(t){if(state.playing){acc+=Math.min(100,t-prior);while(acc>=1000/60&&state.playing){step();acc-=1000/60}}else acc=0;prior=t;requestAnimationFrame(loop)}requestAnimationFrame(loop);</script>'''.replace('__OPTIONS__',''.join(f'<option value="{s["id"]}">원표 {s["id"]}</option>'for s in seqs)).replace('__DATA__',json.dumps(payload,ensure_ascii=False))
    (o/'REVIEW.html').write_text(html,'utf8');write(o/'report.json',{'candidate_sha256':sha(data),'source_bin':SOURCE.relative_to(ROOT).as_posix(),'source_bin_sha256':SOURCE_SHA,'exe_sha256':sha(exe),'metadata':{'path':qpath.relative_to(ROOT).as_posix(),'sha256':sha(qpath.read_bytes())},'native_step_checks':checks,'sequences':seqs,'native_pngs':native_files,'display_crop':{'size':[96,96],'origin':[48,48],'all_body_and_effect_pixels_inside':True},'native_table_bytes_verified':True,'timing_changed':False,'preview_call_rate_assumption':60,'external_state_or_physics_reproduced':False,'continuous_animation_actually_watched_by_model':False,'runtime_verified':False,'browser_verified':False})
    print(json.dumps({'sequences':len(seqs),'steps':sum(len(s['steps'])for s in seqs),'native_images':len(images),'report_sha256':sha((o/'report.json').read_bytes())}))
if __name__=='__main__':main()
