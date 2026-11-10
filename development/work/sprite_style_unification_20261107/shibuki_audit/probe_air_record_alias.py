"""기존 head5 레코드 연속 구간으로 새 머리 텍셀을 정확히 표시할 수 있는지 조사.

레코드/은행/ARC는 쓰지 않는다. 같은 VRAM 텍셀의 여러 소비 좌표까지 검사한다.
"""
from pathlib import Path
import sys,json,struct,time
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from inspect_air_layers import arrays,REFS,P
from scripts.export_x_consistency import Archive
from src.psx_player import bank_offsets,composition_frame,indexed_atlas,compose_indices
from native_pose_pack import need,sha,write

def decode_templates(a,bank=5,max_parts=24):
    off=bank_offsets(a.c);start=off[bank];end=off[bank+1];count=composition_frame(a.c,bank,0)['bank_frame_count'];lo=start+count*4
    templates=[]
    # Every chosen sequence consists of existing complete 4-byte records.
    for p in range(lo,end,4):
        records=[];coverage=set();tiles=set()
        for length in range(1,min(max_parts,(end-p)//4)+1):
            flag,t,x,y=struct.unpack_from('<BBbb',a.c,p+(length-1)*4)
            if flag&0x33 or t>=32:break
            records.append((flag,t,x,y));tiles.add(t)
            if t:coverage.update((yy+160)*384+xx+160 for yy in range(y,y+16)for xx in range(x,x+16)if -160<=xx<224 and -160<=yy<224)
            templates.append((len(tiles-{0}),length,p,tuple(records),frozenset(coverage)))
    return sorted(templates,key=lambda q:(q[0],q[1],q[2]))

def solve(target,records):
    # Only use a source texel when all its visible possible destinations want
    # the same nonzero color. Any conflicts remain transparent. This is stricter
    # than relying on overdraw, so a passing solution has no hidden corruption.
    wanted=target.ravel();consumers={};unsafe=set()
    for flag,t,x,y in records:
        if t==0:continue
        for dy in range(16):
            yy=y+dy+160
            if not 0<=yy<384:return None
            for dx in range(16):
                xx=x+dx+160
                if not 0<=xx<384:return None
                u=15-dx if flag&64 else dx;v=15-dy if flag&128 else dy
                key=(t,v,u);consumers.setdefault(key,set()).add(yy*384+xx)
                if (t%16==0 and u==0)or(flag&128 and v==0):unsafe.add(key)
    atlas=np.zeros((32,256),np.uint8);covered=set()
    for key,positions in consumers.items():
        if key in unsafe:continue
        vals={int(wanted[p])for p in positions}
        if len(vals)==1 and 0 not in vals:
            t,v,u=key;atlas[t//16*16+v,t%16*16+u]=next(iter(vals));covered.update(positions)
    points=set(map(int,np.flatnonzero(wanted)))
    if not points<=covered:return None
    # Native row-major 4bpp bytes, not contiguous per-tile byte slices.
    raw=bytes((atlas[:,0::2]|(atlas[:,1::2]<<4)).ravel())
    cp={'parts':[{'index':i,'flags':fl,'tile':t,'x':x,'y':y,'page':0,'clut':0,'unknown_flags':0,'flip_x':bool(fl&64),'flip_y':bool(fl&128)}for i,(fl,t,x,y) in enumerate(records)]}
    pix,size,bb,_=compose_indices(raw,32,cp);small=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);result=np.zeros_like(target);result[bb[1]+160:bb[3]+160,bb[0]+160:bb[2]+160]=small
    need(np.array_equal(result,target),'Alias solver exact native decode mismatch')
    return raw,int(np.count_nonzero(atlas)),len(consumers)

def main():
    out=H/'air_record_alias_probe03';need(not out.exists(),'Fresh output required');out.mkdir();a=Archive(P.read_bytes());templates=decode_templates(a);rows=[]
    for n in sorted(REFS):
        base,full=arrays(n);d=H/'air_common_head_probe03';common=np.array(Image.open(d/f'{n:03}_common_head_mask.png'))>0;deco=np.array(Image.open(d/f'{n:03}_head_indices.png'))
        target=np.where(common,full,0).astype(np.uint8);target[deco>0]=deco[deco>0]
        points=set(map(int,np.flatnonzero(target)));found=None;checked=0
        for _,length,p,recs,cov in templates:
            if not points<=cov:continue
            checked+=1;solution=solve(target,recs)
            if solution is None:continue
            raw,texels,vars=solution;found={'record_offset_entry':p,'record_offset_bank':p-bank_offsets(a.c)[5],'part_count':length,'record_hex':a.c[p:p+length*4].hex(),'tiles':sorted({t for fl,t,x,y in recs if t}),
                'raw_sha256':sha(raw),'stored_nonzero_texels':texels,'source_variables':vars};(out/f'{n:03}_head_trial.raw').write_bytes(raw);break
        Image.fromarray(target).save(out/f'{n:03}_diagnostic_head_target.png');rows.append({'ref':n,'target_sha256':sha(target.tobytes()),'target_pixels':int(np.count_nonzero(target)),
                     'geometrically_compatible_solutions_checked':checked,'solution':found});print(n,found and(found['part_count'],found['tiles']),flush=True)
    write(out/'report.json',{'analysis_only':True,'source_arc_sha256':sha(P.read_bytes()),'candidate_record_sequences':len(templates),'rows':rows,
          'all_targets_exact':all(r['solution']is not None for r in rows),'native_bank_or_resource_written':False,
          'art_target_is_capacity_diagnostic_not_accepted_final_head':True,'packing_with_body_shot_layers_pending':True,
          'method':'기존 은행5 연속 레코드 별칭. GPU 끝단0/16열·flipY첫행 투명. 동일 텍셀의 모든 좌표에서 같은 목표색일 때만 기록. 원compose_indices로 완전일치 확인.'})
if __name__=='__main__':main()
