"""미국판 X의 점프·낙하·착지와 공유 사격 참조를 읽기 전용 조사한다."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import sha256
from src.psx_player import composition_frame

def main():
 source=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z';inv=json.loads((source/'inventory.json').read_text());parts=(source/'composition_entry.bin').read_bytes()
 if sha256((source/'original.arc').read_bytes())!=inv['archive']['sha256']:raise ValueError('Original extraction changed')
 out=ROOT/'work/ver_buki_riko/shibuki_art/air_v1';out.mkdir(exist_ok=True);pairs=[]
 sheet=Image.new('RGB',(6*264,4*264),'#28394b');draw=ImageDraw.Draw(sheet)
 for i,n in enumerate(range(33,55,2)):
  a,b=inv['base_frames'][n:n+2]
  if a['offset']!=b['offset'] or inv['stream_sharing'][str(a['offset'])]!=[[0,n],[0,n+1]]:raise ValueError('Unexpected alias')
  aa={q['tile'] for q in a['composition']['parts']};bb={q['tile'] for q in b['composition']['parts']}
  armor={str(bank):sorted({q['tile'] for k in (n,n+1) for q in composition_frame(parts,bank,k)['parts']}) for bank in (5,6,7,8)}
  if (aa|bb)&{t for ts in armor.values() for t in ts}:raise ValueError('Base overlaps armor')
  pairs.append({'frames':[n,n+1],'stream':a['offset'],'budget':a['compressed_end']-a['offset'],'tile_count':a['tile_count'],'common_base_tiles':sorted(aa&bb),'nonshoot_only_tiles':sorted(aa-bb),'shoot_only_tiles':sorted(bb-aa),'armor_overlay_tiles':armor,'part_counts':[len(a['composition']['parts']),len(b['composition']['parts'])],'bounds':[a['bounds'],b['bounds']]})
  for row,q in enumerate((a,b)):
   x=(i%6)*264;y=((i//6)*2+row)*264;pic=Image.open(source/q['image']).convert('RGBA');pic=pic.resize((pic.width*3,pic.height*3),Image.Resampling.NEAREST)
   sheet.paste(pic,(x+132+q['bounds'][0]*3,y+114+q['bounds'][1]*3),pic);draw.text((x+8,y+8),f"X {q['index']:03d}",fill='white')
 sheet.save(out/'original_air_reference.png')
 plan={'task':'x_shibuki','source_inventory':str((source/'inventory.json').relative_to(ROOT)),'frames':list(range(33,55)),'animations':{str(n):inv['animations'][n] for n in (10,11,12,122,123,124)},'paired_frames':pairs,'evidence':'work/research/decomp/src/main/player.c:236,277,292; US EXE animations in extraction','art_produced':False,'runtime_verified':False}
 (out/'plan.json').write_text(json.dumps(plan,indent=2));print(json.dumps({'out':str(out),'pairs':pairs}))

if __name__=='__main__':main()
