"""현재 Ultimate 등장/승리 몸체와 의상층을 읽기 전용으로 재추출한다."""
from pathlib import Path
import sys,json
import numpy as np
D=Path(__file__).resolve().parent;ROOT=D.parents[2]
sys.path[:0]=[str(ROOT),str(D/'native_restore'),str(D/'base_run_repaint')]
from preview_restore import Archive,digest,sha,write,need,helper
from pack_cycle import raw
from scripts.prepare_shibuki_ultimate_production import records
def main():
    src=D/'rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC';need(digest(src)=='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9','부모 확인')
    a=Archive(src.read_bytes());out=D/'ultimate_ceremony_repaint/preflight_v1';out.mkdir(parents=True,exist_ok=False)
    refs=list(range(133,141))+[156,157,158,204,205,206,207];frames=[];rows=[]
    for n in refs:
        before=a.composite(n,15)[0];after=a.composite(n,0)[0]
        b=np.array(before);f=np.array(after);mask=(b[:,:,3]>0)|(f[:,:,3]>0);yy,xx=np.where(mask)
        layers={str(pb):sha(a.layer(n,pb)[0].tobytes())for pb in(0,5,6,7,8)}
        for tag,im in [('before',before),('after',after)]:im.save(out/f'{tag}_{n:03}.png')
        frames.append({'ref':n,'raw_sha256':sha(raw(a,0,n)),'stream_offset':a.banks[0]['frames'][n]['offset'],'tile_count':a.banks[0]['frames'][n]['tile_count'],'layers_sha256':layers,'before_rgba_sha256':sha(before.tobytes()),'after_rgba_sha256':sha(after.tobytes()),'composition_sha256':{str(pb):sha(records(a.c,pb,n))for pb in(0,5,6,7,8)},'jacket_layer_pixels':int(np.count_nonzero(a.layer(n,5)[0])),'costume_rgba_difference':int(np.any(b!=f,axis=2).sum()),'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-159),int(yy.max()-159)]if len(xx)else None})
        rows.append((f'Ultimate {n}',[('before idle',a.composite(0,15)[0]),('current before',before),('after idle',a.composite(0,0)[0]),('current after',after)]))
    sheets=[]
    for i in range(0,len(rows),2):
        path=out/f'comparison_{i//2+1}.png';helper.grid(rows[i:i+2],path,6);sheets.append({'path':path.relative_to(ROOT).as_posix(),'sha256':digest(path),'refs':refs[i:i+2]})
    identical=[]
    for i,p in enumerate(frames):
        for q in frames[i+1:]:
            if p['before_rgba_sha256']==q['before_rgba_sha256'] and p['after_rgba_sha256']==q['after_rgba_sha256']:identical.append([p['ref'],q['ref']])
    write(out/'manifest.json',{'source_arc':src.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'frames':frames,'sheets':sheets,'identical_rgba_pairs':identical,'scope':'Ultimate 등장/승리15참조×전후의상 정적 읽기.141/142대기복귀·순수전송효과는 보존 기준으로 이번 재작화목표에 자동포함하지 않음. 아직 생성·수정·동결·게임검사 없음.','images_actually_viewed':False,'game_written':False})
    print(json.dumps({'frames':len(frames),'sheets':len(sheets),'identical_rgba_pairs':identical}))
if __name__=='__main__':main()
