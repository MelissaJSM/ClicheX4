"""원화와 현재 네이티브 이미지의 출처 대조. 제작 자원은 쓰지 않는다."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from collect import SOURCE,OUT,EXPECTED,digest
from scripts.discover_inputs import DiscReader
from scripts.export_x_consistency import Archive
FONT=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
def clean(im):
 im=im.convert('RGBA');bb=im.getbbox()
 if not bb:return np.zeros((1,1,4),np.uint8)
 a=np.array(im.crop(bb));a[a[:,:,3]==0]=0;return a
def main():
 assert digest(SOURCE)==EXPECTED
 names=('PL00_U.ARC','PL02_U.ARC','MOJIPAT.ARC','LOAD_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC')
 with SOURCE.open('rb')as f:
  d=DiscReader(f,SOURCE.stat().st_size);rs={r['name'].split(';')[0]:r for r in d.inspect()['files']};assets={n:d.read(rs[n]['lba'],rs[n]['size'])for n in names}
 arcs={n:Archive(assets[n])for n in('PL00_U.ARC','PL02_U.ARC')}
 source_specs=[
  ('base_run7','base',7,'work/ver_rin_nana/nana_art/run_v1/normalized05/art.json',7),
  ('base_cyclone98','base',98,'work/ver_rin_nana/nana_art/special_v1/production01/art.json',98),
  ('base_ladder144','base',144,'work/ver_rin_nana/nana_art/ladder_v1/production01/art.json',144),
  ('fourth_ladder144','fourth',144,'work/ver_rin_nana/nana_fourth_armor/ladder_art_v5/layers.json',144),
  ('ultimate_dash69','ultimate_before',69,None,69),
 ]
 specs=[];current={}
 for sid,form,ref,meta,n in source_specs:
  arc=arcs['PL02_U.ARC'if form.startswith('ultimate')else'PL00_U.ARC'];mask=0 if form=='base'else 15
  current[sid]=arc.composite(ref,mask,2)[0];idle=arc.composite(0,mask,2)[0]
  if meta:
   data=json.loads((ROOT/meta).read_text('utf8'));p=Path(data['source']);p=p if p.is_absolute()else ROOT/p
   rows=data.get('registrations',data.get('registration',data.get('frames',[])));q=next(q for q in rows if q['frame']==n);box=q['source_box'];raw=Image.open(p).convert('RGBA')
   if 'source_cell'in q:
    i=q['source_cell'];raw=raw.crop((i%3*raw.width//3,i//3*raw.height//3,(i%3+1)*raw.width//3,(i//3+1)*raw.height//3))
   crop=raw.crop(box)
   assert digest(p)==data['source_sha256']
  else:
   p=ROOT/'work/ver_rin_nana/nana_ultimate_armor/dash_hair_v1/generated.png';raw=Image.open(p).convert('RGBA');q={'source_cell':1};box=[raw.width//4,0,raw.width//2,raw.height//2];crop=raw.crop(box);bb=crop.getbbox();crop=crop.crop(bb)
  out=OUT/'provenance';out.mkdir(exist_ok=True);crop.save(out/f'{sid}_source_crop.png')
  board=Image.new('RGB',(960,360),(183,193,199));draw=ImageDraw.Draw(board)
  draw.text((8,8),f'{sid} / 원화(비게임 크기) → 현재 / 대기 기준',font=FONT,fill='#102030')
  picture=crop.copy();picture.thumbnail((310,300),Image.Resampling.NEAREST);board.paste(picture,(5+(310-picture.width)//2,45),picture)
  for i,im in enumerate((current[sid],idle),1):
   piece=im.crop((110,105,210,185)).resize((300,240),Image.Resampling.NEAREST);board.paste(piece,(i*320,65),piece)
  fp=out/f'{sid}_comparison.png';board.save(fp)
  specs.append({'id':sid,'form':form,'ref':ref,'source':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'metadata':meta,'registration':q,'crop':box,'sheet':fp.relative_to(ROOT).as_posix(),'new_art':False})
 # Independent comparison with retained indexed/registered PNGs. Bounding-box
 # translation is ignored only here; this is artwork provenance, not an anchor test.
 candidates=[
  ('base_run7','work/ver_rin_nana/nana_art/run_v1/normalized05/run_007.png'),
  ('base_cyclone98','work/ver_rin_nana/nana_art/special_v1/production01/frame_098.png'),
  ('base_ladder144','work/ver_rin_nana/nana_art/ladder_v1/production01/frame_144.png'),
  ('fourth_ladder144','work/ver_rin_nana/nana_fourth_armor/ladder_art_v5/full_144.png'),
  ('ultimate_dash69','work/ver_rin_nana/nana_ultimate_armor/dash_hair_packed_v3/ultimate_069.png'),
 ]
 exact=[]
 for sid,p in candidates:
  path=ROOT/p;a=clean(current[sid]);b=clean(Image.open(path));same=a.shape==b.shape and np.array_equal(a,b)
  exact.append({'id':sid,'retained_native':p,'sha256':digest(path),'same_rgba_bbox':bool(same),'current_bbox_shape':list(a.shape),'retained_bbox_shape':list(b.shape),'different_pixels':int(np.count_nonzero(np.any(a!=b,axis=2)))if a.shape==b.shape else None})
 old=json.loads((ROOT/'work/sprite_reaudit_20261106/nana/manifest.json').read_text('utf8'))
 ui={n:{'current_sha256':hashlib.sha256(assets[n]).hexdigest(),'previous_sha256':old['asset_sha256'][n],'unchanged':hashlib.sha256(assets[n]).hexdigest()==old['asset_sha256'][n]}for n in names[2:]}
 extra=['work/ver_rin_nana/nana_art/run_v1/firing_generated.png','work/ver_rin_nana/nana_art/air_v1/generated.png','work/ver_rin_nana/nana_art/dash_v1/generated.png','work/ver_rin_nana/nana_art/run_v1/generated.png','work/ver_rin_nana/nana_ultimate_armor/dash_v1/generated.png']
 report={'source_bin':str(SOURCE.relative_to(ROOT)),'source_bin_sha256':EXPECTED,'source_originals':specs,'retained_native_comparison':exact,'ui_identity_to_previous_review':ui,'additional_source_hashes':{p:digest(ROOT/p)for p in extra}}
 (OUT/'provenance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');assert digest(SOURCE)==EXPECTED
 print(json.dumps({'retained':exact,'ui_unchanged':all(q['unchanged']for q in ui.values())}))
if __name__=='__main__':main()
