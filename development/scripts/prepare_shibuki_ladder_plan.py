"""미국판 사다리 일반/사격 프레임·공유 타일 읽기 전용 조사."""
import argparse,json,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import sha256
from src.psx_player import composition_frame

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',choices=('ver_buki_riko','ver_rin_nana'),default='ver_buki_riko');args=p.parse_args();character='nana' if args.project=='ver_rin_nana' else 'shibuki'
 source=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z';inv=json.loads((source/'inventory.json').read_text());parts=(source/'composition_entry.bin').read_bytes()
 assert sha256((source/'original.arc').read_bytes())==inv['archive']['sha256']
 out=ROOT/'work'/args.project/(character+'_art')/'ladder_v1';out.mkdir(exist_ok=True,parents=True)
 animations={str(n):inv['animations'][n] for n in (27,28,29,30,31,32,92,93)};frames=sorted({s['frame'] for a in animations.values() for s in a['steps']});records=[]
 sheet=Image.new('RGB',(5*264,3*264),'#28394b');dr=ImageDraw.Draw(sheet)
 for i,n in enumerate(frames):
  r=inv['base_frames'][n];body={q['tile'] for q in r['composition']['parts']};aliases=inv['stream_sharing'][str(r['offset'])]
  armor={q['tile'] for b in range(5,9) for q in composition_frame(parts,b,n)['parts']}
  assert not body&armor
  records.append({'frame':n,'aliases':aliases,'budget':r['compressed_end']-r['offset'],'tile_count':r['tile_count'],'part_count':len(r['composition']['parts']),'writable':sorted(body),'armor_tiles':sorted(armor),'bounds':r['bounds'],'parts':r['composition']['parts']})
  x=i%5*264;y=i//5*264;im=Image.open(source/r['image']).convert('RGBA');im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);sheet.paste(im,(x+132+r['bounds'][0]*3,y+114+r['bounds'][1]*3),im);dr.text((x+8,y+8),f'X {n:03d}',fill='white')
 sheet.save(out/'original_ladder_reference.png')
 plan={'source_inventory':str((source/'inventory.json').relative_to(ROOT)),'animations':animations,'frames':frames,'groups':records,'evidence':['work/research/decomp/src/main/player_enter.c:462','work/research/decomp/src/main/player.c:704','work/research/decomp/src/main/player_special.c:506','US EXE animation table'],'runtime_verified':False}
 (out/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8');print(json.dumps([{k:v for k,v in r.items() if k!='parts'} for r in records]))
if __name__=='__main__':main()
