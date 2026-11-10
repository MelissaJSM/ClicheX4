"""나나 공중 제작용 원작22참조의 공유·용량·시간표를 읽기 전용 추출한다."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import INV,write
from scripts.project import digest
from src.psx_player import composition_frame

def main():
 inv=json.loads(INV.read_text('utf8'));source=INV.parent;parts=(source/'composition_entry.bin').read_bytes()
 if digest(source/'original.arc')!=inv['archive']['sha256']:raise ValueError('Original extraction changed')
 out=ROOT/'work/ver_rin_nana/nana_art/air_v1';out.mkdir(parents=True,exist_ok=True);pairs=[]
 board=Image.new('RGB',(6*264,4*264),'#28394b');draw=ImageDraw.Draw(board)
 for i,n in enumerate(range(33,55,2)):
  a,b=inv['base_frames'][n:n+2]
  if a['offset']!=b['offset'] or inv['stream_sharing'][str(a['offset'])]!=[[0,n],[0,n+1]]:raise ValueError('Unexpected air alias')
  aa={p['tile'] for p in a['composition']['parts']};bb={p['tile'] for p in b['composition']['parts']}
  armor={str(bank):sorted({p['tile'] for k in (n,n+1) for p in composition_frame(parts,bank,k)['parts']}) for bank in (5,6,7,8)}
  if (aa|bb)&{t for ts in armor.values() for t in ts}:raise ValueError('Armor conflict')
  pairs.append({'frames':[n,n+1],'stream':a['offset'],'budget':a['compressed_end']-a['offset'],'tile_count':a['tile_count'],'common_base_tiles':sorted(aa&bb),'nonshoot_only_tiles':sorted(aa-bb),'shoot_only_tiles':sorted(bb-aa),'armor_overlay_tiles':armor,'part_counts':[len(a['composition']['parts']),len(b['composition']['parts'])],'bounds':[a['bounds'],b['bounds']]})
  for j,q in enumerate((a,b)):
   x,y=i%6*264,(i//6*2+j)*264;pic=Image.open(source/q['image']).convert('RGBA');pic=pic.resize((pic.width*3,pic.height*3),Image.Resampling.NEAREST);board.paste(pic,(x+132+q['bounds'][0]*3,y+114+q['bounds'][1]*3),pic);draw.text((x+8,y+8),f"X {q['index']:03d}",fill='white')
 board.save(out/'native_air_reference.png')
 write(out/'plan.json',{'task':'x_nana','source_inventory':INV.relative_to(ROOT).as_posix(),'frames':list(range(33,55)),'order':list(range(33,55,2)),'animations':{str(n):inv['animations'][n] for n in (10,11,12,122,123,124)},'paired_frames':pairs,'runtime_verified':False})
 print(json.dumps({'output':str(out),'pairs':[(p['frames'],p['budget'],p['part_counts']) for p in pairs]}))
if __name__=='__main__':main()
