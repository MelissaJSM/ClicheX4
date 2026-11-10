"""다음 노바/연결213~220의 실제 현재 층과 원US 공유를 읽기 추출한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
N=Path(__file__).resolve().parent;ROOT=N.parents[2];D=N/'ultimate_nova_repaint'
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from scripts.export_sprite_playback import read_disc
from scripts.prepare_shibuki_ultimate_production import records
from src.psx_player import composition_frame,bank_offsets
def bbox(z):
 y,x=np.nonzero(z);return None if not len(x)else[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)]
def main():
 out=D/'existing_v1';need(not(out/'report.json').exists(),'새보고');out.mkdir(parents=True,exist_ok=True);p=N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC';need(digest(p)=='94326933d0dd62ccd7a5904019cae9fd36fc068a6acde8941d6bf8ff363666ca','동결부모');a=Archive(p.read_bytes());c=Archive((N/'ultimate_hover_repaint/packed_hover_candidate_v1/PL02_U.ARC').read_bytes());us=Archive(read_disc(ROOT/'MegaMan X4.bin',['PL02_U.ARC'])['PL02_U.ARC']);pbs=(0,5,6,7,8);proof=[];fullrows=[];layerrows=[]
 for n in range(213,221):
  f=a.banks[0]['frames'][n];layers={};rawowners=[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']]
  for pb in pbs:
   z=a.layer(n,pb)[0];need(np.array_equal(z,c.layer(n,pb)[0]),'호버 후보에서비대상불변');Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png');rr=composition_frame(a.c,pb,n);owners=[]
   for bank in range(len(bank_offsets(a.c))):
    count=composition_frame(a.c,bank,0)['bank_frame_count']
    for ref in range(count):
     q=composition_frame(a.c,bank,ref)
     if {p['record_offset']for p in q['parts']}&{p['record_offset']for p in rr['parts']}:owners.append([bank,ref])
   layers[str(pb)]={'indexed_sha256':sha(z.tobytes()),'opaque':int((z>0).sum()),'bbox':bbox(z),'indices':np.unique(z[z>0]).tolist(),'parts':rr['parts'],'shared_record_owners':owners}
  fullrows.append((str(n),[('idle jacket',a.composite(0,15)[0]),('current mask15',a.composite(n,15)[0]),('idle acquired',a.composite(0,0)[0]),('current mask0',a.composite(n,0)[0])]))
  layerrows.append((str(n),[(f'layer{pb}',a.rgba(a.layer(n,pb)[0],0 if pb==0 else 16))for pb in pbs]))
  proof.append({'ref':n,'tile_count':f['tile_count'],'raw_offset':f['offset'],'raw_owners':rawowners,'layers':layers,'original_us_tile_count':us.banks[0]['frames'][n]['tile_count'],'actual_mask_note':'원코드217이상 mask15; 213..216은일반의상정책'if n>=217 else'일반의상정책, 실제도달상태별 확인 필요'})
 for i in range(0,8,2):helper.grid(fullrows[i:i+2],out/f'comparison_{i//2+1}.png',5);helper.grid(layerrows[i:i+2],out/f'layers_{i//2+1}.png',5)
 pairs=[]
 for x in range(213,221):
  for y in range(x+1,221):
   same=[pb for pb in pbs if np.array_equal(a.layer(x,pb)[0],a.layer(y,pb)[0])]
   if same:pairs.append({'a':x,'b':y,'identical_layers':same})
 meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));seq=[q for q in meta['characters']['nana']['forms']['ultimate_after']['animations']if any(s['frame_ref']in range(213,221)for s in q['steps'])]
 write(out/'report.json',{'source_arc':p.relative_to(ROOT).as_posix(),'source_sha256':sha(a.data),'hover_candidate_nova_layers_unchanged':True,'original_us_arc_sha256':sha(us.data),'refs':list(range(213,221)),'frames':proof,'identical_layer_pairs':pairs,'related_original_tables':seq,'scope':'현재8참조 읽기만 수행. 새원화/수용/게임실행 검증은 아니다.','read_only':True});print(json.dumps({'frames':8,'tables':[q['id']for q in seq],'report':str(out/'report.json')}))
if __name__=='__main__':main()
