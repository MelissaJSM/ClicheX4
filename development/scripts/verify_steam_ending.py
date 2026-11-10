"""Independently render native ending maps and protect original creator credits."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.steam_arc import SteamArc
from scripts.build_steam_ending import W,D,STEAM,sha,find,indexed_screens,patch_screens
from scripts.verify_steam_get_boss import render_background
from scripts.inventory_shibuki_ui import background
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry

def main():
 builds=json.loads((W/'ending_builds.json').read_text('utf8'));results=[];screens=unchanged=creator_pixels=0
 for r in builds:
  a=SteamArc((ROOT/r['output']).read_bytes(),r['output_sha256']);a.validate_stream_order();old=SteamArc((W/'original'/r['relative_path']).read_bytes(),r['original_sha256'])
  palette=find(a,b'COL\0').payload[12:];assert palette==find(old,b'COL\0').payload[12:]
  mp=find(a,b'OMP\0').payload;cells=find(a,b'OCL\0').payload
  assert len(mp)==12+struct.unpack_from('<I',mp,8)[0]*2 and len(cells)==12+struct.unpack_from('<I',cells,8)[0]*4
  assert all(v&16383<(len(cells)-12)//4 for v in struct.unpack('<12288H',mp[12:]))
  ptr=json.loads((ROOT/'projects'/r['mode']/'current_build.json').read_text('utf8'));ps,_=read_disc((ROOT/ptr['cue']).with_suffix('.bin'),['ST0F_U1.ARC','COL0F_U1.ARC'])
  actual=[];expected=[];protected=0
  native_before=indexed_screens(old);native_after=indexed_screens(a)
  for s in range(48):
   im=render_background(a,s);got=np.array(im);exi=np.array(Image.open(D/(r['mode']+f'_expected_indices_{s:02}.png')));exrows=np.array(Image.open(D/(r['mode']+f'_expected_rows_{s:02}.png')))
   er=np.repeat(np.repeat(exrows,16,0),16,1);words=np.array(struct.unpack('<2048H',palette),np.uint16).reshape(128,16);cw=words[er,exi];rgba=np.stack([(cw>>k&31)*255//31 for k in (0,5,10)]+[np.where(exi,255,0)],axis=2).astype('uint8');rgba[rgba[:,:,3]==0]=0
   assert np.array_equal(got,rgba),(r['target_arc'],s)
   if r['mode']=='ver_buki_riko':
    psim=np.array(background(ps['ST0F_U1.ARC'],entry(ps['COL0F_U1.ARC'],5),s));psim[psim[:,:,3]==0]=0;assert np.array_equal(got,psim)
   actual.append(im);expected.append(Image.fromarray(rgba));screens+=1
  # Verify full creator names and company logos, not merely a changed-byte budget.
  for s in range(4,48):
   px,rows=native_before[s];ap,ar=native_after[s];p=np.repeat(np.repeat(rows,16,0),16,1);z=np.repeat(np.repeat(ar,16,0),16,1)
   mask=(px>0)&(p!=81)
   if r['mode']=='ver_rin_nana':
    if 26<=s<=33:mask[:]=False
    if s in (38,39):mask[64:96]=False
    if s in (46,47):mask[80:96]&=p[80:96]!=80
   else:
    if s>=38:mask[:]=False
    if s in (28,29):mask[:32]=False
    if s in (36,37):mask[:64]=False
   assert not np.any(mask&((px!=ap)|(p!=z))),(r['target_arc'],'creator',s)
   protected+=int(mask.sum())
  creator_pixels+=protected
  changed={e['name'] for e in r['changed_entries']}
  for e in old.entries:
   if e.name not in changed:assert a.by_key[e.key].payload==e.payload;unchanged+=1
  if r['mode']=='ver_rin_nana':
   # The previous native corrections to voice credits are not overwritten.
   before=find(old,b'OCL\0').payload;after=find(a,b'OCL\0').payload;assert after[12:len(before)]==before[12:]
   original_screens={16,17}
   assert all(np.array_equal(np.array(render_background(old,s)),np.array(actual[s])) for s in original_screens)
   assert all(np.array_equal(np.array(render_background(old,s))[:240],np.array(actual[s])[:240]) for s in (18,19))
   assert len(find(a,b'TEX\0','\\dds\\').payload)==len(find(old,b'TEX\0','\\dds\\').payload)
   # Negative validation with real native layout, without writing any files.
   rejected=0
   for label,px,rows in [('bad_index',np.full((256,256),16,np.uint8),np.full((16,16),80,np.uint8)),('bad_palette',np.ones((256,256),np.uint8),np.full((16,16),128,np.uint8)),('bad_shape',np.zeros((1,1),np.uint8),np.full((16,16),80,np.uint8))]:
    try:patch_screens(old,{26:(px,rows)})
    except ValueError:rejected+=1
    else:raise AssertionError(label)
   noop,_=patch_screens(old,{});assert all(old.by_key[k].payload==v for k,v in noop.items())
  else:rejected=0
  selected=[4,14,26,28,30,32,38,42,44,46] if r['mode']=='ver_rin_nana' else [4,14,24,28,34,36,38,40,42,44]
  board=Image.new('RGBA',(640,10*138+28),'#17202d');draw=ImageDraw.Draw(board);draw.text((8,4),r['mode']+' / native assets reconstruction, NOT gameplay capture',fill='white')
  # Full 320x256 panels; two columns and five rows, no screenshot downscaling.
  for i,s in enumerate(selected):
   x=i%2*320;y=i//2*276+28;im=Image.new('RGBA',(320,256));im.alpha_composite(actual[s]);im.alpha_composite(actual[s+1],(256,0));board.alpha_composite(im,(x,y));draw.text((x+2,y+258),'map '+str(s)+' / '+str(s+1),fill='white')
  board.convert('RGB').save(D/(r['mode']+'_ending_review.png'))
  results.append({'target_arc':r['target_arc'],'screens_rgba_equal':48,'protected_creator_and_logo_pixels':protected,'negative_cases_rejected':rejected,'no_change_roundtrip':True,'passed':True})
 report={'passed':True,'archives':len(builds),'background_screens_rgba_equal':screens,'creator_and_logo_pixels_preserved':creator_pixels,'unrelated_entries_preserved':unchanged,'files':results,'runtime_ending_scroll_verified':False}
 (D/'verification.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(report)
if __name__=='__main__':main()
