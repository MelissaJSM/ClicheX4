"""수용 미국판 사본의 타이틀 XA 음성 76섹터만 새 BIN에 기록한다."""
import sys,json,hashlib,shutil
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.psx_xa_audio import validate_audio_sector
from scripts.project import working_cue
from scripts.discover_inputs import DiscReader

PARENT=ROOT/'out/ver_buki_riko/shibuki_voice_mute_20261028T064914983985Z'
PARENT_SHA='ab78f90aef06d8a884a0ea1b5eef36faf5c3f5af1b3df74c92f7dd9922a5ecf2'
SOURCE_SHA='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
RAW_SHA='211dc5c48422ddc288586898a2f5e5dfc28b3a18c0ee9626c4ebd4cd0d9ec455'
D=ROOT/'work/ver_buki_riko/title_voice_v1'
LBA=226570;COUNT=1544
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def require(value,reason):
    if not value:raise ValueError(reason)
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8')

def checked_replacement(before,after):
    require(hashlib.sha256(before).hexdigest()==RAW_SHA,'Unsupported original title XA')
    require(len(after)==len(before)==COUNT*2352,'XA file length changed')
    expected=set(range(936,1544,8));changes=[]
    for i in range(COUNT):
        a=before[i*2352:(i+1)*2352];b=after[i*2352:(i+1)*2352]
        if a==b:continue
        require(i in expected,'Change outside title speech channel/time range')
        validate_audio_sector(a);validate_audio_sector(b,allow_absent_edc=False)
        require(a[:24]==b[:24] and a[2328:2348]==b[2328:2348],'XA header, flags, or padding changed')
        changes.append(i)
    require(set(changes)==expected,'Incomplete title speech replacement')
    return changes

def main():
    source=ROOT/'MegaMan X4.bin';parent=PARENT/'shibuki_riko.bin'
    require(digest(source)==SOURCE_SHA and digest(parent)==PARENT_SHA,'Unsupported game hash')
    preparation=json.loads((D/'preparation.json').read_text('utf-8'))
    revised=(D/'title_replacement.xa').read_bytes()
    require(hashlib.sha256(revised).hexdigest()==preparation['replacement_raw_sha256'],'Prepared audio hash differs')
    with parent.open('rb') as f:f.seek(LBA*2352);raw=f.read(COUNT*2352)
    with source.open('rb') as f:f.seek(LBA*2352);original=f.read(COUNT*2352)
    require(raw==original,'Title sound already modified in parent')
    changes=checked_replacement(raw,revised)
    # Reject corrupted/foreign channels and bad input lengths before creating output.
    negative=[]
    bad_channel=bytearray(revised);bad_channel[2352+24]^=1
    bad_edc=bytearray(revised);bad_edc[936*2352+2348]^=1
    for label,a,b in [('wrong_source',revised,revised),('truncated',raw,revised[:-1]),('other_channel',raw,bytes(bad_channel)),('bad_edc',raw,bytes(bad_edc))]:
        try:checked_replacement(a,b)
        except ValueError:negative.append(label)
        else:raise AssertionError('Invalid patch accepted: '+label)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'out/ver_buki_riko'/('cliche_title_voice_'+stamp);out.mkdir(exist_ok=False)
    target=out/'shibuki_riko.bin';require(not target.exists() and target.resolve()!=parent.resolve(),'Output collision')
    expected={LBA+i for i in changes};full_hash=hashlib.sha256();actual=[]
    with parent.open('rb') as src,target.open('xb') as dst:
        for lba in range(parent.stat().st_size//2352):
            a=src.read(2352);b=revised[(lba-LBA)*2352:(lba-LBA+1)*2352] if lba in expected else a
            dst.write(b);full_hash.update(b)
            if b!=a:actual.append(lba)
    require(set(actual)==expected,'Sector changes mismatch')
    verified=[];reproduced=hashlib.sha256()
    with parent.open('rb') as a,target.open('rb') as b:
        for lba in range(parent.stat().st_size//2352):
            old,new=a.read(2352),b.read(2352)
            expected_bytes=revised[(lba-LBA)*2352:(lba-LBA+1)*2352] if lba in expected else old
            require(new==expected_bytes,'Whole disc readback mismatch');reproduced.update(expected_bytes)
            if old!=new:
                validate_audio_sector(new,allow_absent_edc=False);verified.append(lba)
        require(not b.read(1),'Output length changed')
    require(reproduced.hexdigest()==full_hash.hexdigest()==digest(target),'Reproduced disc hash differs')
    require(digest(source)==SOURCE_SHA and digest(parent)==PARENT_SHA,'Protected inputs changed')
    (out/'shibuki_riko.cue').write_text(working_cue((PARENT/'shibuki_riko.cue').read_text('ascii'),'shibuki_riko.bin'),'ascii')
    shutil.copy2(D/'cliche_title_final.wav',out/'cliche_title_preview.wav')
    manifest={'project':'ver_buki_riko','task':'cliche_title_voice','kind':'cliche_title_call_local_tts_v1',
        'source_sha256':SOURCE_SHA,'parent_build':str(PARENT.relative_to(ROOT)),'parent_bin_sha256':PARENT_SHA,
        'modified_bin':{'sha256':full_hash.hexdigest(),'size':target.stat().st_size},
        'changed_resources':['/XA/BGM5_U.XA;1 channel 0 speech tail'],
        'resource_lba':LBA,'resource_raw_sectors':COUNT,'changed_sectors':len(actual),
        'changed_lba':actual,'full_disc_sectors_compared':parent.stat().st_size//2352,
        'same_size':True,'disc_reproduction_verified':True,'negative_cases_rejected':negative,
        'preparation':'work/ver_buki_riko/title_voice_v1/preparation.json',
        'graphics_text_exe_gameplay_audio_other_xa_fmv_preserved':True,
        'title_effect_prefix_seconds_preserved':6.24,'runtime_audio_verified':False,'user_accepted':False}
    save(out/'manifest.json',manifest)
    save(D/'build.json',{'build':str(out.relative_to(ROOT)),'cue':str((out/'shibuki_riko.cue').relative_to(ROOT)),
        'bin_sha256':full_hash.hexdigest(),'manifest':str((out/'manifest.json').relative_to(ROOT))})
    print(json.dumps({'build':str(out.relative_to(ROOT)),'sha256':full_hash.hexdigest(),'changed_sectors':len(actual),'negative_tests':len(negative)}))
if __name__=='__main__':main()
