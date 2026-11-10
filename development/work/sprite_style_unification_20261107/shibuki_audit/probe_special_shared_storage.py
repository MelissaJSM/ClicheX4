"""동일층 공통 도트/후그리기를 이용해 새 그림을 손실 없이 공동 저장한다."""
from pathlib import Path
import sys,json,itertools,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_armor_remaining import pack_many_patterns
from scripts.prepare_shibuki_ultimate_production import fast_fit,repack_parts
from scripts.overhaul_sprites_costume_pack import pack_planes
from pack_shibuki_hurt import repack_fixed_global
from repack_part_records_lossless import repack as repack_global
from optimize_hurt_tile_storage import optimize
from src.psx_compress import encode_stream
PBS=(0,5,6,7,8)
def main():
 o=H/'standing_special_storage02';need(not o.exists(),'Fresh shared probe');o.mkdir();a=Archive((H/'prepared_hurt_base01/PL00_U.ARC').read_bytes());s=H/'standing_special_layers01';targets={n:{b:np.array(Image.open(s/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in(95,97)};rows=[];valid=[]
 for combo in itertools.chain.from_iterable(itertools.combinations(PBS,k)for k in range(1,6)):
  for alpha in(False,True):
   images=[];keys=[]
   for b in PBS:
    left,right=(targets[n][b]for n in(95,97))
    if b not in combo:
     for n,v in((95,left),(97,right)):keys.append((b,str(n)));images.append(crop(v))
    else:
     m=(left>0)&(right>0)if alpha else(left==right)&(left>0);common=np.where(m,left,0).astype('uint8');ld=np.where(m,0,left).astype('uint8');rd=np.where(m&(left==right),0,right).astype('uint8')
     for label,v in(('common',common),('95',ld),('97',rd)):
      if v.any():keys.append((b,label));images.append(crop(v))
   record={'banks':list(combo),'alpha_common':alpha}
   try:
    r,rs=pack_many_patterns(bytes(4096),32,images,set(range(1,32)),[24]*len(images));parts=dict(zip(keys,rs));full={n:{b:parts.get((b,'common'),[])+parts.get((b,str(n)),[])for b in PBS}for n in(95,97)};need(all(len(rr)<=24 for ll in full.values()for rr in ll.values()),'Parts24');cost=len(encode_stream(r));record.update(passed=True,bytes=cost,parts={str(n):{str(b):rr for b,rr in ll.items()}for n,ll in full.items()},raw=r.hex());valid.append(record)
   except ValueError as e:record.update(passed=False,error=str(e))
   rows.append(record)
  write(o/'progress.json',{'rows':rows});print(json.dumps({'banks':list(combo),'best_bytes':min((r['bytes']for r in valid),default=None),'done':len(rows)}),flush=True)
 top=[]
 for rec in sorted(valid,key=lambda r:r['bytes'])[:5]:
  nr,mapping,opt=optimize(bytes.fromhex(rec['raw']),{0,16},steps=8);changes={b:{}for b in PBS}
  for n in(95,96,97):
   src=95 if n==96 else n
   for b in PBS:changes[b][n]=b''.join(struct.pack('<BBbb',fl,mapping[t],x-80+(n==96),y-80)for t,x,y,fl in rec['parts'][str(src)][str(b)])or struct.pack('<BBbb',0,0,-8,-8)
  try:
   nc=a.c;slack={}
   for b,rr in changes.items():
    try:nc,slack[b]=repack_parts(nc,b,rr)
    except ValueError:nc,slack[b],_=repack_global(nc,b,rr)
   _,gr=repack_fixed_global(a,{95:nr,96:nr,97:nr},{95:32,96:32,97:32});trial={'passed':True,'graphics':gr,'parts_slack':slack}
  except ValueError as e:trial={'passed':False,'error':str(e)}
  top.append({'banks':rec['banks'],'alpha_common':rec['alpha_common'],'optimization':opt,'raw':nr.hex(),'parts':{str(b):{str(n):v.hex()for n,v in rr.items()}for b,rr in changes.items()},'fixed_bank_trial':trial});write(o/'optimized.json',top);print(json.dumps({'top':len(top),'cost':opt['after'],'trial':trial}),flush=True)
 write(o/'report.json',{'options':len(rows),'fitting_atlases':len(valid),'best_unoptimized':min((r['bytes']for r in valid),default=None),'optimized':top,'art_target_unchanged':True,'arc_written':False,'bank_boundary_changed':False})
if __name__=='__main__':main()
