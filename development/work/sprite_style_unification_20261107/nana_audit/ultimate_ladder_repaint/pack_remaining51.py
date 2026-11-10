"""RN43을 부모로 남은7사다리 참조만 교체한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(D)]
import pack_first7 as pack
from preview_restore import Archive,digest,sha,write,need,helper
from prepare_first7_targets import composite
REFS=(148,149,150,151,152,153,155);PBS=(0,5,6,7,8);OUT=D/'packed_remaining51'
def main():
 need(not OUT.exists(),'Fresh output');OUT.mkdir();plan=json.loads((W/'staging_rn_v43.json').read_text('utf8'));src=plan['resources']['PL02_U.ARC'];p=ROOT/src['path'];need(digest(p)==src['after'],'Current parent');a=Archive(p.read_bytes());targets={};hashes={};sources={};body={}
 for n in REFS:
  s=D/('shots_registered51'if n in(150,155)else'remaining_common51c');b=np.array(Image.open(s/f'before_{n:03}_indices.png'));v=np.array(Image.open(s/f'after_{n:03}_indices.png'));need(not ((v>0)&(b==0)).any(),'Costume coverage');need(label(b>0,np.ones((3,3)))[1]==label(v>0,np.ones((3,3)))[1]==1,'Body connection');body[n]=(b,v)
  ls={0:v,5:np.where((b!=v)|(b==15),b,0).astype(np.uint8),**{pb:np.zeros_like(v)for pb in(6,7,8)}};hashes[str(n)]={}
  for pb,z in ls.items():targets[n,pb]=z;hashes[str(n)][str(pb)]=sha(z.tobytes());Image.fromarray(z).save(OUT/f'layer{pb}_{n:03}.png')
  for mask in range(16):
   for arm in (1,2):need(composite(a,ls,mask,arm).tobytes()==a.rgba(b,16).tobytes()if mask&1 else composite(a,ls,mask,arm).tobytes()==a.rgba(v).tobytes(),'Costume RGBA')
  for f in('before','after'):q=s/f'{f}_{n:03}_indices.png';sources[q.relative_to(ROOT).as_posix()]=digest(q)
 pack.BEFORE=src['after'];pack.REFS=REFS;new,report=pack.build(p.read_bytes(),targets,{'targets':hashes},all_rgba=False);actual=Archive(new)
 for n,(x0,y0,x1,y1)in[(150,(-24,-11,-16,-4)),(155,(-21,-15,-13,-8))]:
  sl=(slice(160+y0,160+y1),slice(160+x0,160+x1))
  for mask in(0,15):need(np.array_equal(np.array(actual.composite(n,mask)[0])[sl],np.array(a.composite(n,mask)[0])[sl]),'Gun RGBA/alpha exact')
 report.update({'remaining_unmodified_refs':[],'current_parent':src,'scope':'잔여7사다리 참조의 새원화35층. 원권총/총구/표/팔레트와 비대상 보존. 실기 별도.','target_sources':sources,'generated_sources':{str((D/name/'generated.png').relative_to(ROOT)):digest(D/name/'generated.png')for name in('b_costume_registered51','shots_registered51')},'native_decoder_pending':True,'full_project_complete':False})
 (OUT/'PL02_U.ARC').write_bytes(new);write(OUT/'verification.json',report)
 for i,ns in enumerate(((148,149),(150,155),(151,152,153))):helper.grid([(str(n),[('old jacket',a.composite(n,15)[0]),('new jacket',actual.composite(n,15)[0]),('old bare',a.composite(n)[0]),('new bare',actual.composite(n)[0])])for n in ns],OUT/f'readback_{i}.png',6)
 trial={'project':'ver_rin_nana','source_bin':'out/ver_rin_nana/sprite_style_unification_20261107_v43/rin_nana.bin','source_sha256':'e751a82bc3d1e228d26389d911ca4b46efa12612dcea69b6c99fdeb3ba3ca637','output':'out/ver_rin_nana/sprite_style_unification_20261107_v44','resources':{'PL02_U.ARC':{'path':(OUT/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':src['after'],'after':sha(new)}},'prior_plan':'work/sprite_style_unification_20261107/staging_rn_v43.json','checkpoint_only':True,'full_art_unification_complete':False,'checkpoint_label':'nana_ultimate_ladder_remaining7_resume51','review_images':[]};write(W/'staging_rn_v44.json',trial);print(json.dumps({'candidate':sha(new),'refs':REFS,'packing':report['packing']}))
if __name__=='__main__':main()
