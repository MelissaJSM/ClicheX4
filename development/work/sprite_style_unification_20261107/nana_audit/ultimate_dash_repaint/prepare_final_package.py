"""검사된 대시/노바 후보를 새 최종 준비 경로로 모으되 동결은 별도로 수행한다."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
FINAL='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0'
def main():
 out=D/'packed_dash_candidate_v1';need(not out.exists(),'Fresh output');source=D/'packed_dash_nova_diagnostic_v3';parent=D.parent/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC';need(digest(source/'PL02_U.ARC')==FINAL and digest(D/'reproduction_nova_v1/PL02_U.ARC')==FINAL,'Exact reproduction');ev=json.loads((source/'extended_verification.json').read_text('utf8'));need(ev['passed']and ev['candidate_sha256']==FINAL,'Extended verification');out.mkdir();shutil.copy2(source/'PL02_U.ARC',out/'PL02_U.ARC')
 for file in('verification.json','extended_verification.json','nova_readback.png'):shutil.copy2(source/file,out/file)
 a=Archive(parent.read_bytes());b=Archive((out/'PL02_U.ARC').read_bytes())
 for i,refs in enumerate(((67,69,71),(73,75,77),(79,81,83),(93,))):
  rows=[]
  for n in refs:
   labels=('연결93','연결94')if n==93 else('몸체','사격')
   rows.append((f'{n}/{n+1}',[('후폼 대기',b.composite(0)[0]),(labels[0],b.composite(n)[0]),(labels[1],b.composite(n+1)[0]),('전폼 대기',b.composite(0,15)[0]),(labels[0],b.composite(n,15)[0]),(labels[1],b.composite(n+1,15)[0])]))
  helper.grid(rows,out/f'readback_{i+1}.png',5)
 cyc=json.loads((D/'native_cycle_v1/manifest.json').read_text('utf8'))
 for aid in(16,17,18,19,128,129):
  seq=cyc['cases'][str(aid)];w=96;h=80;scale=2;sheet=Image.new('RGB',(w*scale*len(seq),32+h*scale*2),(184,194,201));draw=ImageDraw.Draw(sheet)
  for i,q in enumerate(seq):
   n=q['ref'];draw.text((i*w*scale+4,4),f'{n} / {q["calls"]} calls',fill=(20,20,20))
   for j,mask in enumerate((15,0)):
    im=b.composite(n,mask)[0].crop((112,112,208,192)).resize((w*scale,h*scale),Image.Resampling.NEAREST);sheet.paste(im,(i*w*scale,32+j*h*scale),im)
  sheet.save(out/f'timeline_{aid}.png')
 write(out/'proposal.json',{'project':'ver_rin_nana','baseline_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','parent_arc_sha256':sha(a.data),'files':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa','working_parent_before':sha(a.data),'after':FINAL}},'changed_from_working_parent':{'dash_both_costumes':list(range(67,85))+[93,94],'nova_head_only':[217,218,220]},'candidate_only':True,'freeze_pending':'원MIPS 및 독립 읽기 검사 이후 별도 FROZEN 생성'})
 write(out/'reproduction.json',{'passed':True,'candidate_sha256':FINAL,'dash_intermediate_sha256':digest(D/'reproduction_dash_v1/PL02_U.ARC'),'separate_final_sha256':digest(D/'reproduction_nova_v1/PL02_U.ARC'),'scripts':{p.name:digest(p)for p in [D/'pack_native.py',D/'pack_nova_head.py',D/'pack_single_safe.py',D/'repack_identical.py']},'source_guard':sha(a.data),'independent_readback_pending':True})
 print(json.dumps({'out':str(out),'after':FINAL,'proposal_sha256':digest(out/'proposal.json')}))
if __name__=='__main__':main()
