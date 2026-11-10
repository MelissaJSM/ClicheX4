"""Port the actual current PS1 title mix, including final effects and reverberation."""
from pathlib import Path
import sys,json,struct,hashlib,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts.discover_inputs import DiscReader
from scripts.build_steam_title_voice import decode,save,sha,FF
from src.steam_stream import TITLE_STREAMS,decode_sngw,encode_sngw,preserve_native_comments,native_title_info,clear_records,vorbis_comments
W=R/'work/steam_port_20261109';D=W/'title_voice/v3';OUT=R/'out/steam_title_voice_20261109_v3'

def main():
 D.mkdir(parents=True,exist_ok=True)
 prepared=json.loads((R/'work/overhaul_20261105/audio/title/prepared/mix.json').read_text('utf8'))
 baseline={r['relative_path']:r['sha256'] for r in json.loads((W/'backup_manifest.json').read_text('utf8'))['originals']}
 sources=[];pcm_by_mode={}
 for mode in ('ver_rin_nana','ver_buki_riko'):
  pointer=json.loads((R/'projects'/mode/'current_build.json').read_text('utf8'))
  path=(R/pointer['cue']).with_suffix('.bin')
  with path.open('rb') as f:actual_hash=hashlib.file_digest(f,'sha256').hexdigest()
  if actual_hash!=pointer['sha256']:raise ValueError('Current PS1 build hash mismatch')
  with path.open('rb') as f:
   reader=DiscReader(f,path.stat().st_size)
   record=next(r for r in reader.inspect()['files'] if r['name'].split(';')[0]=='BGM5_U.XA')
   if record['lba']!=226570:raise ValueError('Unexpected title resource LBA')
   f.seek(record['lba']*2352);raw=f.read(1544*2352)
  if sha(raw)!=prepared['after_sha256']:raise ValueError('Current PS1 title does not match final C07 mix')
  xa=D/(mode+'_current.xa');save(xa,raw)
  s16=subprocess.run([str(FF),'-v','error','-i',str(xa),'-map','0:a:0','-f','s16le','pipe:1'],capture_output=True,check=True).stdout
  data=subprocess.run([str(FF),'-v','error','-i',str(xa),'-map','0:a:0','-ar','48000','-f','f32le','pipe:1'],capture_output=True,check=True).stdout
  pcm=np.frombuffer(data,dtype='<f4').reshape(-1,2).copy()
  if pcm.shape!=(494080,2):raise ValueError('Unexpected current PS1 sample count')
  pcm_by_mode[mode]=pcm
  sources.append({'mode':mode,'bin':path.relative_to(R).as_posix(),'bin_sha256':actual_hash,
   'raw_xa_sha256':sha(raw),'decoded_s16_sha256':sha(s16),'decoded_frames':len(s16)//4,
   'matches_final_c07':True,'resampled_pcm_sha256':sha(data)})
 if not np.array_equal(*pcm_by_mode.values()):raise ValueError('Mode title mixes unexpectedly differ')
 builds=[];reports=[]
 for rel,bankrel in TITLE_STREAMS.items():
  raw=(W/'original'/rel).read_bytes();bank=(W/'original'/bankrel).read_bytes()
  if sha(raw)!=baseline[rel] or sha(bank)!=baseline[bankrel]:raise ValueError('Original backup hash mismatch')
  native_ogg=decode_sngw(raw);native=decode(native_ogg);first=clear_records(bank)[0]
  if first['frames']!=len(native) or first['size']!=len(raw):raise ValueError('Native timing differs')
  region='en' if '/eng/' in rel else 'jp';mode='ver_buki_riko' if region=='en' else 'ver_rin_nana'
  pcm=pcm_by_mode[mode];target=np.zeros_like(native)
  # EN directly reuses the full final PS1 mix. JP has an extra 2.24 s of
  # presentation: preserve only its opening effect, then play that same mix.
  # This discards the entire old Japanese call, not just its final X4 syllables.
  offset=0 if region=='en' else 107520
  take=min(len(pcm),len(target)-offset)
  if np.max(abs(pcm[take:]),initial=0)>1e-5:raise ValueError('Would truncate audible PS1 tail')
  target[offset:offset+take]=pcm[:take]
  fade=0
  if offset:
   target[:offset]=native[:offset]
   fade=3072;weight=np.linspace(0,1,fade)[:,None]
   target[offset:offset+fade]=native[offset:offset+fade]*(1-weight)+pcm[:fade]*weight
  preserved_start=offset+fade
  if not np.array_equal(target[preserved_start:offset+take],pcm[fade:take]):
   raise ValueError('Final PS1 mix changed after transition')
  voice_at=offset+round(6.1*48000)
  encoded=subprocess.run([str(FF),'-v','error','-f','f32le','-ar','48000','-ac','2','-i','pipe:0',
   '-map_metadata','-1','-c:a','libvorbis','-q:a','10','-flags','+bitexact','-fflags','+bitexact',
   '-serial_offset','0','-f','ogg','pipe:1'],input=target.astype('<f4').tobytes(),capture_output=True,check=True).stdout
  encoded=preserve_native_comments(encoded,native_ogg);new=encode_sngw(encoded,raw[:4])
  info=native_title_info(new);decoded=decode(decode_sngw(new))
  if info['frames']!=len(native) or decoded.shape!=native.shape:raise ValueError('Duration changed')
  snr=float(10*np.log10(np.sum(target.astype(float)**2)/np.sum((target-decoded).astype(float)**2)))
  tail=target[voice_at:];difference=tail-decoded[voice_at:]
  speech_snr=float(10*np.log10(np.sum(tail.astype(float)**2)/np.sum(difference.astype(float)**2)))
  if snr<32 or speech_snr<32:raise ValueError(f'Insufficient encoding quality {snr=} {speech_snr=}')
  newbank=bytearray(bank);struct.pack_into('<I',newbank,60,len(new));newbank=bytes(newbank)
  if bank[:60]!=newbank[:60] or bank[64:]!=newbank[64:]:raise ValueError('Other stream metadata changed')
  for path,payload in ((rel,new),(bankrel,newbank)):
   dest=OUT/path;save(dest,payload)
   builds.append({'relative_path':path,'output':dest.relative_to(R).as_posix(),'original_sha256':baseline[path],
    'output_sha256':sha(payload),'reviewed_title_stream':True,'install_eligible':True,
    'source_current_ps1':sources[0 if region=='jp' else 1]})
  preview=D/(region+'_preview.wav')
  subprocess.run([str(FF),'-v','error','-y','-i','pipe:0',str(preview)],input=encoded,capture_output=True,check=True)
  reports.append({'region':region,'frames':len(native),'seconds':len(native)/48000,
   'ps1_mix_offset_seconds':offset/48000,'crossfade_seconds':fade/48000,'voice_start_seconds':voice_at/48000,
   'no_old_jp_audio_after_seconds':(offset+fade)/48000 if region=='jp' else None,
   'full_final_mix_preserved_in_pcm_after_intro_blend':True,'voice_effects_and_reverb_preserved':True,
   'no_pitch_or_time_stretch':True,'native_comments':vorbis_comments(encoded),'snr_db':snr,'speech_snr_db':speech_snr,
   'peak':float(np.max(abs(decoded))),'preview':preview.relative_to(R).as_posix()})
 report={'passed':True,'sources':sources,'rows':reports,'runtime_verified':False}
 save(W/'title_voice_v3_builds.json',(json.dumps(builds,indent=2)+'\n').encode())
 save(D/'verification.json',(json.dumps(report,indent=2)+'\n').encode())
 print(json.dumps(report))
if __name__=='__main__':main()
