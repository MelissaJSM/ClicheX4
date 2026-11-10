"""체력 1/3 미만 대기 애니메이션6의 공유6참조를 읽기 전용 조사."""
import argparse,json,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.psx_player import composition_frame
from scripts.discover_inputs import sha256

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',choices=('ver_buki_riko','ver_rin_nana'),default='ver_buki_riko');a=p.parse_args();character='nana' if a.project=='ver_rin_nana' else 'shibuki'
 source=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z';inv=json.loads((source/'inventory.json').read_text());parts=(source/'composition_entry.bin').read_bytes();assert sha256((source/'original.arc').read_bytes())==inv['archive']['sha256']
 out=ROOT/'work'/a.project/(character+'_art')/'low_hp_v1';out.mkdir(exist_ok=True,parents=True);records=[];sheet=Image.new('RGB',(6*264,264),'#28394b');dr=ImageDraw.Draw(sheet)
 for i,n in enumerate(range(120,126)):
  r=inv['base_frames'][n];body={q['tile'] for q in r['composition']['parts']};armor={q['tile'] for b in range(5,9) for q in composition_frame(parts,b,n)['parts']};assert not body&armor
  records.append({'frame':n,'aliases':inv['stream_sharing'][str(r['offset'])],'budget':r['compressed_end']-r['offset'],'tile_count':r['tile_count'],'part_count':len(r['composition']['parts']),'writable':sorted(body),'armor_tiles':sorted(armor),'bounds':r['bounds'],'parts':r['composition']['parts']})
  im=Image.open(source/r['image']).convert('RGBA');im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);sheet.paste(im,(i*264+132+r['bounds'][0]*3,114+r['bounds'][1]*3),im);dr.text((i*264+8,8),str(n),fill='white')
 sheet.save(out/'original_reference.png');(out/'plan.json').write_text(json.dumps({'source_inventory':str((source/'inventory.json').relative_to(ROOT)),'groups':records,'animation':inv['animations'][6],'condition_evidence':'work/research/decomp/src/main/player_common.c:1101 hp < max_hp/3','runtime_verified':False},indent=2));print(json.dumps([{k:v for k,v in r.items() if k!='parts'} for r in records]))
if __name__=='__main__':main()
