"""Port current PS1 weapon-get art/labels and eight Korean boss introductions."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.inspect_steam_portraits import frames
from src.steam_arc import SteamArc,pat_from_ps1
from src.steam_player import unpack_indices
from src.steam_portraits import encode_banks
from src.steam_ui import stage_texture,pat_frames
W=ROOT/'work/steam_port_20261109';D=W/'get_boss_completion';OUT=ROOT/'out/steam_get_boss_20261109_v1'
STEAM=Path('C:/Program Files (x86)/Steam/steamapps/common/Mega Man X Legacy Collection')
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Output collision')
 p.write_bytes(b)
def find(a,magic,folder=''):
 candidates=[e for e in a.entries if e.payload[:4]==magic and folder in e.name]
 if len(candidates)!=1:raise ValueError(('Ambiguous resource',magic,folder))
 return candidates[0]
def replace_map(native,old,new,unit):
 if native[4:8]!=struct.pack('<I',1) or native[12:]!=old or len(new)%unit:raise ValueError('Native map correspondence')
 if struct.unpack_from('<I',native,8)[0]!=len(old)//unit:raise ValueError('Native map count')
 return native[:8]+struct.pack('<I',len(new)//unit)+new
def background_texture(template,old,new):
 # Native uses a fixed 2048-square texture; untouched pages beyond the new
 # PS1 atlas remain as before and the new OCL only references the new prefix.
 if len(new)>len(old):raise ValueError('Unexpected background expansion')
 return stage_texture(template,old,new+old[len(new):])
def main():
 D.mkdir(exist_ok=True)
 if (W/'get_boss_builds.json').exists():raise ValueError('Frozen build already exists')
 baseline={r['relative_path']:r['sha256']for r in json.loads((W/'backup_manifest.json').read_text('utf8'))['originals']}
 installed={r['relative_path']:r['installed_sha256']for r in json.loads((W/'install_state.json').read_text('utf8'))['files']}
 us_names=['ST0F_UX.ARC','ST0F_UZ.ARC','COL0F_U0.ARC']+[v for i in range(1,9)for v in (f'STD_1_{i}U.ARC',f'COLD_1U{i}.ARC')]
 jp_names=['ST0F_0X.ARC','ST0F_0Z.ARC','COL0F_00.ARC']+[v for i in range(1,9)for v in (f'STD_1_{i}.ARC',f'COLD_1_{i}.ARC')]
 uspath=ROOT/'MegaMan X4.bin';jppath=ROOT/'Rockman X4.bin'
 if digest(uspath)!='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b':raise ValueError('US reference hash')
 jp_hash=digest(jppath)
 if jp_hash!='a8fcc59d1d934c8601389bccc26f7a110b74f8fc025f1c73ebe63a46c547c9a1':raise ValueError('JP reference hash')
 us,_=read_disc(uspath,us_names);jp,_=read_disc(jppath,jp_names)
 reports=[]
 for mode,suffix,original in [('ver_rin_nana','',jp),('ver_buki_riko','_eng',us)]:
  ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));source=(ROOT/ptr['cue']).with_suffix('.bin')
  if digest(source)!=ptr['sha256']:raise ValueError('Current PS1 mismatch')
  src,_=read_disc(source,us_names)
  jobs=[(f'st0f_0{c}{suffix}.arc',f'ST0F_U{c.upper()}.ARC',f'ST0F_{"U" if suffix else "0"}{c.upper()}.ARC','COL0F_U0.ARC','COL0F_U0.ARC' if suffix else 'COL0F_00.ARC','get')for c in ['x','z']]
  jobs += [(f'std_1_{i}{suffix}.arc',f'STD_1_{i}U.ARC',f'STD_1_{i}{"U" if suffix else ""}.ARC',f'COLD_1U{i}.ARC',f'COLD_1U{i}.ARC' if suffix else f'COLD_1_{i}.ARC','boss')for i in range(1,9)]
  for target,psname,oldname,palname,oldpalname,kind in jobs:
   rel='nativeDX10/X4/romPC/'+target;native=SteamArc((W/'original'/rel).read_bytes(),baseline[rel]);parent=SteamArc((STEAM/rel).read_bytes(),installed.get(rel,baseline[rel]));old=original[oldname];new=src[psname];updates={}
   bg=find(native,b'TEX\0','\\dds\\');updates[bg.key]=background_texture(bg.payload,entry(old,0x10000),entry(new,0x10000))
   for k,magic,unit in [(0,b'OMP\0',2),(1,b'OCL\0',4)]:
    e=find(native,magic);updates[e.key]=replace_map(e.payload,entry(old,k),entry(new,k),unit)
   col=find(native,b'COL\0','\\stage\\col\\')
   if col.payload[12:]!=entry(original[oldpalname],5):raise ValueError('Original palette differs')
   updates[col.key]=col.payload[:12]+entry(src[palname],5)
   pat=find(native,b'PAT\0');native_frames=pat_frames(pat.payload);old_frames=frames(entry(old,10));new_frames=frames(entry(new,10))
   if native_frames!=old_frames:raise ValueError('Original stage PAT differs')
   if kind=='get':
    tex=find(native,b'TEX\0','\\chr\\');oldpx=unpack_indices(entry(old,0x10102));newpx=unpack_indices(entry(new,0x10102))
    if len(tex.payload)-20!=len(newpx):raise ValueError('Get atlas capacity')
    if suffix:
     if tex.payload[20:20+len(oldpx)]!=oldpx:raise ValueError('EN get atlas correspondence')
    else:
     # Steam JP's second page has its own kanji glyph pixels. Its first
     # English page and all 21 PAT records match PS1 JP. All labels are
     # replaced here, so no native kanji tiles are retained accidentally.
     if len(oldpx)!=106496 or tex.payload[20:65556]!=oldpx[:65536]:raise ValueError('JP shared get atlas page differs')
    if len(native_frames)!=1 or len(native_frames[0])!=(22 if suffix else 21):raise ValueError('Get regional frame count')
    updates[tex.key]=tex.payload[:20]+newpx
    updates[pat.key]=encode_banks([new_frames[0][:len(native_frames[0])]])
   else:
    if native_frames!=new_frames or entry(old,12)!=entry(new,12):raise ValueError('Boss animation/layout changed')
    split=struct.unpack_from('<I',entry(old,12),4)[0];oldg=entry(old,0x10102);newg=entry(new,0x10102)
    if oldg[:split]!=newg[:split]:raise ValueError('Boss actor changed')
    tex=next(e for e in native.entries if e.payload[:4]==b'TEX\0' and '\\chr\\' in e.name and e.name.endswith('_001'))
    oldpx,newpx=unpack_indices(oldg[split:]),unpack_indices(newg[split:])
    if tex.payload[20:20+len(oldpx)]!=oldpx or len(oldpx)!=len(newpx):raise ValueError('Description correspondence')
    updates[tex.key]=tex.payload[:20]+newpx+tex.payload[20+len(newpx):]
   for key in updates:
    if parent.by_key[key].payload!=native.by_key[key].payload:raise ValueError('Existing graphics need explicit merge: '+target)
   output=parent.rebuild(updates);back=SteamArc(output);back.validate_stream_order()
   for e in parent.entries:
    if back.by_key[e.key].payload!=updates.get(e.key,e.payload):raise ValueError('Unrelated entry changed')
   dest=OUT/rel;save(dest,output)
   reports.append({'mode':mode,'target_arc':target,'output':dest.relative_to(ROOT).as_posix(),'output_sha256':sha(output),'parent_sha256':sha(parent.raw),'original_sha256':sha(native.raw),'source_bin_sha256':ptr['sha256'],'original_jp_bin_sha256':jp_hash if not suffix else None,'source_stage':psname,'source_palette':palname,'category':kind,'frame_count':len(pat_frames(back.by_key[pat.key].payload)[0]),'jp_get_kanji_page_replaced':kind=='get' and not suffix,'changed_entries':[{'name':parent.by_key[k].name,'magic':parent.by_key[k].payload[:4].decode('ascii'),'sha256':sha(v)}for k,v in updates.items() if v!=parent.by_key[k].payload],'boss_actor_animation_preserved':kind=='boss','install_eligible':True,'runtime_verified':False})
 write(W/'get_boss_builds.json',reports)
 print({'archives':len(reports),'get_screens':sum(r['category']=='get'for r in reports),'boss_screens':sum(r['category']=='boss'for r in reports),'jp_original_sha256':jp_hash})
if __name__=='__main__':main()
