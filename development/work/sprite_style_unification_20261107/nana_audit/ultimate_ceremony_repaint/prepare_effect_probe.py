"""입증된 기존 등장 효과를 새 몸체에 원위치로 재합성하는 읽기 비교."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,digest,sha,write,need,helper
from pack_cycle import raw
from src.psx_player import composition_frame,compose_indices
def render(a,n,parts):
    px,size,box,_=compose_indices(raw(a,0,n),a.banks[0]['frames'][n]['tile_count'],{'parts':parts},allowed_cluts={0,1,2,3});v=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);z=np.zeros((384,384),np.uint8);y,x=np.nonzero(v);z[y+box[1]+160,x+box[0]+160]=v[y,x];return z
def overlay(bg,fg):
    z=bg.copy();z[fg>0]=fg[fg>0];return z
def full(a,n):
    z=a.layer(n)[0].copy()
    for pb in(8,5,7,6):v=a.layer(n,pb)[0];z[v>0]=v[v>0]
    return z
def main():
    p=N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC';need(digest(p)=='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5','부모');a=Archive(p.read_bytes())
    histp=ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC';need(digest(histp)=='89f9cc0a7c9a01a8d38dbc9fd67078413f06c71cc10234e358f5fde5e2643ab4','역사');h=Archive(histp.read_bytes());bodydir=D/'costume_pair_probe_v3';out=D/'effect_probe_v1';out.mkdir(exist_ok=False);records=[];rows=[]
    body={(f,n):np.array(Image.open(bodydir/f'{f}_{n:03}.png'))for f in('before','after')for n in(133,135,136,137)}
    for n in(136,137):
        ps=[q for q in composition_frame(h.c,0,n)['parts']if q['tile']==7];fx=render(h,n,ps);need(int((fx>0).sum())==46,'46px 역사효과')
        displayed={}
        for form,start in(('before',16),('after',0)):
            old=full(a,n)if start else a.layer(n)[0];need(np.array_equal(old[fx>0],fx[fx>0]),'현재효과 exact')
            new=overlay(body[form,n],fx);Image.fromarray(new).save(out/f'{form}_{n:03}_indices.png');displayed[form]=new
            records.append({'ref':n,'form':form,'body_sha256':sha(body[form,n].tobytes()),'effect_sha256':sha(fx.tobytes()),'source_parts':ps,'original_effect_pixels':46,'effect_all46_values_exact':bool(np.array_equal(new[fx>0],fx[fx>0])),'new_body_pixels_under_effect':int(((body[form,n]>0)&(fx>0)).sum()),'effect_translation':[0,0],'output_sha256':sha(new.tobytes())})
        rows.append((f'arrival {n}',[('old before',a.composite(n,15)[0]),('new+original FX',a.rgba(displayed['before'],16)),('old after',a.composite(n,0)[0]),('new+original FX',a.rgba(displayed['after'],0))]))
    fx134=h.layer(129)[0];need(np.array_equal(overlay(fx134,a.layer(133)[0]),a.layer(134)[0]),'134 부모파생')
    nb=overlay(fx134,body['before',133]);na=overlay(fx134,body['after',133])
    for form,z in(('before',nb),('after',na)):Image.fromarray(z).save(out/f'{form}_134_indices.png')
    records.append({'ref':134,'source':'historical129 energy + new133 each costume body','effect_sha256':sha(fx134.tobytes()),'body_over_effect':True,'effect_translation':[0,0],'before_sha256':sha(nb.tobytes()),'after_sha256':sha(na.tobytes())})
    rows.append(('arrival134',[('old before',a.composite(134,15)[0]),('new133+orb',a.rgba(nb,16)),('old after',a.composite(134)[0]),('new133+orb',a.rgba(na))]))
    ps=composition_frame(h.c,0,131)['parts'][:16];fx131=render(h,131,ps);old=np.where(a.layer(133)[0]>0,13,fx131).astype(np.uint8);need(np.array_equal(old,a.layer(131)[0]),'131 부모파생');need(np.array_equal(fx131,a.layer(132)[0]),'132 원효과')
    new131=np.where(body['after',133]>0,13,fx131).astype(np.uint8);Image.fromarray(new131).save(out/'common_131_indices.png');records.append({'ref':131,'source':'현재 정책대로 base(after)133 알파→13색+역사131첫16효과.양폼 공통 빛실루엣.','effect_sha256':sha(fx131.tobytes()),'source_effect_parts':ps,'ref132_preserved':True,'new_visible_body_contribution':int((new131!=fx131).sum()),'output_sha256':sha(new131.tobytes())})
    rows.append(('arrival131',[('old131',a.composite(131)[0]),('new133 light',a.rgba(new131)),('effect132 unchanged',a.composite(132)[0]),('new133 base',a.rgba(body['after',133]))]))
    for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',5)
    write(out/'manifest.json',{'source_arc_sha256':digest(p),'historical_source':histp.relative_to(ROOT).as_posix(),'historical_source_sha256':digest(histp),'body_manifest_sha256':digest(bodydir/'manifest.json'),'frames':records,'scope':'기존 효과 원위치와 새 몸체의 정적 합성 후보.130·138139·141 잔여연동,권총/손 원위치 및 전체원순서와패킹은미완료.','native_packed':False,'runtime_verified':False});print(json.dumps({'frames':len(records),'new_overlap':[{k:r[k]for k in('ref','form','new_body_pixels_under_effect')}for r in records if'form'in r]}))
if __name__=='__main__':main()
