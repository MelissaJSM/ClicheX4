"""Historical v2 initial-voice reproduction. Use build_steam_title_voice_final.py for current PS1 audio."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.steam_stream import decode_sngw,encode_sngw,ogg_info,clear_records,TITLE_STREAMS,preserve_native_comments,native_title_info,vorbis_comments
from src.steam_arc import SteamArc
W=ROOT/'work/steam_port_20261109'
D=W/'title_voice'
FF=ROOT/'work/tools/voice_env/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def decode(ogg):
    return np.frombuffer(subprocess.run([str(FF),'-v','error','-i','pipe:0','-f','f32le','pipe:1'],
        input=ogg,capture_output=True,check=True).stdout,dtype='<f4').reshape(-1,2).copy()

def save(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=raw:raise ValueError('Output collision: '+str(path))
    path.write_bytes(raw)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',choices=['v2'],default='v2')
    args=parser.parse_args()
    output_root=ROOT/f'out/steam_title_voice_20261109_{args.version}'
    review=D/args.version;review.mkdir(parents=True,exist_ok=True)
    baseline={r['relative_path']:r for r in json.loads((W/'backup_manifest.json').read_text('utf8'))['originals']}
    def original(rel):
        raw=(W/'original'/rel).read_bytes()
        if sha(raw)!=baseline[rel]['sha256']:raise ValueError('Original input hash mismatch')
        return raw
    master=ROOT/'work/ver_buki_riko/title_voice_v1/title_master.wav'
    accepted=ROOT/'work/ver_buki_riko/title_voice_v1/title_replacement.xa'
    if sha(accepted.read_bytes())!='0e2f4b8154c91cb61a99e99a2aefbd81e7e8535a973b56c9605b80feff24b626':
        raise ValueError('Accepted title source changed')
    pcm=np.frombuffer(subprocess.run([str(FF),'-v','error','-i',str(master),'-ar','48000','-f','f32le','pipe:1'],
        capture_output=True,check=True).stdout,dtype='<f4').reshape(-1,2)
    # The approved master contains logo effects through 6.27 s. Speech is 6.30 onward.
    voice=pcm[302400:].copy()
    live=np.flatnonzero(np.max(abs(voice),axis=1)>1/32768)
    voice=voice[:int(live[-1])+1]
    builds=[];reports=[]
    for rel,bankrel in TITLE_STREAMS.items():
        region='en' if '/eng/' in rel else 'jp'
        raw=original(rel);ogg=decode_sngw(raw)
        if encode_sngw(ogg,raw[:4])!=raw:raise ValueError('Original roundtrip failed')
        native=decode(ogg);info=ogg_info(ogg)
        bank=original(bankrel);records=clear_records(bank);first=records[0]
        if (len(raw),len(native),info['frames'])!=(first['size'],first['frames'],first['frames']):
            raise ValueError('Native duration metadata mismatch')
        # JP title sound is a different composition, with the call after 9.96 s.
        # Fade its quiet effect tail before that onset; do not shift speech pitch/speed.
        cut,voice_at=(299520,302400) if region=='en' else (476160,479040)
        target=native.copy();target[cut:]=0
        tail=1440
        target[cut:cut+tail]=native[cut:cut+tail]*np.linspace(1,0,tail)[:,None]
        if voice_at+len(voice)>len(target):raise ValueError('Voice exceeds native title length')
        target[voice_at:voice_at+len(voice)]+=voice
        if np.max(abs(target[cut:]))>=1:raise ValueError('Replacement speech clipping')
        encoded=subprocess.run([str(FF),'-v','error','-f','f32le','-ar','48000','-ac','2','-i','pipe:0',
            '-map_metadata','-1','-c:a','libvorbis','-q:a','10','-flags','+bitexact','-fflags','+bitexact',
            '-serial_offset','0','-f','ogg','pipe:1'],input=target.astype('<f4').tobytes(),capture_output=True,check=True).stdout
        encoded=preserve_native_comments(encoded,ogg)
        new=encode_sngw(encoded,raw[:4]);decoded=decode(decode_sngw(new));newinfo=native_title_info(new)
        if len(decoded)!=len(native) or newinfo['frames']!=len(native):raise ValueError('Duration changed')
        snr=float(10*np.log10(np.sum(target.astype(float)**2)/np.sum((target-decoded).astype(float)**2)))
        voice_snr=float(10*np.log10(np.sum(voice.astype(float)**2)/np.sum((voice-decoded[voice_at:voice_at+len(voice)]).astype(float)**2)))
        if snr<32 or voice_snr<32 or np.max(abs(decoded[cut:]))>=1:
            raise ValueError(f'Stream quality/clipping check failed: {snr=}, {voice_snr=}, peak={np.max(abs(decoded[cut:]))}')
        newbank=bytearray(bank);struct.pack_into('<I',newbank,60,len(new));newbank=bytes(newbank)
        if bank[:60]!=newbank[:60] or bank[64:]!=newbank[64:]:raise ValueError('Unrelated STQR change')
        for path,payload in [(rel,new),(bankrel,newbank)]:
            output=output_root/path;save(output,payload)
            builds.append({'relative_path':path,'output':output.relative_to(ROOT).as_posix(),
                'original_sha256':sha(original(path)),'output_sha256':sha(payload),
                'reviewed_title_stream':True,'install_eligible':True})
        preview=review/(region+'_preview.wav')
        subprocess.run([str(FF),'-v','error','-y','-i','pipe:0',str(preview)],input=encoded,capture_output=True,check=True)
        reports.append({'region':region,'native_frames':len(native),'seconds':len(native)/48000,
            'source_roundtrip_identical':True,'prefix_pcm_identical_until':cut/48000,'speech_start':voice_at/48000,
            'voice_samples':len(voice),'pitch_or_speed_changed':False,'other_clear_clips_and_events_preserved':True,
            'snr_db':snr,'speech_snr_db':voice_snr,'peak':float(np.max(abs(decoded))),
            'original_decoded_peak':float(np.max(abs(native))),
            'native_comments':vorbis_comments(encoded),'native_comments_byte_preserved':True,
            'sngw_sha256':sha(new),'preview':preview.relative_to(ROOT).as_posix()})
    embedded=[]
    for path in (W/'original/nativeDX10/X4/romPC').glob('*.arc'):
        for e in SteamArc(path.read_bytes()).entries:
            if e.payload[:4]==b'STQR' or '\\bgm\\' in e.name:embedded.append((path.name,e.name))
    if embedded:raise ValueError('Unexpected embedded stream bank requires review')
    report={'passed':True,'source_master_sha256':sha(master.read_bytes()),'source_accepted_xa_sha256':sha(accepted.read_bytes()),
        'title_banks_embedded_in_arc':embedded,'rows':reports,'game_listening_verified':False}
    save(W/f'title_voice_{args.version}_builds.json',(json.dumps(builds,indent=2)+'\n').encode())
    save(review/'verification.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps(report))

if __name__=='__main__':main()
