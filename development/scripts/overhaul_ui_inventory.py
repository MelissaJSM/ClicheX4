"""통합 수정 UI의 실제 디스크 자원·조립·색상표를 읽기 전용으로 추출한다."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,sha256
from scripts.project import digest
from scripts.prepare_riko_ui import entry
from scripts.prepare_hud_emblems import composed,render_pixels,inner_slice
from scripts.prepare_ui_revision import pause_background
from scripts.build_rin_pause import composition
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static
D=ROOT/'work/overhaul_20261105/ui'
BUILDS={
 'ver_buki_riko':('out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin','8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a'),
 'ver_rin_nana':('out/ver_rin_nana/nana_ultimate_nova_20261104T185708218838Z/rin_nana.bin','5dd089c181cd141955f8e98e3a6b028f24253f2ca4179ed34e194f6a276047f0'),
 'original':('MegaMan X4.bin','3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b')}
def load(project):
 path,expected=BUILDS[project];p=ROOT/path
 if digest(p)!=expected:raise ValueError('Source differs')
 with p.open('rb')as f:
  d=DiscReader(f,p.stat().st_size);rr=d.inspect()['files'];records={x['path'].split('/')[-1].split(';')[0]:x for x in rr}
  wanted=[n for n in records if n in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','SLUS_005.61','LOAD_U.ARC','MOJIPAT.ARC','ST0E_U0.ARC') or n.startswith('COL')]
  raw={n:d.read(records[n]['lba'],records[n]['size']) for n in wanted}
 return raw,records
def main():
 D.mkdir(parents=True,exist_ok=True);out=D/'inventory';out.mkdir(exist_ok=False);allmeta={};hudimgs=[];portraits=[]
 for project in BUILDS:
  raw,rr=load(project);folder=out/project;folder.mkdir();meta={'files':{n:{**rr[n],'sha256':sha256(v)}for n,v in raw.items()},'hud':{},'pause':{},'life':{}}
  pal=entry(raw['COL00_0X.ARC'],5)[17*32:18*32]
  for name in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
   arc=raw[name];g=entry(arc,0x10206);p=entry(arc,3);a,sz,bb,_=composed(g,aliased_composition(p,1,69));im=render_pixels(a,pal);im.save(folder/(name+'_hud.png'));ys,xs=inner_slice(bb);crop=render_pixels(a[ys,xs],pal);hudimgs.append((project+'/'+name,crop));meta['hud'][name]={'bounds':bb,'palette':list(struct.unpack('<16H',pal)),'parts':aliased_composition(p,1,69)['parts']}
   c=composition(arc);px,sz,bb,_=compose_static(entry(arc,0x10007)[12288:],local_composition(c));pa=render_pixels(np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]),entry(arc,0x11)[320:352]);pa.save(folder/(name+'_portrait.png'));bg=pause_background(arc);bg.alpha_composite(pa,(64+bb[0],192+bb[1]));bg.save(folder/(name+'_pause.png'));portraits.append((project+'/'+name,bg));meta['pause'][name]={'bounds':bb,'parts':c['parts'],'screen_origin':[64+bb[0],192+bb[1]]}
   for n in (89,90,98):
    co=aliased_composition(p,3,n);px,sz,bb,_=composed(g,co);clut=co['parts'][0]['clut'];pp=entry(arc,9)[(11+clut)*32:(12+clut)*32];render_pixels(px,pp).resize((sz[0]*8,sz[1]*8),Image.Resampling.NEAREST).save(folder/(name+f'_life_{n}.png'));meta['life'][name+f'_{n}']={'bounds':bb,'parts':co['parts'],'palette':list(struct.unpack('<16H',pp))}
  exe=raw['SLUS_005.61'];meta['loading_rectangles']=[list(struct.unpack_from('<hhBBBB',exe,0xded04+8+i*8)) for i in (0,1)];allmeta[project]=meta
 for label,items,cell,cols in [('hud',hudimgs,(220,170),3),('pause',portraits,(340,270),3)]:
  board=Image.new('RGB',(cell[0]*cols,cell[1]*((len(items)+cols-1)//cols)),'#536273');draw=ImageDraw.Draw(board)
  for i,(name,im)in enumerate(items):
   x,y=i%cols*cell[0],i//cols*cell[1];draw.text((x+4,y+4),name,fill='white');im=im.resize((im.width*(8 if label=='hud' else 1),im.height*(8 if label=='hud' else 1)),Image.Resampling.NEAREST);board.paste(im,(x+5,y+24),im)
  board.save(out/(label+'_comparison.png'))
 (out/'inventory.json').write_text(json.dumps(allmeta,indent=2)+'\n','utf8');print(str(out))
if __name__=='__main__':main()
