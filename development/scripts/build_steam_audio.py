"""Port accepted gameplay audio without changing graphics or game save data."""
import hashlib,json,re,struct,subprocess,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.steam_arc import SteamArc
from src.steam_audio import mute_wave,wave_info,bank_records,sequence_events
W=ROOT/'work/steam_port_20261109';O=W/'original';D=W/'audio'
OUT=ROOT/'out/steam_audio_20261109_v2'
FF=ROOT/'work/tools/voice_env/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Output collision: '+str(p))
 p.write_bytes(b)

def main():
 baseline={r['relative_path']:r['sha256'] for r in json.loads((W/'backup_manifest.json').read_text('utf8'))['originals']}
 def original(rel):
  b=(O/rel).read_bytes()
  if sha(b)!=baseline[rel]:raise ValueError('Original backup mismatch')
  return b
 parentfile=W/'audio/parents_pause_v3.json'
 if not parentfile.exists():write(parentfile,(W/'pause_builds.json').read_bytes())
 parents=json.loads(parentfile.read_text('utf8'))
 sources=json.loads((D/'player_sources.json').read_text('utf8'))
 effects={r['effect']:(ROOT/r['output']).read_bytes() for r in sources}
 assert all(sha(effects[r['effect']])==r['sha256'] for r in sources)
 stem='nativeDX10/X4/sound/se/'
 replacements={};audit=[]
 for player in (0,1):
  bank='vo_pl0'+str(player)
  for language in ('','_eng'):
   suffix=language.upper()
   bp=stem+bank+'/'+bank+language+'.sbkr';br=original(bp);revised=bytearray(br);records=bank_records(br)
   if len(records)!=13:raise ValueError('Player voice bank count differs')
   seq=original(stem+bank+'/'+bank+language+'.srqr');events=sequence_events(seq)
   if [(r[0],r[1]) for r in events]!=[(i,i) for i in range(13)]+[(112,12)]:raise ValueError('Player event mapping differs')
   death_id=12 if player else 11
   donorbank=original(stem+'se_pl01/se_pl01.sbkr');donor=bank_records(donorbank)[11]
   rakuhouha=original('nativeDX10/'+donor[0].replace('\\','/')+'.xsew')
   for wid in range(13 if player else 12):
    rel=stem+bank+'/wav/'+bank.upper()+f'_PG00_ID{wid:02}'+suffix+'.xsew'
    raw=original(rel)
    if wid in (0,1):new=effects['hurt'];label='hurt'
    elif wid==death_id:new=effects['death'];label='death'
    elif player and wid==10:new=rakuhouha;label='rakuhouha'
    else:new=mute_wave(raw);label='mute'
    replacements[rel]=new
    # Independent decode, including exact silence and preserved muted duration.
    path=D/'decode_v2'/Path(rel).name;write(path,new)
    pcm=subprocess.run([str(FF),'-v','error','-i',str(path),'-f','s16le','pipe:1'],capture_output=True,check=True).stdout
    pcm=np.frombuffer(pcm,dtype='<i2');info=wave_info(new)
    if label=='mute':
     if np.any(pcm) or wave_info(raw)!=info:raise ValueError('Muted sound changed duration or is not silent')
    elif not np.any(pcm):raise ValueError('Effect became silent')
    audit.append({'path':rel,'role':label,'before_sha256':sha(raw),'after_sha256':sha(new),'frames':len(pcm),'rate':info['rate'],'peak':int(np.max(np.abs(pcm.astype(int))))})
   for i,(name,at,record) in enumerate(records):
    if i in (0,1,12):revised[at+9]=127
    elif player and i==10:
     # Reuse the original nonvoice effect's pitch/envelope, but keep the voice
     # event's sound identifier and resource filename.
     revised[at:at+76]=donor[2][:76];revised[at+9]=103
   replacements[bp]=bytes(revised)
 # Accepted modest saber/slash impact reinforcement, on shared original effects.
 rel=stem+'se_pl01/se_pl01.sbkr';raw=original(rel);new=bytearray(raw)
 for i,(name,at,record) in enumerate(bank_records(raw)):
  if i in (7,8):new[at+9]=round(record[9]*120/105)
  if i in (9,10):new[at+9]=round(record[9]*114/100)
 replacements[rel]=bytes(new)
 reports=[];pause=[]
 def emit(rel,data,parent=None,**extra):
  path=OUT/rel;write(path,data)
  row={'relative_path':rel,'output':path.relative_to(ROOT).as_posix(),'output_sha256':sha(data),'install_eligible':True,'actual_listening_verified':False,**extra}
  if parent:row.update(parent=parent['output'],parent_sha256=parent['output_sha256'])
  reports.append(row);return row
 for parent in parents:
  arc=SteamArc((ROOT/parent['output']).read_bytes(),parent['output_sha256']);updates={}
  for e in arc.entries:
   ext={b'RIFF':'.xsew',b'SBKR':'.sbkr',b'SRQR':'.srqr'}.get(e.payload[:4])
   if ext:
    rel='nativeDX10/'+e.name.replace('\\','/')+ext
    if rel in replacements:
     if e.payload!=original(rel):raise ValueError('Unexpected already modified audio entry')
     updates[e.key]=replacements[rel]
  result=arc.rebuild(updates);back=SteamArc(result);back.validate_stream_order()
  if any(e.payload!=back.by_key[e.key].payload for e in arc.entries if e.key not in updates):raise ValueError('Unrelated asset changed')
  rel='nativeDX10/X4/romPC/'+parent['target_arc']
  row=emit(rel,result,parent,mode=parent['mode'],target_arc=parent['target_arc'],changed_entries=[list(k) for k in updates],non_audio_resources_preserved=True)
  pause.append({**parent,**row})
 # Eight-boss EN combat resources are native JP recordings/event maps. Boss4
 # already shares the JP ARC. Their nonaudio pixels/COF are byte-identical.
 for i in (1,2,3,5,6,7,8):
  for prefix in (f'st{i}_1_1',f'onpare_{i}'):
   rel='nativeDX10/X4/romPC/'+prefix+'_eng.arc'
   en=SteamArc(original(rel));jp=SteamArc(original(rel.replace('_eng','')))
   for e in en.entries:
    if '\\sound\\' not in e.name and e.payload[:4]!=b'RLST':
     if jp.by_key[e.key].payload!=e.payload:raise ValueError('Boss nonaudio differs')
   data=bytearray(jp.raw)
   for e in jp.entries:
    if e.payload[:4]==b'RLST':
     name=e.name+'_eng';data[8+80*e.index:8+80*e.index+64]=name.encode().ljust(64,b'\0')
   back=SteamArc(data);back.validate_stream_order()
   emit(rel,bytes(data),boss=i,native_jp_audio=True,nonaudio_payloads_preserved=True)
 # Mirror loose wave/bank assets so cache/fallback lookup cannot find old voices.
 for rel,data in replacements.items():emit(rel,data)
 # Native boss intro table has 23 unique clips for the first 8 bosses. Preserve
 # all later English NPC/boss dialogue; no movie or BGM assets are touched.
 exe=original('RXC1.exe');tracks=list(exe[0x1ada510-0x401200:0x1ada510-0x401200+39]);ids=sorted(set(tracks[:24]))
 if len(ids)!=23 or set(ids)&set(tracks[24:]) or any(not 40<=i<80 for i in ids):raise ValueError('Intro voice table differs')
 for track in ids:
  group=(track-40)//8+1;clip=(track-40)%8+1
  source=f'nativeDX10/X4/sound/voice/wav/VOICE{group}/VOICE{group}_{clip:04}.sngw'
  target=f'nativeDX10/X4/sound/voice/wav/VOICE{group}/eng/VOICE{group}_{clip:04}_eng.sngw'
  emit(target,original(source),original_audio_source=source,source_original_sha256=baseline[source],boss_intro_track=track)
 # Stream banks carry byte and decoded sample counts. Keep each English path
 # pointer and event table, but update all eight metadata fields for copied clips.
 for group in range(1,6):
  rel=f'nativeDX10/X4/sound/voice/x4_voice{group:02}_eng.stqr'
  en=original(rel);jp=original(rel.replace('_eng',''));new=bytearray(en)
  for raw in (en,jp):
   if raw[:8]!=b'STQR\x08\0\0\0' or struct.unpack_from('<3I',raw,8)!=(8,16,1) or struct.unpack_from('<2I',raw,32)!=(56,344):raise ValueError('Stream bank layout differs')
  for clip in range(1,9):
   if 40+(group-1)*8+clip-1 not in ids:continue
   at=56+(clip-1)*36
   if struct.unpack_from('<II',jp,at+12)!=(2,48000):raise ValueError('Stream audio format differs')
   new[at+4:at+36]=jp[at+4:at+36]
  emit(rel,bytes(new),stream_event_tables_and_other_clips_preserved=True)
 write(W/'audio_builds.json',(json.dumps(reports,indent=2)+'\n').encode())
 write(W/'audio_pause_builds.json',(json.dumps(pause,indent=2)+'\n').encode())
 write(D/'build_verification.json',(json.dumps({'passed':True,'wave_checks':audit,'source_effects':sources,'boss_intro_tracks':ids,'arc_count':len(pause)+14,'loose_file_count':len(replacements)+28,'no_ps1_files_changed':True,'gameplay_listening_verified':False},indent=2)+'\n').encode())
 print(json.dumps({'files':len(reports),'archives':len(pause)+14,'wave_checks':len(audit),'intro_clips':len(ids)}))
if __name__=='__main__':main()
