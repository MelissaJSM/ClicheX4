"""동결 공중 후보에서 남은 대시/공중대시 참조와 원래 동작표만 추출한다."""
from pathlib import Path
import sys,json
import numpy as np
D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path[:0]=[str(ROOT),str(D/'native_restore')]
from preview_restore import Archive,sha,digest,need,write,helper
from src.psx_player import composition_frame
SOURCE=D/'air_repaint/packed_air_candidate_v1/PL00_U.ARC';EXPECTED='721457a50ea48e76c1ac592eec21db274b43c5863cc5b3df310ac981d5890dca';OUT=D/'dash_repaint';REFS=[*range(67,85),93,94]
def main():
    need(digest(SOURCE)==EXPECTED,'Parent');a=Archive(SOURCE.read_bytes());OUT.mkdir(exist_ok=True);records=[]
    for n in REFS:
        ar=a.layer(n)[0];y,x=np.nonzero(ar);ey,ex=np.nonzero(ar==14);f=a.banks[0]['frames'][n]
        records.append({'ref':n,'bbox':[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)],'eye':[float(np.median(ex)-160),float(np.median(ey)-160)]if len(ex)else None,'base_rgba_sha256':sha(a.composite(n)[0].tobytes()),'fourth_rgba_sha256':sha(a.composite(n,15)[0].tobytes()),'tile_count':f['tile_count'],'aliases':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],'parts':{str(pb):len(composition_frame(a.c,pb,n)['parts'])for pb in(0,5,6,7,8)}})
    refs=list(range(67,85,2))+[93]
    for i in range(0,len(refs),3):
        helper.grid([(f'dash {n}/{n+1}',[('기본 대기',a.composite(0)[0]),('현재 기본',a.composite(n)[0]),('다른 공중대시 자세'if n==93 else'현재 사격',a.composite(n+1)[0]),('포스 대기',a.composite(0,15)[0]),('현재 포스',a.composite(n,15)[0]),('다른 공중대시 자세'if n==93 else'포스 사격',a.composite(n+1,15)[0])])for n in refs[i:i+3]],OUT/f'current_{i//3+1}.png',5)
    helper.grid([(label,[(str(n),a.composite(n,mask)[0])for n in(0,7,39,63,69,73,77,93)])for label,mask in [('기본',0),('포스',15)]],OUT/'style_sequence.png',5)
    source=ROOT/'work/sprite_consistency_20261105/playback/manifest.json';m=json.loads(source.read_text('utf8'));animations=[]
    for p in m['characters']['nana']['forms']['base']['animations']:
        if any(s['frame_ref']in REFS for s in p['steps']):animations.append({k:p[k]for k in('id','label','address','steps')})
    write(OUT/'inputs.json',{'parent_arc':SOURCE.relative_to(ROOT).as_posix(),'parent_arc_sha256':EXPECTED,'scope':REFS,'frames':records,'prior_animation_manifest_sha256':digest(source),'animation_note':'표는 이전 해시 고정 EXE에서 추출한 보조자료이며 이번 ARC에는 시간표 변경이 없다. 현재 EXE를 다시 실행한 증거는 아니다.','animations':animations,'new_art_generated':False,'native_packed':False})
    print(json.dumps({'out':str(OUT),'refs':len(records),'animations':len(animations)}))
if __name__=='__main__':main()
