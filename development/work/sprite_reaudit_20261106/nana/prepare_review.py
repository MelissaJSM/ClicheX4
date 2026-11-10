"""Current Nana art review sheets; no image design changes or game writes."""
from pathlib import Path
import hashlib,json,math,struct,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader
from scripts.export_x_consistency import Archive,GROUPS,GROUP_NAMES,metrics
from scripts.build_sprite_consistency_gallery import normalized
from scripts.prepare_riko_ui import entry
from scripts.ultimate_costume_swap_ui import ui_canvas
from scripts.verify_shibuki_save_icon import icon,rgba as word_rgba
from src.psx_player import composition_frame
from src.psx_ui_atlas import local_composition
from src.psx_static_effect import compose_static
OUT=Path(__file__).parent;SHA='dcdf175eb93014da90d1bfb429774b48533e1c156e289a3ac49f969ea7a0f9c7'
SOURCE=ROOT/'out/ver_rin_nana/hurt_capsule_fix_20261106_v1/rin_nana.bin'
FONT=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',13)
FORMS=[('base','기본','PL00_U.ARC',0),('fourth','포스','PL00_U.ARC',15),('ultimate_before','얼티밋 전 재킷','PL02_U.ARC',15),('ultimate_after','얼티밋 후 수영복','PL02_U.ARC',0)]
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def canvas(im,origin=80):
 result=Image.new('RGBA',(384,384));result.alpha_composite(im,(160-origin,160-origin));return result
def rgba(a,words):
 table=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]+[0 if i==0 else 255]for i,w in enumerate(words)],np.uint8)
 return Image.fromarray(table[a])
def grid(rows,path,scale=2):
 boxes=[im.getbbox()for _,items in rows for _,im in items if im.getbbox()];box=(min([144]+[b[0]for b in boxes])-3,min([112]+[b[1]for b in boxes])-3,max([176]+[b[2]for b in boxes])+3,max([183]+[b[3]for b in boxes])+3)
 width,height=(box[2]-box[0])*scale,(box[3]-box[1])*scale;cw,ch=width+8,height+42;cols=max(len(items)for _,items in rows)
 board=Image.new('RGB',(cw*cols,ch*len(rows)),(183,193,199));draw=ImageDraw.Draw(board)
 for r,(label,items)in enumerate(rows):
  for i,(ref,im)in enumerate(items):
   x,y=i*cw,r*ch;draw.text((x+3,y+2),label,font=FONT,fill='#101820');draw.text((x+3,y+18),ref,font=FONT,fill='#25313d')
   if i==0:draw.rectangle((x,y,x+cw-1,y+ch-1),outline='#416d8a')
   p=im.crop(box).resize((width,height),Image.Resampling.NEAREST);board.paste(p,(x,y+40),p)
 board.save(path);return {'path':path.relative_to(ROOT).as_posix(),'size':list(board.size),'scale':scale,'world_window':[v-160 for v in box],'rows':[{'form':s,'refs':[r for r,_ in v]}for s,v in rows]}
