"""새85..92 두폼을 실제 BR22 원표88/89/90/91/94 순서로 표시한다."""
from pathlib import Path
import sys,json,struct,base64,io
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page,digest

def main():
    out=H/'standing_fire_sequence01';need(not out.exists(),'Fresh sequence output')
    paths={'base':H/'prepared_standing_fire_base01/PL00_U.ARC'}
    expected={'base':'4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175'}
    arcs={}
    for key,path in paths.items():need(sha(path.read_bytes())==expected[key],'Candidate changed');arcs[key]=Archive(path.read_bytes())
    source=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v22/shibuki_riko.bin'
    source_sha='54e53da83b0255e6123dc3c9d6ffeab867bc5201107b1a0ed89c798038739e99'
    need(digest(source)==source_sha,'Wrong native table source')
    files,_=read_disc(source,('SLUS_005.61',));exe=files['SLUS_005.61'];load=struct.unpack_from('<I',exe,0x18)[0]
    offset=lambda address:int(address,16)-load+0x800
    meta_path=ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json'
    meta=json.loads(meta_path.read_text('utf8'));seqs=[];checks=[]
    for seq in meta['animations']:
        if seq['id'] not in (88,89,90,91,94):continue
        ptr=struct.unpack_from('<I',exe,offset(meta['table_address'])+4*seq['id'])[0]
        need(ptr==int(seq['address'],16),'Animation pointer changed')
        for step in seq['steps']:
            raw=exe[offset(step['address']):offset(step['address'])+4];need(raw.hex()==step['bytes'],'Step bytes changed')
            duration,event,relative,ref=struct.unpack('<bbbB',raw)
            need((duration,event,relative,ref)==(step['duration_signed'],step['event_signed'],step['relative_step'],step['frame']),'Step fields changed')
            need((duration&255 or 256)==step['duration_calls_uninterrupted'],'Call duration changed')
        seqs.append({k:seq[k] for k in ('id','address','steps')});checks.append({'id':seq['id'],'steps':len(seq['steps']),'pointer':hex(ptr),'all_bytes_exact':True})
    need(len(seqs)==5,'Missing table');out.mkdir();images={};native={};forms=['base','fourth']
    refs=sorted({step['frame'] for seq in seqs for step in seq['steps']})
    for form,key,mask in (('base','base',0),('fourth','base',15)):
        arc=arcs[key]
        for ref in refs:
            full=arc.composite(ref,mask)[0];cut=full.crop((112,112,208,208))
            need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(full)[:,:,3]),'Native crop clips')
            buf=io.BytesIO();cut.save(buf,format='PNG');data=buf.getvalue();name=f'{form}_{ref:03}_native.png';(out/name).write_bytes(data)
            images[f'{form}_{ref}']='data:image/png;base64,'+base64.b64encode(data).decode();native[name]=sha(data)
        # 88은 일반사격 복귀,91은 위로 들어올리는 동작까지 포함한다.
        # 대표 두표의 모든 단계를 실제 원점에서 나열한다.
        for seq in seqs:
            if seq['id'] not in (88,91):continue
            page([(f'ID{seq["id"]} p{step["position"]} ref{step["frame"]} {step["duration_calls_uninterrupted"]}call e{step["event_bits"]}',arc.composite(step['frame'],mask)[0]) for step in seq['steps']],arc.composite(0,mask)[0],out/f'{form}_id{seq["id"]}_ordered.png',cols=3,scale=4)
    payload={'sequences':seqs,'images':images,'forms':forms}
    html='''<!doctype html><meta charset="utf-8"><title>시부키85..92 두폼 원순서 검토</title>
<style>body{background:#1d222c;color:#eee;font:16px sans-serif}canvas{width:768px;height:384px;image-rendering:pixelated}button,select{font:inherit}p{max-width:768px}</style>
<h1>새85..92 기본·포스 원표 표시</h1><p>왼쪽부터 기본·포스. 실제 BR22 EXE 표88/89/90/91/94의 순서와 유지 호출수를 읽었습니다. 60호출/초는 검토 가정이며 실제 게임·무기객체·물리·외부상태·음향 이벤트는 재현하지 않습니다.</p>
<select id="anim">__OPTIONS__</select><button id="restart">처음</button><button id="play">재생/정지</button><button id="tick">1호출</button><p id="status"></p><canvas id="canvas" width="192" height="96"></canvas>
<p>상대step0에 진입하면 검토기에서는 마지막 그림을 유지합니다. 실제 호출자는 land_or_fall 등 외부상태로 종료하므로 말미92를 고정96 게임프레임으로 주장하지 않습니다. 별도 투사체와 외부 타이머는 이 검토기에서 실행하지 않습니다.</p>
<script>const DATA=__DATA__;const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;const ims={};let ready=false,state={};function steps(){return DATA.sequences.find(s=>s.id===state.id).steps}function draw(){if(!ready)return;const s=steps()[state.pos];ctx.clearRect(0,0,192,96);DATA.forms.forEach((f,i)=>ctx.drawImage(ims[f+'_'+s.frame],96*i,0));status.textContent=`ID${state.id} p${state.pos} ref${s.frame} ${state.elapsed}/${s.duration_calls_uninterrupted} total${state.total} ${state.holding?'외부상태 대기표시':''}`;}function reset(id=88){state={id,pos:0,elapsed:0,total:0,playing:false,holding:false};state.holding=steps()[0].relative_step===0;draw()}function step(){if(state.holding)return;state.total++;state.elapsed++;const s=steps()[state.pos];if(state.elapsed>=s.duration_calls_uninterrupted){state.pos+=s.relative_step;state.elapsed=0;if(steps()[state.pos].relative_step===0){state.holding=true;state.playing=false}}draw()}anim.onchange=()=>reset(+anim.value);restart.onclick=()=>reset(+anim.value);play.onclick=()=>{if(!state.holding)state.playing=!state.playing};tick.onclick=step;window.review={reset,step,ready:()=>ready,state:()=>({...state,ref:steps()[state.pos].frame})};Promise.all(Object.entries(DATA.images).map(([key,url])=>new Promise(resolve=>{const im=new Image();im.onload=()=>{ims[key]=im;resolve()};im.src=url}))).then(()=>{ready=true;reset()});let prior=0,acc=0;function loop(t){if(state.playing){acc+=Math.min(100,t-prior);while(acc>=1000/60&&state.playing){step();acc-=1000/60}}else acc=0;prior=t;requestAnimationFrame(loop)}requestAnimationFrame(loop);</script>'''
    html=html.replace('__DATA__',json.dumps(payload,ensure_ascii=False)).replace('__OPTIONS__',''.join(f'<option value="{seq["id"]}">원표{seq["id"]}</option>' for seq in seqs))
    # window.status와 같은 이름의 전역을 피한다.
    html=html.replace('status.textContent=',"document.getElementById('status').textContent=")
    (out/'REVIEW.html').write_text(html,'utf8')
    write(out/'report.json',{'candidates':{k:{'path':p.relative_to(ROOT).as_posix(),'sha256':expected[k]} for k,p in paths.items()},
        'source_bin':source.relative_to(ROOT).as_posix(),'source_bin_sha256':source_sha,'exe_sha256':sha(exe),
        'metadata':{'path':meta_path.relative_to(ROOT).as_posix(),'sha256':sha(meta_path.read_bytes())},
        'native_step_checks':checks,'sequences':seqs,'native_pngs':native,'forms':forms,
        'native_table_bytes_verified':True,'timing_changed':False,'preview_call_rate_assumption':60,
        'external_state_or_effect_objects_reproduced':False,'continuous_animation_actually_watched_by_model':False,
        'runtime_verified':False,'browser_verified':False})
    print(json.dumps({'step_count':sum(len(s['steps']) for s in seqs),'native_images':len(native),'report_sha256':sha((out/'report.json').read_bytes())}))

if __name__=='__main__':main()
