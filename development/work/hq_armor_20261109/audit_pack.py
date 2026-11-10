"""Compact non-player HQ tiles; compare every preserved assembled frame."""
import sys,struct,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels,write_tile
from src.psx_static_effect import compose_static

def pack(mode):
 d=H/mode;raw=(d/'originals/ST0D_0X.ARC').read_bytes();g=entry(raw,0x10102);p=entry(raw,10)
 bases=struct.unpack('<5I',entry(raw,12));patterns={};refs={};comps={}
 for bank in (0,1,3,4):
  for n in range(aliased_composition(p,bank,0)['bank_frame_count']):
   c=aliased_composition(p,bank,n);comps[bank,n]=c
   for q in c['parts']:
    tile=bases[bank]//128+q['page']*256+q['tile'];pattern=tile_pixels(g,tile)
    patterns.setdefault(pattern,[]).append(q['record_offset']);refs[q['record_offset']]=(pattern,q)
 # Preserve texel-zero sampling guards on both sides of each 176-tile upload page.
 def safe(px,t):return (t%16!=0 or not any(px[::16])) and (t%176>=16 or not any(px[:16]))
 slots=list(range(len(g)//128));assigned={};ng=bytearray(len(g));np=bytearray(p)
 ordered=sorted(patterns,key=lambda px:(-int(any(px[::16]))-int(any(px[:16])),px))
 for pattern in ordered:
  t=next(t for t in slots if safe(pattern,t));slots.remove(t);assigned[pattern]=t;write_tile(ng,t,pattern)
 for pos,(pattern,q)in refs.items():
  t=assigned[pattern];np[pos]=(q['flags']&252)|(t>>8);np[pos+1]=t&255
 count=((max(assigned.values())+16)//16)*16;checks=0
 for (bank,n),c in comps.items():
  a=compose_static(g[bases[bank]:],local_composition(c))[:3]
  b=compose_static(ng,local_composition(aliased_composition(np,bank,n)))[:3]
  assert a==b,(bank,n);checks+=1
 out=d/'packing';out.mkdir(exist_ok=True);(out/'non_x_texture.bin').write_bytes(ng[:count*128]);(out/'parts.bin').write_bytes(np)
 result={'unique_non_x_patterns':len(patterns),'static_tiles':count,'available_dynamic_tiles':944-count,
  'reclaimed_disc_bytes':len(g)-count*128,'payload_capacity':len(g)-count*128+2048-96,
  'non_x_frames_exact':checks,'all_5_texture_bases':list(bases),'new_non_x_base':0,
  'direct_uv_not_yet_audited':True,'runtime_verified':False}
 (out/'report.json').write_text(json.dumps(result,indent=2));print(mode,result)
 return result
if __name__=='__main__':
 for mode in ['ver_rin_nana','ver_buki_riko']:pack(mode)
