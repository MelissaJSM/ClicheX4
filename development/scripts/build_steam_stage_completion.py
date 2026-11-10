"""Merge PS1 personal stage colors and GangZi capsules into installed Steam arcs."""
import hashlib,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.discover_inputs import DiscReader
from scripts.prepare_riko_ui import entry
from scripts.inspect_steam_portraits import frames
from src.steam_arc import SteamArc
from src.steam_player import unpack_indices
from src.steam_ui import pat_frames
from src.steam_portraits import encode_banks
W=ROOT/'work/steam_port_20261109';D=W/'completion_audit';OUT=ROOT/'out/steam_stage_completion_20261109_v1'
STEAM=Path('C:/Program Files (x86)/Steam/steamapps/common/Mega Man X Legacy Collection')
CAPSULES={'st01_00':6,'st04_01':9,'st06_00':6,'st07_01':9}
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Output collision: '+str(p))
 p.write_bytes(b)
def main():
 D.mkdir(exist_ok=True)
 if (W/'stage_completion_builds.json').exists():raise ValueError('Frozen stage completion manifest exists; preserve it and use a new version for further work')
 backup=json.loads((W/'backup_manifest.json').read_text('utf8'));baseline={r['relative_path']:r['sha256'] for r in backup['originals']}
 state=json.loads((W/'install_state.json').read_text('utf8'));installed={r['relative_path']:r['installed_sha256'] for r in state['files']}
 op=ROOT/'MegaMan X4.bin'
 with op.open('rb') as f:
  if hashlib.file_digest(f,'sha256').hexdigest()!='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b':raise ValueError('Original PS1 hash')
  f.seek(0);reader=DiscReader(f,op.stat().st_size);names=[r['name'].split(';')[0] for r in reader.inspect()['files'] if not r['directory'] and r['name'].startswith(('COL','ST')) and '.ARC' in r['name']]
 original,_=read_disc(op,names);reports=[];audits=[];shared=set()
 native_dir=W/'original/nativeDX10/X4/romPC'
 for mode,suffix in [('ver_rin_nana',''),('ver_buki_riko','_eng')]:
  ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));game=(ROOT/ptr['cue']).with_suffix('.bin')
  with game.open('rb') as f:
   if hashlib.file_digest(f,'sha256').hexdigest()!=ptr['sha256']:raise ValueError('Current PS1 hash')
  ps,_=read_disc(game,names)
  for jp in sorted(native_dir.glob('st*.arc')):
   if jp.stem.endswith(('_eng','_regwor')):continue
   # This pass covers gameplay stages; title, HQ and get screens have other tables.
   if jp.stem.startswith(('st0d','st0e','st0f','std_')):continue
   eng=jp.with_name(jp.stem+'_eng.arc');is_shared=not eng.exists();native=jp if not suffix or is_shared else eng
   target='cliche_br_'+jp.name if suffix and is_shared else native.name
   rel='nativeDX10/X4/romPC/'+target;original_rel='nativeDX10/X4/romPC/'+native.name
   o=SteamArc(native.read_bytes(),baseline[original_rel]);source=STEAM/rel
   raw=source.read_bytes() if source.exists() else o.raw
   if sha(raw)!=installed.get(rel,baseline.get(rel,sha(o.raw))):raise ValueError('Installed parent mismatch: '+rel)
   current=SteamArc(raw);updates={};checks=[]
   for e in o.entries:
    if e.payload[:4]!=b'COL\0' or '\\stage\\col\\' not in e.name:continue
    stem=e.name.split('\\')[-1].upper().replace('_TOPCHRNO','').removesuffix('_ENG')
    name=stem+'.ARC'
    if name not in original:raise ValueError('Stage color name not mapped: '+name)
    old,new=entry(original[name],5),entry(ps[name],5)
    if len(old)!=len(new) or len(e.payload)!=12+len(old):raise ValueError('Color size')
    now=current.by_key[e.key].payload;value=bytearray(now);rows=[]
    allowed={11,13,14,15}
    if jp.stem in CAPSULES:allowed.add(51 if jp.stem in ('st01_00','st06_00') else 63)
    for row in sorted(allowed):
     lo=row*32;hi=lo+32
     if old[lo:hi]==new[lo:hi]:continue
     if e.payload[12+lo:12+hi]!=old[lo:hi]:raise ValueError('Native original color mismatch')
     if now[12+lo:12+hi] not in (old[lo:hi],new[lo:hi]):raise ValueError('Conflicting installed color')
     missing=now[12+lo:12+hi]!=new[lo:hi];rows.append({'row':row,'was_missing':missing})
     value[12+lo:12+hi]=new[lo:hi]
    if rows:updates[e.key]=bytes(value);checks.append({'kind':'stage_colors','source':name,'entry':e.name,'rows':rows})
   if jp.stem in CAPSULES:
    name=jp.stem.upper()+'.ARC';b=CAPSULES[jp.stem];old,new=original[name],ps[name]
    if entry(old,12)!=entry(new,12):raise ValueError('Capsule atlas table moved')
    offsets=struct.unpack('<'+'I'*(len(entry(old,12))//4),entry(old,12));lo=offsets[b];hi=min([v for v in offsets if v>lo],default=len(entry(old,0x10102)))
    opx=unpack_indices(entry(old,0x10102)[lo:hi]);npx=unpack_indices(entry(new,0x10102)[lo:hi])
    tex=next(e for e in o.entries if e.payload[:4]==b'TEX\0' and '\\chr\\stage\\' in e.name and e.name.endswith(f'_{b:03}'))
    if tex.payload[20:20+len(opx)]!=opx:raise ValueError('Capsule texture correspondence')
    now=current.by_key[tex.key].payload
    if now[20:20+len(opx)] not in (opx,npx):raise ValueError('Capsule texture conflict')
    updates[tex.key]=now[:20]+npx+now[20+len(npx):]
    pat=next(e for e in o.entries if e.payload[:4]==b'PAT\0');of=frames(entry(old,10));nf=frames(entry(new,10));native_frames=pat_frames(pat.payload)
    if native_frames!=of:raise ValueError('Capsule PAT regional correspondence')
    banks=pat_frames(current.by_key[pat.key].payload)
    if banks[b] not in (of[b],nf[b]):raise ValueError('Capsule frame conflict')
    banks[b]=nf[b];updates[pat.key]=encode_banks(banks)
    checks.append({'kind':'gangzi_capsule','bank':b,'source':name,'frames':len(nf[b]),'changed_frames':[i for i,(a,c) in enumerate(zip(of[b],nf[b])) if a!=c],'source_pixels_sha256':sha(npx)})
   updates={k:v for k,v in updates.items() if current.by_key[k].payload!=v}
   audits.append({'mode':mode,'target_arc':target,'checks':checks,'missing_entries':len(updates)})
   if not updates:continue
   out=current.rebuild(updates);back=SteamArc(out);back.validate_stream_order()
   if list(back.by_key)!=list(current.by_key):raise ValueError('Entry order changed')
   for e in current.entries:
    if back.by_key[e.key].payload!=updates.get(e.key,e.payload):raise ValueError('Cumulative asset preservation')
   dest=OUT/'nativeDX10/X4/romPC'/target;save(dest,out)
   reports.append({'mode':mode,'target_arc':target,'original_target_arc':native.name,'output':dest.relative_to(ROOT).as_posix(),'output_sha256':sha(out),'parent_sha256':sha(raw),'source_bin_sha256':ptr['sha256'],'original_sha256':sha(o.raw),'checks':checks,'changed_entries':[{'name':current.by_key[k].name,'magic':current.by_key[k].payload[:4].decode('ascii'),'before_sha256':sha(current.by_key[k].payload),'after_sha256':sha(v)}for k,v in updates.items()],'install_eligible':True,'runtime_verified':False,'new_private_file':source.exists() is False})
   if suffix and is_shared:shared.add(jp.stem)
 write(W/'stage_completion_builds.json',reports);write(D/'stage_colors_capsules.json',{'builds':len(reports),'shared_english_resources':sorted(shared),'audit':audits})
 print({'archives':len(reports),'shared_english_resources':sorted(shared),'color_rows':sum(len(c.get('rows',[]))for a in audits for c in a['checks']),'capsules':sum(c['kind']=='gangzi_capsule' for a in audits for c in a['checks'])})
if __name__=='__main__':main()
