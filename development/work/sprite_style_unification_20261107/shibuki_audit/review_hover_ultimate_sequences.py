"""호버 원표12개와 별도제트 원표5개를 독립 호출수로 재생한다."""
from pathlib import Path
import sys,json,struct,base64,io
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,digest
from scripts.c01_audio_build import read_disc
from review_hover_ultimate_contacts import board,fx,overlay,FINAL
def main():
    d=H/'hover_ultimate_sequence01';need(not d.exists(),'새 원표검토');p=H/'prepared_hover_ultimate01/PL02_U.ARC';a=Archive(p.read_bytes());need(sha(a.data)==FINAL,'후보변경');oldp=H/'prepared_nova_strike_ultimate01/PL02_U.ARC';old=Archive(oldp.read_bytes());bp=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v29/shibuki_riko.bin';need(digest(bp)=='753928a3cf2101caabf05cbe112217aa6d4b95b6320674632692831297a52252','BR29변경');ce=read_disc(bp,('SLUS_005.61',))[0]['SLUS_005.61'];oe=read_disc(ROOT/'MegaMan X4.bin',('SLUS_005.61',))[0]['SLUS_005.61'];off=lambda x:x-0x80010000+2048
    mp=ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json';m=json.loads(mp.read_text('utf8'));ids=[21,22,23,24,25,26,133,134,135,136,137,138];seq=[q for q in m['animations']if q['id']in ids];need(len(seq)==12,'원표12');d.mkdir();cases={};pngs={};urls={};effective={}
    def save(name,im):
        cut=im.crop((64,64,256,256));need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]),'원점crop잘림');buf=io.BytesIO();cut.save(buf,format='PNG');blob=buf.getvalue();(d/name).write_bytes(blob);pngs[name]=sha(blob);urls[name]='data:image/png;base64,'+base64.b64encode(blob).decode();return name
    for s in seq:
        aid=s['id'];at=off(int(m['table_address'],16))+aid*4;need(ce[at:at+4]==oe[at:at+4]and struct.unpack_from('<I',ce,at)[0]==int(s['address'],16),'플레이어표포인터');steps=[]
        for q in s['steps']:
            at=off(int(q['address'],16));need(ce[at:at+4]==oe[at:at+4]and ce[at:at+4].hex()==q['bytes'],'원표바이트');n=q['frame'];mask=15 if 217<=n<=230 else 0;effective[str(n)]=mask;names=[]
            for title,ar in(('parent',old),('new',a)):
                name=f'{title}_{n:03}_native.png'
                if name not in pngs:save(name,ar.composite(n,mask)[0])
                names.append(name)
            steps.append({'position':q['position'],'frame':n,'duration':q['duration_calls_uninterrupted'],'relative':q['relative_step'],'event_bits':q['event_bits'],'images':names})
        cases[f'player_{aid}']={'title':f'원플레이어표 {aid} / 부모와 새몸','kind':'player','steps':steps}
    sm={q['id']:q for q in seq}
    for aid in range(21,27):
        rows=[]
        for s in(sm[aid],sm[aid+112]):
            row=[]
            for q in s['steps']:
                n=q['frame'];im=a.composite(n,effective[str(n)])[0];row.append((f'table{s["id"]} p{q["position"]} ref{n} /{q["duration_calls_uninterrupted"]}calls',im,'#e9e8e4'))
            while len(row)<4:row.append(('end state / no extra step',Image.new('RGBA',(384,384)),'#e9e8e4'))
            rows.append(row)
        board(d/f'order_{aid:03}_{aid+112:03}.png',rows,5)
    cp=H/'hover_ultimate_final_contacts01/report.json';contacts=json.loads(cp.read_text('utf8'))
    for r in contacts['original_jet_sequences']:
        aid=r['animation'];at=off(r['pointer']);need(ce[at:at+12]==oe[at:at+12],'제트원표');n={33:221,34:223,35:225,36:227,32:229}[aid];steps=[]
        for pos,s in enumerate(r['steps']):
            z=np.array(Image.open(cp.parent/f'jet_{s[3]:02}_indices.png'));effect=fx(z,(68,173,179,255));names=[save(f'jet_{aid}_{s[3]}_{ref}.png',overlay(a.composite(ref,15)[0],effect))for ref in(n,n+1)];steps.append({'position':pos,'frame':s[3],'duration':s[0],'relative':s[2],'event_bits':s[1],'images':names})
        cases[f'jet_{aid}']={'title':f'원제트표 {aid} / 몸{n}와 사격{n+1}','kind':'jet','steps':steps}
    payload={'cases':cases,'images':urls};html='''<!doctype html><meta charset="utf-8"><title>얼티밋 호버 원순서 검토</title><style>body{background:#202b3c;color:#f0f0f0;font:16px sans-serif}canvas{width:1152px;height:576px;image-rendering:pixelated;background:#e9e8e4}button,select{font:inherit}</style><h1>얼티밋 호버10 원순서 / 별도 추진 위상</h1><p>플레이어표는 왼쪽 부모·오른쪽 새몸. 제트표는 왼쪽 새 비사격·오른쪽 새 사격입니다. 각 표를 독립 재생하며 실제게임의 전환/물리/총탄 이동/입력·이벤트를 실행하지 않습니다. 제트는 원색인 모양을 중립색으로 표시합니다. 96호출 정지는 실제 호버 지속시간이 아닙니다. 60호출/초 표시는 검토 가정입니다. 획득 후 Ultimate 기준으로 공중45..48은mask0,호버는 강제15를 적용합니다.</p><select id="choice"></select><button id="restart">처음</button><button id="play">재생/정지</button><button id="tick">1호출</button><p id="info"></p><canvas id="canvas" width="384" height="192"></canvas><script>const DATA=__DATA__;const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;let ready=false,state={};const ims={};Object.entries(DATA.cases).forEach(([id,v])=>{let op=document.createElement('option');op.value=id;op.textContent=v.title;choice.append(op)});function current(){return DATA.cases[state.id].steps[state.pos]}function draw(){if(!ready)return;ctx.clearRect(0,0,384,192);current().images.forEach((n,i)=>ctx.drawImage(ims[n],i*192,0));info.textContent=`${DATA.cases[state.id].title} p${state.pos} ref${current().frame} elapsed${state.elapsed} calls${state.total}`;}function select(id){state={id,pos:0,elapsed:0,total:0,playing:false};choice.value=id;draw()}function reset(){select(state.id||Object.keys(DATA.cases)[0])}function step(){state.elapsed++;state.total++;if(state.elapsed>=current().duration){state.pos+=current().relative;state.elapsed=0}draw()}choice.onchange=()=>select(choice.value);restart.onclick=reset;tick.onclick=step;play.onclick=()=>state.playing=!state.playing;window.review={reset,select,step,ready:()=>ready,state:()=>({...state,ref:current().frame})};Promise.all(Object.entries(DATA.images).map(([k,url])=>new Promise(resolve=>{const im=new Image();im.onload=()=>{ims[k]=im;resolve()};im.src=url}))).then(()=>{ready=true;reset()});let prior=0,acc=0;function loop(t){if(state.playing){acc+=Math.min(100,t-prior);while(acc>=1000/60){step();acc-=1000/60}}else acc=0;prior=t;requestAnimationFrame(loop)}requestAnimationFrame(loop);</script>'''
    (d/'REVIEW.html').write_text(html.replace('__DATA__',json.dumps(payload)),'utf8');write(d/'report.json',{'candidate_sha256':FINAL,'source_bin':str(bp.relative_to(ROOT)),'source_bin_sha256':digest(bp),'EXE_sha256':sha(ce),'original_EXE_sha256':sha(oe),'metadata_sha256':sha(mp.read_bytes()),'native_table_bytes_verified':True,'player_sequences':seq,'jet_sequences':contacts['original_jet_sequences'],'cases':cases,'effective_masks':effective,'native_pngs':pngs,'original_player_step_count':sum(len(q['steps'])for q in seq),'original_jet_step_count':15,'contact_report_sha256':sha(cp.read_bytes()),'source_script_sha256':sha(Path(__file__).read_bytes()),'sequences_timing_independent':True,'preview_call_rate_assumption':60,'events_or_physics_reproduced':False,'runtime_verified':False,'continuous_animation_actually_watched_by_model':False});print(json.dumps({'cases':len(cases),'native_pngs':len(pngs),'report':sha((d/'report.json').read_bytes())}))
if __name__=='__main__':main()