def main():
 assert digest(SOURCE)==SHA
 names=('PL00_U.ARC','PL02_U.ARC','SLUS_005.61','ST0E_U1.ARC','COL0E_U1.ARC','MOJIPAT.ARC','LOAD_U.ARC')
 with SOURCE.open('rb')as f:
  d=DiscReader(f,SOURCE.stat().st_size);rs={r['name'].split(';')[0]:r for r in d.inspect()['files']if not r['directory']};assets={n:d.read(rs[n]['lba'],rs[n]['size'])for n in names}
 gallery=normalized('nana');previous={q['id']:q for q in gallery['frames']};arcs={n:Archive(assets[n])for n in('PL00_U.ARC','PL02_U.ARC')};images={};frames=[];matches=[];unreconstructed=[];armdiff=[]
 for form,label,name,mask in FORMS:
  arc=arcs[name]
  for ref in range(237):
   actual=15 if form=='ultimate_after'and 217<=ref<=230 else mask
   try:im,_=arc.composite(ref,actual,2)
   except(ValueError,IndexError):
    assert ref in(105,*range(175,183));im=Image.new('RGBA',(384,384));unreconstructed.append([form,ref])
   images[form,ref]=im;row={'form':form,'ref':ref,'mask':actual,'rgba_sha256':sha(im.tobytes()),**metrics(im)};frames.append(row)
   p=previous[f'{form}_{ref:03}'];path=ROOT/'out/sprite_consistency_20261105'/p.get('revised_path',p['path']);old=Image.open(path).convert('RGBA');assert old.tobytes()==im.tobytes(),(form,ref)
   matches.append([form,ref])
   if form=='fourth'and ref not in(105,*range(175,183)):
    alt=arc.composite(ref,actual,1)[0]
    if alt.tobytes()!=im.tobytes():armdiff.append(ref)
 directory=OUT/'main';directory.mkdir(exist_ok=True);sheets=[]
 for group,refs in GROUPS.items():
  for start in range(0,len(refs),12):
   sub=refs[start:start+12];rows=[(label,[('idle 0',images[form,0])]+[(f'{ref:03}',images[form,ref])for ref in sub])for form,label,_,_ in FORMS]
   result=grid(rows,directory/f'{group}_{start//12:02}.png');result.update(group=group,refs=sub);sheets.append(result)
 partial_refs=[0,12,32,33,41,55,62,69,84,85,95,98,100,104,106,115,120,133,140,141,142,148,150,156,161,162,183,217,223,230,231,233]
 directory=OUT/'partial';directory.mkdir(exist_ok=True);partial=[]
 for start in range(0,len(partial_refs),4):
  refs=partial_refs[start:start+4];rows=[]
  for ref in refs:
   rows.append((f'ref {ref:03}',[(f'mask {mask:X}',arcs['PL00_U.ARC'].composite(ref,mask,2)[0])for mask in range(16)]))
  r=grid(rows,directory/f'masks_{start//4:02}.png');r['refs']=refs;r['masks']=list(range(16));partial.append(r)
 if armdiff:
  rows=[]
  for ref in armdiff[:12]:rows.append((f'ref {ref:03}',[(f'arm{arm}',arcs['PL00_U.ARC'].composite(ref,15,arm)[0])for arm in(1,2)]))
  sheets.append(grid(rows,OUT/'armtype_difference.png'))
 menu,tex=assets['MOJIPAT.ARC'],entry(assets['LOAD_U.ARC'],0x10008);ui=[]
 for arm in(1,2):
  ui.append((f'save arm{arm}',[(f'mask {mask:X}',canvas(word_rgba(icon(menu,tex,mask,arm))))for mask in range(16)]))
 ui.append(('save ultimate',[('pre jacket',canvas(word_rgba(ui_canvas(menu,tex,52,30)))),('post swimsuit',canvas(word_rgba(ui_canvas(menu,tex,53,31))))]))
 save=grid(ui,OUT/'save_all.png',3)
 texture=entry(assets['ST0E_U1.ARC'],0x10102);parts=entry(assets['ST0E_U1.ARC'],10);palette=entry(assets['COL0E_U1.ARC'],5);items=[]
 for ref in range(composition_frame(parts,2,0)['bank_frame_count']):
  cp=composition_frame(parts,2,ref);im=Image.new('RGBA',(384,384))
  for p in cp['parts']:
   px,size,bb,_=compose_static(texture[90112:],local_composition({**cp,'parts':[p]}));words=struct.unpack_from('<16H',palette,(16+p['clut'])*32);part=rgba(np.frombuffer(px,np.uint8).reshape(size[1],size[0]),words);im.alpha_composite(part,(160+bb[0],160+bb[1]))
  items.append((f'select {ref}',im))
 selection=grid([('현재 선택',[('game idle',images['base',0])]+items)],OUT/'selection_all.png',4)
 report={'source':SOURCE.relative_to(ROOT).as_posix(),'sha256':SHA,'asset_sha256':{n:sha(a)for n,a in assets.items()},'frames':frames,'exact_current_vs_gallery_with_revised':len(matches),
  'unreconstructed_reserved':unreconstructed,'main_sheets':sheets,'partial_sheets':partial,'partial_refs':partial_refs,'partial_masks_visually_reviewable':len(partial_refs)*16,
  'force_armtype_pixel_differences':armdiff,'save':save,'selection':selection,'runtime_verified':False,'art_modified':False,'viewed_sheets_not_recorded_by_export':True}
 write(OUT/'manifest.json',report);assert digest(SOURCE)==SHA
 print(json.dumps({'main_sheets':len(sheets),'gallery_matches':len(matches),'partial_sheets':len(partial),'armtype_difference_refs':armdiff,'selection_refs':len(items)}),flush=True)
if __name__=='__main__':main()
