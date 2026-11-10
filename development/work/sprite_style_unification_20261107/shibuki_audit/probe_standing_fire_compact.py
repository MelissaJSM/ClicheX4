"""픽셀 손실 없는 타일 내부 평행이동/저장 반전/정원 선택 시험."""
from pathlib import Path
import sys,json,argparse,itertools
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'work/tools'))
from native_pose_pack import need,sha,write,crop
from probe_standing_fire_capacity import PBS
from probe_run_compact_flip import packed
from probe_run_occluded_tile_union import tiles_of,render
from scripts.export_x_consistency import Archive
from scripts.overhaul_sprites_costume_pack import pack_planes
from scripts.prepare_shibuki_ultimate_production import pack_shared
from pack_shibuki_hurt import tile_seed
from src.psx_compress import encode_stream
from psx_compress_cost import encoded_cost

def compact(raw,parts,fixed,passes=2):
    tt=tiles_of(raw);used={r[1]for rr in parts.values()for r in rr}|set(fixed);fixed=set(fixed)|{0};used.discard(0)
    shape={}
    for t in used:
        y,x=np.nonzero(tt[t]);shape[t]=(int(y.max()+1),int(x.max()+1),len(x))if len(x)else(0,0,0)
    move=sorted(used-fixed);data={t:tt[t].tobytes()for t in move};best=None;trials=0
    for count in range(max(max(fixed)+1,len(used)+1),33):
        slots=sorted(set(range(1,count))-fixed)
        for key in(lambda t:shape[t],lambda t:(shape[t][1],shape[t][0]),lambda t:data[t],lambda t:data[t][::-1]):
            for reverse in(False,True):
                order=sorted(move,key=key,reverse=reverse);mapping={h:h for h in fixed};available=order.copy()
                for pos in slots:
                    if not available:break
                    old=next((t for t in available if pos%16!=0 or not tt[t][:,0].any()),None)
                    if old is None:continue
                    available.remove(old);mapping[old]=pos
                if available:continue
                trial=[np.zeros((16,16),np.uint8)for _ in range(count)]
                for old,new in mapping.items():trial[new]=tt[old].copy()
                cost=encoded_cost(packed(trial,count));trials+=1
                if best is None or cost<best[0]:best=(cost,count,trial,mapping)
    need(best is not None,'정원 후보 없음');cost,count,tiles,mapping=best
    pp={k:[[fl,mapping[t],x,y]for fl,t,x,y in rr]for k,rr in parts.items()}
    movable=sorted(set(mapping.values())-fixed-{16});history=[cost]
    for step in range(passes):
        any_improvement=False
        for t in movable:
            ar=tiles[t];yy,xx=np.nonzero(ar)
            if not len(xx):continue
            x0,y0,x1,y1=int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1);patch=ar[y0:y1,x0:x1];h,w=patch.shape
            found=None;bestcost=cost
            for flip in(False,True):
                for dy in range(17-h):
                    for dx in range(17-w):
                        if not flip and(dx,dy)==(x0,y0):continue
                        new=np.zeros((16,16),np.uint8);new[dy:dy+h,dx:dx+w]=patch[:,::-1]if flip else patch
                        trial=tiles.copy();trial[t]=new;value=encoded_cost(packed(trial,count));trials+=1
                        if value<bestcost:bestcost=value;found=(new,flip,dx,dy)
            if found:
                new,flip,dx,dy=found;tiles[t]=new
                for rr in pp.values():
                    for r in rr:
                        if r[1]!=t:continue
                        fl,_,x,y=r;oldleft=(16-x1)if fl&64 else x0
                        nf=fl^(64 if flip else 0);newleft=(16-dx-w)if nf&64 else dx
                        oldtop=(16-y1)if fl&128 else y0;newtop=(16-dy-h)if nf&128 else dy
                        r[0]=nf;r[2]+=oldleft-newleft;r[3]+=oldtop-newtop
                cost=bestcost;any_improvement=True
        history.append(cost)
        if not any_improvement:break
    expanded=tiles+[np.zeros((16,16),np.uint8)for _ in range(32-count)]
    for k,rr in parts.items():need(np.array_equal(render(tt,rr),render(expanded,pp[k])),'저장변환 표시 불일치')
    nr=packed(tiles,count);need(len(encode_stream(nr))==cost,'비용 불일치')
    for t in range(0,count,16):need(not tiles[t][:,0].any(),'GPU U경계')
    for t in fixed:need(np.array_equal(tt[t],tiles[t]),'보호타일 변경')
    return nr,pp,{'count':count,'before':len(encode_stream(raw)),'after':cost,'saved':len(encode_stream(raw))-cost,'trials':trials,'history':history,'fixed_tiles':sorted(fixed),'exact_layers':len(parts)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='standing_fire_compact01');ap.add_argument('--passes',type=int,default=2);z=ap.parse_args();d=H/z.output;need(not d.exists(),'새 폴더 필요');d.mkdir()
    a=Archive((H/'prepared_standing_special_base01/PL00_U.ARC').read_bytes());s=H/'standing_fire_targets_probe01';targets={n:{b:np.array(Image.open(s/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in range(85,93)};rows=[]
    for refs in((85,86),(87,92),(88,89),(90,),(91,)):
        fixed={7,8}if refs==(88,89)else set()
        if len(refs)==2 and not fixed:
            name='_'.join(map(str,refs));raw=(H/'standing_fire_shared01'/f'{name}_raw.bin').read_bytes();q=json.loads((H/'standing_fire_shared01'/f'{name}_records.json').read_text('utf8'));rr=q['records'];parts={(b,n):[[fl,t,x-80,y-80]for t,x,y,fl in rr[i*5+j]]for i,n in enumerate(refs)for j,b in enumerate(PBS)}
        else:
            n=refs[-1];imgs=[crop(targets[n][b])for b in PBS];seed=tile_seed(a,88,fixed)if fixed else bytes(4096)
            if fixed:imgs.append(crop(np.roll(targets[88][5],1,axis=1)))
            raw,rr=pack_planes(seed,32,imgs,set(range(32))-{0,16}-fixed,[24]*len(imgs));parts={}
            for r in refs:
                for i,b in enumerate(PBS):parts[b,r]=[[fl,t,x-80-(r==88),y-80]for t,x,y,fl in(rr[5]if r==88 and b==5 else rr[i])]
                if r==88:
                    for p in json.loads((s/'manifest.json').read_text('utf8'))['effect88']['source_records']:parts[0,r].append([p['flags'],p['tile'],p['x'],p['y']])
        nr,pp,proof=compact(raw,parts,fixed,z.passes);proof.update(refs=list(refs),raw=nr.hex(),parts={str(b):{str(n):v for(bb,n),v in pp.items()if bb==b}for b in PBS})
        rows.append(proof);write(d/'report.json',{'groups':rows,'art_changed':False,'arc_written':False,'scope':'저장위치/반전·타일정원만 바꾼 읽기 조사. 원그림 모든층 exact, 효과7/8 전체보존. 조립은행 용량과 원MIPS/GPU는 후속.'});print(json.dumps({k:v for k,v in proof.items()if k not in('raw','parts')}),flush=True)
if __name__=='__main__':main()
