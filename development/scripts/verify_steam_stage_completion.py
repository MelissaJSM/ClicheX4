"""Independently read the cumulative stage output and check PS1 colors/capsules."""
import json,struct,sys,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.inspect_steam_portraits import frames
from scripts.build_steam_selection import render_frame
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames
from src.steam_player import unpack_indices
W=ROOT/'work/steam_port_20261109';D=W/'completion_audit'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 builds=json.loads((W/'stage_completion_builds.json').read_text('utf8'));results=[];color_rows=0;capsule_frames=0;unchanged=0
 board=Image.new('RGB',(1440,640),'#18202e');draw=ImageDraw.Draw(board);draw.text((12,8),'Steam decoded GangZi capsules / NOT gameplay capture',fill='white');images=0
 for mode in ['ver_rin_nana','ver_buki_riko']:
  subset=[r for r in builds if r['mode']==mode];names=sorted({c['source']for r in subset for c in r['checks']})
  ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));ps,_=read_disc((ROOT/ptr['cue']).with_suffix('.bin'),names)
  for r in subset:
   a=SteamArc((ROOT/r['output']).read_bytes(),r['output_sha256']);a.validate_stream_order()
   for c in r['checks']:
    if c['kind']=='stage_colors':
     e=next(e for e in a.entries if e.name==c['entry']);pal=entry(ps[c['source']],5)
     for row in c['rows']:
      y=row['row'];assert e.payload[12+y*32:12+(y+1)*32]==pal[y*32:(y+1)*32];color_rows+=1
    else:
     s=ps[c['source']];b=c['bank'];fr=frames(entry(s,10))[b];pat=next(e.payload for e in a.entries if e.payload[:4]==b'PAT\0')
     assert pat_frames(pat)[b]==fr
     offsets=struct.unpack('<'+'I'*(len(entry(s,12))//4),entry(s,12));lo=offsets[b];g=entry(s,0x10102);hi=min([v for v in offsets if v>lo],default=len(g));pixels=unpack_indices(g[lo:hi]);tex=next(e.payload for e in a.entries if e.payload[:4]==b'TEX\0' and '\\chr\\stage\\' in e.name and e.name.endswith(f'_{b:03}'))
     assert tex[20:20+len(pixels)]==pixels;capsule_frames+=len(fr)
     pal=next(e.payload[12:]for e in a.entries if e.payload[:4]==b'COL\0' and '\\stage\\col\\' in e.name and '_0X' in e.name.upper() or e.payload[:4]==b'COL\0' and '\\stage\\col\\' in e.name and '_1X' in e.name.upper())
     base=48 if b==6 else 60
     # Actual changed character frames include body, mouth and hologram.
     for k,n in enumerate([6,7,21]):
      im=render_frame(tex,fr[n],pal,base);im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
      x=images%4*360+k*118;y=images//4*290+45;board.paste(im,(x,y),im)
     draw.text((images%4*360+4,images//4*290+26),mode+' '+r['target_arc'][:7],fill='white');images+=1
   parent=Path('C:/Program Files (x86)/Steam/steamapps/common/Mega Man X Legacy Collection/nativeDX10/X4/romPC')/r['target_arc']
   before=parent.read_bytes() if parent.exists() else (W/'original/nativeDX10/X4/romPC'/r['original_target_arc']).read_bytes()
   assert sha(before)==r['parent_sha256'];p=SteamArc(before);changed={(e['name'],e['magic'])for e in r['changed_entries']}
   for e in p.entries:
    if (e.name,e.payload[:4].decode('ascii','replace')) not in changed:assert a.by_key[e.key].payload==e.payload;unchanged+=1
   results.append({'target_arc':r['target_arc'],'source_bin_sha256':ptr['sha256'],'passed':True})
 board.save(D/'gangzi_capsules.png')
 result={'passed':True,'archives':len(results),'color_rows':color_rows,'capsule_frames':capsule_frames,'unchanged_entries':unchanged,'runtime_scenes_verified':False,'files':results}
 (D/'stage_completion_verification.json').write_text(json.dumps(result,indent=2)+'\n','utf8');print({k:v for k,v in result.items() if k!='files'})
if __name__=='__main__':main()
