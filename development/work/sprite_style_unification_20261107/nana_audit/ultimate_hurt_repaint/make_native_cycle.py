"""새 피격13의 실제 ARC와 미국판 원시간표를 오프라인으로 비교한다."""
from pathlib import Path
import sys,json,io,base64,ast
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
from scripts.export_sprite_playback import read_disc,at
FINAL='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5'
REFS=tuple(range(106,115))+(233,234,235,236)
def main():
    out=D/'native_cycle_v1';out.mkdir(exist_ok=False)
    old=Archive((N/'rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC').read_bytes())
    new=Archive((D/'packed_hurt_candidate_v1/PL02_U.ARC').read_bytes());need(sha(new.data)==FINAL,'후보 해시')
    src=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v18/rin_nana.bin'
    need(digest(src)=='0f40463b883e00a7e3acf268fd45052b905d0454440d8c5436ce24fe80f58c95','실제 부모 디스크 해시')
    exe=read_disc(src,['SLUS_005.61'])['SLUS_005.61']
    meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'))
    records={q['id']:q for q in meta['characters']['nana']['forms']['base']['animations']};cases={};tables=[]
    for aid in range(33,38):
        q=records[aid];need(at(exe,int(q['table_address'],16)+4*aid,4).hex()==q['pointer_bytes'],'실제 표 포인터')
        for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'실제 시간표 스텝')
        cases[str(aid)]=[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step'],'event':s['event']}for s in q['steps']];tables.append(q)
    cases['수동 대기/몸체 연결 · 임의12호출']=[{'ref':n,'calls':12,'step':1,'event':0}for n in(0,106,110,233,234,0)]
    refs=sorted({s['ref']for seq in cases.values()for s in seq});data={};frames=[];bounds=(80,104,240,200);w,h=160,96
    for n in refs:
        images=[old.composite(0)[0],old.composite(n)[0],new.composite(n)[0],old.composite(0,15)[0],old.composite(n,15)[0],new.composite(n,15)[0]];urls=[];hashes=[]
        for j,im in enumerate(images):
            outside=np.array(im)[:,:,3];outside[bounds[1]:bounds[3],bounds[0]:bounds[2]]=0;need(not outside.any(),f'검토창 절단 {n}/{j}')
            crop=im.crop(bounds);crop.save(out/f'{n:03}_{j}.png');buf=io.BytesIO();crop.save(buf,format='PNG');urls.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode())
            v=np.array(crop);v[v[:,:,3]==0]=0;hashes.append(sha(v.tobytes()))
        data[str(n)]=urls;frames.append({'ref':n,'canvas_rgba_sha256':hashes,'changed':n in REFS})
    tree=ast.parse((N/'ultimate_wall_repaint/make_native_cycle.py').read_text('utf8'))
    html=next(q.value.value for q in ast.walk(tree)if isinstance(q,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='html'for t in q.targets)and isinstance(q.value,ast.Constant))
    html=html.replace('Nana Ultimate native wall review','Nana hurt13 native review').replace('나나 얼티밋 벽 · ARC 재추출','나나 얼티밋 피격13 · ARC 재추출')
    html=html.replace('전폼 대기 / 기존 / 새 후보 / 후폼 대기 / 기존 / 새 후보','After idle / Previous after / New after / Before idle / Previous before / New before').replace('실제 EXE 표 13·14·15·125·126·127','실제 EXE 표 33·34·35·36·37')
    html=html.replace('section{display:flex;gap:4px}','section{display:flex;gap:4px;flex-wrap:wrap;max-width:1950px}')
    html=html.replace('SMALL',''.join(f'<canvas id="small{j}" width="{w}" height="{h}"></canvas>'for j in range(6))).replace('BIG',''.join(f'<canvas id="big{j}" width="{w*2}" height="{h*2}"></canvas>'for j in range(6)))
    html=html.replace('DATAJSON',json.dumps(data,separators=(',',':'))).replace('CASEJSON',json.dumps(cases,ensure_ascii=False,separators=(',',':')))
    (out/'REVIEW.html').write_text(html,'utf8')
    for aid in range(33,38):
        seq=cases[str(aid)];sheet=Image.new('RGB',(192*len(seq),360),'#b6c0c7');dr=ImageDraw.Draw(sheet)
        for i,s in enumerate(seq):
            dr.text((192*i+4,3),f'{s["ref"]} / {s["calls"]} calls',fill='black')
            for j,mask in enumerate((0,15)):
                im=new.composite(s['ref'],mask)[0].crop((112,112,208,192)).resize((192,160),Image.Resampling.NEAREST);sheet.paste(im,(192*i,30+160*j),im)
        sheet.save(out/f'timeline_{aid}.png')
    write(out/'manifest.json',{'parent_arc_sha256':sha(old.data),'candidate_arc_sha256':sha(new.data),'exe_sha256':sha(exe),'native_table_bytes_exact':True,'tables':tables,'cases':cases,'frames':frames,'window':bounds,'canvas_size':[w,h],'html_sha256':digest(out/'REVIEW.html'),'runtime_verified':False,'clock_assumption':'60호출/초 가정. 실제 게임 물리·이벤트 복귀를 실행하지 않으며 상대스텝0은 검토 반복으로 처리.','renderer_policy':'Ultimate after mask0 / before mask15 arm2. 피격에 포함된 원효과/파생실루엣을 함께 표시. 몸통아머 접촉피격은 원코드상 표35로 연결.'})
    print(json.dumps({'refs':len(refs),'native_tables':len(tables),'out':str(out)}))
if __name__=='__main__':main()
