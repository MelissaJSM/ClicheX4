"""Read-only audit of modified PS1 stage palette rows against installed resources."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_steam_ending import W,D,STEAM,sha
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.steam_arc import SteamArc
from src.steam_region_routes import SHARED
from src.steam_ui import pat_frames
from src.steam_player import unpack_indices
from scripts.inspect_steam_portraits import frames

def main():
 changes=json.loads((W/'completion_audit/ps1_stage_changes.json').read_text('utf8'));installed={r['relative_path']:r['installed_sha256']for r in json.loads((W/'install_state.json').read_text('utf8'))['files']};result={}
 ref,_=read_disc(ROOT/'MegaMan X4.bin',['ST00_00.ARC']);refpx=unpack_indices(entry(ref['ST00_00.ARC'],0x10102)[204800:217088]);refpat=frames(entry(ref['ST00_00.ARC'],10))[11]
 for mode,suffix in [('ver_rin_nana',''),('ver_buki_riko','_eng')]:
  modified={r['file']:r['changes'][0]['rows']for r in changes[mode]if r['file'].startswith('COL') and r['changes'][0]['kind']=='0x5'}
  ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));ps,_=read_disc((ROOT/ptr['cue']).with_suffix('.bin'),list(modified))
  rows=[];seen=set()
  for p in sorted((W/'original/nativeDX10/X4/romPC').glob('st*.arc')):
   stem=p.stem
   if mode=='ver_rin_nana' and stem.endswith('_eng'):continue
   if mode=='ver_buki_riko' and not stem.endswith('_eng') and stem not in SHARED:continue
   target='cliche_br_'+p.name if suffix and stem in SHARED else p.name;rel='nativeDX10/X4/romPC/'+target
   a=SteamArc((STEAM/rel).read_bytes(),installed.get(rel))
   for e in a.entries:
    if e.payload[:4]!=b'COL\0' or '\\stage\\col\\'not in e.name:continue
    name=e.name.split('\\')[-1].upper().replace('_TOPCHRNO','').removesuffix('_ENG')
    name={'COL0E_00':'COL0E_U0','COL0E_01':'COL0E_U1','COL0F_00':'COL0F_U0','COL0F_01':'COL0F_U1'}.get(name,name)
    m=re.fullmatch(r'COLD_1_([1-8])',name)
    if m:name='COLD_1U'+m[1]
    name+='.ARC'
    if name not in modified:continue
    source=entry(ps[name],5);native=e.payload[12:]
    if len(native)!=len(source):raise ValueError(('Palette size',target,name))
    different=[n for n in modified[name]if native[n*32:(n+1)*32]!=source[n*32:(n+1)*32]]
    explanation=None
    if different==[35] and stem in ('st0d_0x','st0d_0z'):
     matching='COL0D_0X.ARC' if stem.endswith('x') else 'COL0D_0Z.ARC'
     assert native[35*32:36*32]==entry(ps[matching],5)[35*32:36*32]
     explanation='HQ intentionally assigns the displayed character palette to both native COL copies; matches '+matching
    elif different==[50] and stem=='st0b_0z':
     original=SteamArc((W/'original/nativeDX10/X4/romPC'/p.name).read_bytes())
     assert native[50*32:51*32]==original.by_key[e.key].payload[12+50*32:12+51*32]
     assert not any(q.payload[:4]==b'TEX\0' and q.payload[20:20+len(refpx)]==refpx for q in original.entries)
     assert not any(q.payload[:4]==b'PAT\0' and refpat in pat_frames(q.payload) for q in original.entries)
     explanation='Original X-portrait palette remains in the Zero-only stage with no matching X portrait atlas/PAT; runtime use of this unused-looking copy not proven'
    rows.append({'arc':target,'entry':e.name,'ps1_palette':name,'modified_rows':modified[name],'different_rows':different,'difference_context':explanation});seen.add(name)
  result[mode]={'comparisons':rows,'unmapped_ps1_palette_files':sorted(set(modified)-seen),'differences':[{k:v for k,v in r.items()if k!='modified_rows'}for r in rows if r['different_rows']]}
 report={'scope':'modified PS1 stage COL rows only; not a proof of all graphics or runtime behavior','modes':result}
 (D/'stage_palette_coverage.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
 for mode,r in result.items():print(mode,'palettes',len(r['comparisons']),'unmapped',r['unmapped_ps1_palette_files'],'differences',r['differences'])
if __name__=='__main__':main()
