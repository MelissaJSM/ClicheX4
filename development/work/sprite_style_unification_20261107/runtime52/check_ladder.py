"""Read-only native framebuffer comparison; contact sheets contain actual captures."""
from pathlib import Path
import argparse,hashlib,json,sys
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from src.epsxe_state import framebuffer,match_sprite
p=argparse.ArgumentParser();p.add_argument('--before',action='store_true');args=p.parse_args();prefix='preladder_'if args.before else'ladder_';tag='before_'if args.before else'';mask=15 if args.before else 0
src=json.loads((W/'staging_rn_v44.json').read_text('utf8'))['resources']['PL02_U.ARC']
data=(ROOT/src['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==src['after'];arc=Archive(data)
refs=[*range(143,156),183];sprites={n:arc.composite(n,mask)[0] for n in refs};sprites={n:im.crop(im.getbbox())for n,im in sprites.items()}
rows=[];unique={};best={};totals={n:[0,0,0]for n in refs}
for p in sorted(O.glob(prefix+'*/evidence.json')):
 e=json.loads(p.read_text('utf8'))
 for s in e['samples']:
  n=s['frame'];totals[n][0]+=1;totals[n][1]+=int(s['native_decode_exact']);totals[n][2]+=int(s['gpu_exact'])
  video=(p.parent/f'vram{s["index"]:02}.bin').read_bytes();sig=hashlib.sha256(video).hexdigest()
  if sig in unique:continue
  matches=[]
  for page in(0,240):
   screen=framebuffer(video,0,page)
   for ref in [n]+[r for r in refs if r!=n]:
    hits=match_sprite(screen,sprites[ref])
    for hit in hits:
     row={'source':str(p.parent.relative_to(O)),'sample':s['index'],'player_ref':n,'displayed_ref':ref,'page':page,**hit};matches.append(row)
     key=(ref,hit['flip_x'])
     if key not in best:best[key]=(row,screen)
  unique[sig]=matches;rows.extend(matches)
report={'BIN_sha256':e['bin_sha256'],'source_arc_sha256':src['after'],'actual_gameplay':True,'samples_by_ref':totals,'unique_vram_samples':len(unique),'unique_vram_with_full_pixel_match':sum(bool(x)for x in unique.values()),'matched_display_refs':sorted({r['displayed_ref']for r in rows}),'matches':rows,'memory_written':False,'all_new_refs_observed':all(totals[n][0]for n in(148,149,150,151,152,153,155)),'all_new_refs_full_pixel_match':all(any(r['displayed_ref']==n for r in rows)for n in(148,149,150,151,152,153,155))}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',14);panels=[]
for ref in sorted({k[0]for k in best}):
 for key in sorted(k for k in best if k[0]==ref):
  row,screen=best[key];pic=sprites[ref];x,y=row['x'],row['y'];rect=(max(0,x-14),max(0,y-10),min(320,x+pic.width+14),min(240,y+pic.height+10));crop=screen.crop(rect).resize(((rect[2]-rect[0])*3,(rect[3]-rect[1])*3),Image.Resampling.NEAREST)
  board=Image.new('RGB',(320,250),'#18202b');d=ImageDraw.Draw(board);d.text((8,5),f'실제 화면 · {ref} · 반전 {key[1]}',font=font,fill='white');d.text((8,27),f'{row["opaque_pixels_equal"]} 불투명 픽셀 전체 일치',font=font,fill='#b4e2d8');board.paste(crop,(max(0,(320-crop.width)//2),52));panels.append(board)
for first in range(0,len(panels),6):
 sheet=Image.new('RGB',(960,500),'#18202b')
 for i,panel in enumerate(panels[first:first+6]):sheet.paste(panel,(i%3*320,i//3*250))
 sheet.save(O/f'{tag}actual_ladder_{first//6+1:02}.png')
report['costume']='before'if args.before else'after'
(O/f'{tag}ladder_screen_matches.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({k:v for k,v in report.items()if k!='matches'}))
