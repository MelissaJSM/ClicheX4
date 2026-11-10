"""노바 원표106 준비4단계와 기존217..220의 표시 순서를 분리해 검토한다."""
from pathlib import Path
import sys,json,struct,base64,io
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,digest
from scripts.c01_audio_build import read_disc
def main():
    d=H/'nova_base_sequence02';need(not d.exists(),'새 순서판');p=H/'prepared_nova_base01/PL00_U.ARC';need(sha(p.read_bytes())=='619032d0b81ffc50e5f5664ff1e3d0c077f226a7d5a8ccfac081be6a2126c6c5','후보 변경');a=Archive(p.read_bytes())
    source=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v26/shibuki_riko.bin';source_sha='b99860d4a87e8b152d2476ea65851583eb01d7978f9b97488a8d88ad7b536f27';need(digest(source)==source_sha,'원표 BIN 변경')
    exe=read_disc(source,('SLUS_005.61',))[0]['SLUS_005.61'];load=struct.unpack_from('<I',exe,0x18)[0];off=lambda x:int(x,16)-load+0x800
    mp=ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json';m=json.loads(mp.read_text('utf8'));s=next(q for q in m['animations']if q['id']==106)
    need(struct.unpack_from('<I',exe,off(m['table_address'])+106*4)[0]==int(s['address'],16),'표 포인터 변경')
    for q in s['steps']:need(exe[off(q['address']):off(q['address'])+4].hex()==q['bytes'],'원step 변경')
    need([q['frame']for q in s['steps'][:4]]==[213,215,216,214],'준비순서');d.mkdir();native={};images={};forms=['base','fourth'];effective={}
    for form,mask in(('base',0),('fourth',15)):
        for ref in sorted({q['frame']for q in s['steps']}):
            em=mask;im=a.composite(ref,em)[0];cut=im.crop((64,64,256,256));need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]),'효과 crop 잘림');buf=io.BytesIO();cut.save(buf,format='PNG');blob=buf.getvalue();name=f'{form}_{ref:03}_native.png';(d/name).write_bytes(blob);native[name]=sha(blob);images[f'{form}_{ref}']='data:image/png;base64,'+base64.b64encode(blob).decode();effective[f'{form}_{ref}']=em
        page([(f'p{q["position"]} ref{q["frame"]} {q["duration_calls_uninterrupted"]}calls e{q["event_bits"]}',a.composite(q['frame'],mask)[0])for q in s['steps'][:5]],a.composite(0,mask)[0],d/f'{form}_preparation_order.png',cols=3,scale=4)
    payload={'steps':s['steps'],'forms':forms,'images':images}
    html='''<!doctype html><meta charset="utf-8"><title>시부키 노바 준비 원표106</title><style>body{background:#1c2230;color:#eee;font:16px sans-serif}canvas{width:1152px;height:576px;image-rendering:pixelated}button{font:inherit}</style><h1>노바 준비4와 기존 효과 연결</h1><p>왼쪽 기본·오른쪽 포스.213..216만 새 원화이며217..220은 부모를 보존했습니다.일반 PL00는 모든단계에서 player+A7의 기본0/포스15를 유지합니다. Ultimate의217이후강제15와다릅니다. 원표의 호출수·상대분기만 재생하며 물리이동·입력 조건·이벤트·이펙트 객체·소리는 실행하지 않습니다.</p><button id="restart">처음</button><button id="play">재생/정지</button><button id="tick">1호출</button><p id="info"></p><canvas id="canvas" width="384" height="192"></canvas><script>const DATA=__DATA__;const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;const ims={};let ready=false,state={};function current(){return DATA.steps[state.pos]}function draw(){if(!ready)return;ctx.clearRect(0,0,384,192);DATA.forms.forEach((f,i)=>ctx.drawImage(ims[f+'_'+current().frame],192*i,0));info.textContent=`p${state.pos} ref${current().frame} elapsed${state.elapsed} calls${state.total}`;}function reset(){state={pos:0,elapsed:0,total:0,playing:false};draw()}function step(){state.elapsed++;state.total++;if(state.elapsed>=current().duration_calls_uninterrupted){state.pos+=current().relative_step;state.elapsed=0}draw()}restart.onclick=reset;tick.onclick=step;play.onclick=()=>state.playing=!state.playing;window.review={reset,step,ready:()=>ready,state:()=>({...state,ref:current().frame})};Promise.all(Object.entries(DATA.images).map(([k,url])=>new Promise(resolve=>{const im=new Image();im.onload=()=>{ims[k]=im;resolve()};im.src=url}))).then(()=>{ready=true;reset()});let prior=0,acc=0;function loop(t){if(state.playing){acc+=Math.min(100,t-prior);while(acc>=1000/60){step();acc-=1000/60}}else acc=0;prior=t;requestAnimationFrame(loop)}requestAnimationFrame(loop);</script>'''
    (d/'REVIEW.html').write_text(html.replace('__DATA__',json.dumps(payload)),'utf8')
    cp=H.parent/'zero_audit/shibuki_nova_hover_relations01/conclusions.json'
    write(d/'report.json',{'candidate_sha256':sha(p.read_bytes()),'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':source_sha,'exe_sha256':sha(exe),'metadata_sha256':sha(mp.read_bytes()),'mask_reading':{'path':cp.relative_to(ROOT).as_posix(),'sha256':sha(cp.read_bytes())},'sequences':[s],'native_table_bytes_verified':True,'original_steps':len(s['steps']),'new_art_steps':4,'new_refs':[213,214,215,216],'parent_preserved_effect_refs':[217,218,219,220],'forms':forms,'native_pngs':native,'effective_masks':effective,'preview_call_rate_assumption':60,'events_or_physics_reproduced':False,'runtime_verified':False,'claim_basic_can_trigger_nova':False,'continuous_animation_actually_watched_by_model':False})
    print(json.dumps({'original_steps':len(s['steps']),'new_steps':4,'images':len(native),'report':sha((d/'report.json').read_bytes())}))
if __name__=='__main__':main()
