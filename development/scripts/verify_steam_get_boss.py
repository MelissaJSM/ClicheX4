"""Decode installed-format get/boss assets independently and compare PS1 art."""
import json,struct,sys,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.inspect_steam_portraits import frames
from scripts.inventory_shibuki_ui import background
from scripts.build_steam_selection import render_frame
from src.steam_arc import SteamArc
from src.steam_player import unpack_indices
from src.steam_ui import pat_frames
W=ROOT/'work/steam_port_20261109';D=W/'get_boss_completion'
def sha(b):return hashlib.sha256(b).hexdigest()
def render_background(a,screen):
 tex=next(e.payload for e in a.entries if e.payload[:4]==b'TEX\0' and '\\dds\\' in e.name);pixels=np.frombuffer(tex[20:],np.uint8).reshape(2048,2048)
 mp=next(e.payload for e in a.entries if e.payload[:4]==b'OMP\0');cells=next(e.payload for e in a.entries if e.payload[:4]==b'OCL\0');pal=next(e.payload[12:]for e in a.entries if e.payload[:4]==b'COL\0' and '\\stage\\col\\' in e.name)
 out=np.zeros((256,256,4),np.uint8)
 for j,v in enumerate(struct.unpack_from('<256H',mp,12+screen*512)):
  if not v:continue
  attr=struct.unpack_from('<I',cells,12+(v&16383)*4)[0];tile=attr>>16&4095;page,local=divmod(tile,256);x=(page%8)*256+(local%16)*16;y=(page//8)*256+(local//16)*16
  pix=pixels[y:y+16,x:x+16]
  if v&16384:pix=pix[:,::-1]
  if v&32768:pix=pix[::-1]
  words=struct.unpack_from('<16H',pal,((attr>>8&63)+64)*32);colors=np.array([[(c>>s&31)*255//31 for s in [0,5,10]]+[255 if i else 0] for i,c in enumerate(words)],np.uint8)
  rgba=colors[pix];rgba[rgba[:,:,3]==0]=0;out[(j//16)*16:(j//16+1)*16,(j%16)*16:(j%16+1)*16]=rgba
 return Image.fromarray(out)
def main():
 builds=json.loads((W/'get_boss_builds.json').read_text('utf8'));results=[];screens=quads=unchanged=0
 for mode in ['ver_rin_nana','ver_buki_riko']:
  rows=[r for r in builds if r['mode']==mode];ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));names=sorted({v for r in rows for v in [r['source_stage'],r['source_palette']]});ps,_=read_disc((ROOT/ptr['cue']).with_suffix('.bin'),names)
  get_board=Image.new('RGBA',(1280,600),'#202938');gd=ImageDraw.Draw(get_board);gd.text((8,6),mode+' / decoded Steam assets / NOT gameplay capture',fill='white')
  boss_board=Image.new('RGBA',(1280,680),'#202938');bd=ImageDraw.Draw(boss_board)
  bd.text((8,646),'Decoded background colors / description shown in INDEX GRAYSCALE (not runtime colors)',fill='white')
  for r in rows:
   a=SteamArc((ROOT/r['output']).read_bytes(),r['output_sha256']);a.validate_stream_order();s=ps[r['source_stage']];pal=entry(ps[r['source_palette']],5)
   mp=next(e.payload for e in a.entries if e.payload[:4]==b'OMP\0');cells=next(e.payload for e in a.entries if e.payload[:4]==b'OCL\0')
   assert mp[12:]==entry(s,0) and cells[12:]==entry(s,1)
   assert struct.unpack_from('<I',mp,8)[0]*2==len(mp)-12 and struct.unpack_from('<I',cells,8)[0]*4==len(cells)-12
   assert all((v&16383)<(len(cells)-12)//4 for v in struct.unpack('<'+'H'*((len(mp)-12)//2),mp[12:]))
   native_pal=next(e.payload[12:]for e in a.entries if e.payload[:4]==b'COL\0' and '\\stage\\col\\' in e.name);assert native_pal==pal
   # Independently rebuild every background screen, including zero cells,
   # mirrored tiles, per-cell palette selection and transparent pixels.
   rendered=[]
   for screen in range(len(entry(s,0))//512):
    actual=render_background(a,screen);expected=np.array(background(s,pal,screen));expected[expected[:,:,3]==0]=0
    assert np.array_equal(np.array(actual),expected),(r['target_arc'],screen);rendered.append(actual);screens+=1
   pat=pat_frames(next(e.payload for e in a.entries if e.payload[:4]==b'PAT\0'));source_frames=frames(entry(s,10));g=entry(s,0x10102)
   if r['category']=='get':
    tex=next(e.payload for e in a.entries if e.payload[:4]==b'TEX\0' and '\\chr\\'in e.name);assert tex[20:]==unpack_indices(g);assert pat[0]==source_frames[0][:len(pat[0])];quads+=sum(len(f)//4 for f in pat[0])
    idx=0 if '_0x' in r['target_arc'] else 1;x=idx*640
    get_board.alpha_composite(rendered[0],(x,30));get_board.alpha_composite(rendered[1],(x+256,30))
    if idx==0:get_board.alpha_composite(rendered[5],(x+64,40))
    else:get_board.alpha_composite(rendered[3],(x,40));get_board.alpha_composite(rendered[4],(x+256,40))
    # Separate art/label preview avoids pretending the native motion positions were tested.
    for k,f in enumerate([idx,4,13,18]):
     im=render_frame(tex,pat[0][f],pal,1 if f>=2 else 0);get_board.alpha_composite(im,(x+12,310+k*60))
   else:
    assert pat==source_frames;split=struct.unpack_from('<I',entry(s,12),4)[0];tex=next(e.payload for e in a.entries if e.payload[:4]==b'TEX\0' and '\\chr\\'in e.name and e.name.endswith('_001'));assert tex[20:20+(len(g)-split)*2]==unpack_indices(g[split:]);quads+=sum(len(f)//4 for f in pat[1])
    i=int(r['target_arc'].split('_')[2].split('.')[0]);top=(16+(i-1)*2,17+(i-1)*2);lower=[(32,33),(34,35),(36,37),(38,39),(40,41),(42,11),(12,13),(14,15)][i-1]
    picture=Image.new('RGBA',(320,240))
    for pair in [top,lower]:picture.alpha_composite(rendered[pair[0]]);picture.alpha_composite(rendered[pair[1]],(256,0))
    x=(i-1)%4*320;y=(i-1)//4*320;boss_board.alpha_composite(picture,(x,y))
    # This review shows description indices, without guessing the native palette base.
    grey=struct.pack('<16H',*[round(i*31/15)*0x421 for i in range(16)])*4
    desc=render_frame(tex,pat[1][0],grey,0);boss_board.alpha_composite(desc,(x+40,y+240))
   # Immutable pre-install parent: current install is still the accepted build.
   p=D/'preserved_before/archives'/r['target_arc']
   if not p.exists():p=Path('C:/Program Files (x86)/Steam/steamapps/common/Mega Man X Legacy Collection/nativeDX10/X4/romPC')/r['target_arc']
   before=p.read_bytes();assert sha(before)==r['parent_sha256'];parent=SteamArc(before);changed={(e['name'],e['magic'])for e in r['changed_entries']}
   for e in parent.entries:
    if (e.name,e.payload[:4].decode('ascii','replace'))not in changed:assert a.by_key[e.key].payload==e.payload;unchanged+=1
   results.append({'target_arc':r['target_arc'],'backgrounds':len(rendered),'passed':True})
  get_board.convert('RGB').save(D/(mode+'_get.png'));boss_board.convert('RGB').save(D/(mode+'_boss.png'))
 report={'passed':True,'archives':len(results),'background_screens_rgba_equal':screens,'label_quads_verified':quads,'unrelated_entries_preserved':unchanged,'actual_runtime_scenes':False,'files':results};(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print({k:v for k,v in report.items() if k!='files'})
if __name__=='__main__':main()
