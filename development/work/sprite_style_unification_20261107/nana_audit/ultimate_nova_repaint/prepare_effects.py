"""노바 역사 효과 규칙을 재현한 뒤 새217에 맞춘 별도 후보를 만든다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,binary_fill_holes
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
def reconstruct(oldbody,oldfx,newbody,fill):
 remove=binary_dilation(oldbody>0,iterations=1);envelope=binary_fill_holes(oldfx>0);fx=oldfx.copy();fx[remove]=0;holes=remove&envelope&(fx==0)&(newbody==0);fx[holes]=fill;fx[newbody>0]=0
 return fx,remove,envelope,holes
def main():
 out=D/'effects_probe_v1';out.mkdir(exist_ok=False);current=N/'ultimate_hover_repaint/packed_hover_candidate_v1/PL02_U.ARC';historical=ROOT/'work/ver_rin_nana/nana_ultimate_armor/nova_packed_v2/PL02_U.ARC';swap=ROOT/'work/ultimate_costume_swap_20261105/core/prepared_complete_v1/ver_rin_nana/PL02_U.ARC'
 for p,h in((current,'e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff'),(historical,'89f9cc0a7c9a01a8d38dbc9fd67078413f06c71cc10234e358f5fde5e2643ab4'),(swap,'a8269047ab937d5bbd6b5e97e7cdeb0241b9e60b1612eb2bb93d692d79fef7d2')):need(digest(p)==h,'출처 고정 해시')
 a,h,s=Archive(current.read_bytes()),Archive(historical.read_bytes()),Archive(swap.read_bytes());body=np.array(Image.open(D/'dash217_semantic_v1/body_217_indices.png'));oldbody=h.layer(217,5)[0];seed=s.layer(217)[0];proof=[];rows=[]
 for n,fill in((218,14),(220,7)):
  oldfx=h.layer(n,5)[0];previous,remove,envelope,oldholes=reconstruct(oldbody,oldfx,seed,fill);need(np.array_equal(previous,a.layer(n,5)[0]),'역사 규칙의 현재 효과 exact');fx,_,_,holes=reconstruct(oldbody,oldfx,body,fill);protected=(~remove)&(body==0);need(np.array_equal(fx[protected],oldfx[protected]),'기존몸/새몸 바깥 효과 색인 exact');need(not ((fx>0)&(body>0)).any(),'새몸 가림 없음');im=a.rgba(body);im.alpha_composite(a.rgba(fx,16));uncut=a.rgba(body);uncut.alpha_composite(a.rgba(a.layer(n,5)[0],16));rows.append((str(n),[('current',a.composite(n,15)[0]),('old effect over new body diagnostic',uncut),('new body + registered effect',im),('registered effect only',a.rgba(fx,16))]));Image.fromarray(body).save(out/f'body_{n:03}_indices.png');Image.fromarray(fx).save(out/f'effect_{n:03}_indices.png')
  for name,z in(('original_body_dilation',remove),('original_envelope',envelope),('fill_mask',holes),('preserved_effect_mask',protected)):
   Image.fromarray((z*255).astype(np.uint8)).save(out/f'{name}_{n}.png')
  proof.append({'ref':n,'historical_layer5_sha256':sha(oldfx.tobytes()),'old_body_dilation1_count':int(remove.sum()),'historical_reproduction_exact':True,'historical_fill_count':int(oldholes.sum()),'new_fill_count':int(holes.sum()),'fill_existing_index':fill,'old_effect_opaque':int((previous>0).sum()),'new_effect_opaque':int((fx>0).sum()),'different_cells':int((fx!=previous).sum()),'unchanged_effect_covers_new_body':int(((previous>0)&(body>0)).sum()),'new_effect_covers_body':0,'new_body_outside_original_envelope':int(((body>0)&~envelope).sum()),'source_protected_cells':int(protected.sum()),'new_effect_sha256':sha(fx.tobytes())})
 oldflash=np.zeros_like(body);oldflash[binary_dilation(seed>0,iterations=2)]=7;oldflash[seed>0]=6;need(np.array_equal(oldflash,a.layer(219,5)[0]),'기존219 역사 실루엣 exact');flash=np.zeros_like(body);flash[binary_dilation(body>0,iterations=2)]=7;flash[body>0]=6;Image.fromarray(flash).save(out/'effect_219_indices.png');Image.fromarray(body).save(out/'body_217_indices.png');rows.append(('219',[('current silhouette',a.composite(219,15)[0]),('current body',a.composite(217,15)[0]),('new silhouette candidate',a.rgba(flash,16)),('new body',a.rgba(body))]));helper.grid(rows[:1],out/'comparison_1.png',5);helper.grid(rows[1:2],out/'comparison_2.png',4);helper.grid(rows[2:],out/'comparison_3.png',7)
 write(out/'manifest.json',{'current_sha256':digest(current),'historical_sha256':digest(historical),'swap_seed_sha256':digest(swap),'source_body_sha256':sha(body.tobytes()),'frames':proof,'flash219':{'rule':'Manhattan2 index7 외곽 + 새217 alpha index6','old_body_count':int((seed>0).sum()),'new_body_count':int((body>0).sum()),'new_flash_count':int((flash>0).sum()),'historical_old_flash_exact':True,'new_indexed_sha256':sha(flash.tobytes())},'scope':'역사 규칙 재현 후 새몸체를 대입한 별도 효과후보. 현재 효과1084/2683 texel 전체 byte보존이라고 주장하지 않음. 원래 에너지 바깥 모양/색/원점은기존몸팽창영역과새몸밖에서exact. 실제CLUT시간변화/원MIPS/원표/ARC 미검증.','native_packed':False,'runtime_verified':False});print(json.dumps(proof))
if __name__=='__main__':main()
