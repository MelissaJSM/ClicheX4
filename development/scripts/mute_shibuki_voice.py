"""Mute only verified X gameplay samples in PL00/PL02, preserving native SFX."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc, sha256
from scripts.inventory_riko_voice import parse_bank
from scripts.project import working_cue
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks
from src.psx_spu_audio import decode_spu, silence_fixed_oneshot, validate_oneshot_template

PARENT=ROOT/'out/ver_buki_riko/hud_emblems_20261028T063603173029Z'
PARENT_SHA='e95273a35a45521ca6fd4ac2ae87562b2749fcd50145e6a1f292269c70468bac'
SOURCE=ROOT/'MegaMan X4.bin'
SOURCE_SHA='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
HEADER_SHA='22ebe296498468fe7a1e9de2b74f18bb185b391e0930ae530646c6e94037d2ed'
BODY_SHA='3aae0b66f594a8d09dac66c609701c5d0823c240522966c5bc0c57df073a16c2'
RECORDS={'PL00_U.ARC':{'lba':1135,'size':796672},'PL02_U.ARC':{'lba':1887,'size':796672}}
WORK=ROOT/'work/ver_buki_riko/shibuki_voice_mute_v1'

def require(test,message):
    if not test:raise ValueError(message)

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def save(path,value):
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)

def mute_archive(current,original):
    require(len(current)==len(original)==796672,'Unsupported archive length')
    layout=psx_arc(current)
    native=psx_arc(original)
    head,body_entry=layout[12:14]
    require(head['type']=='0x6' and body_entry['type']=='0x20301','Unexpected voice entry types')
    require(head['offset']==706560 and head['size']==3164 and body_entry['offset']==710656 and body_entry['size']==57216,
            'Unsupported voice bank placement')
    def data(raw,e):return raw[e['offset']:e['offset']+e['size']]
    header,body=data(current,head),data(current,body_entry)
    require(sha256(header)==HEADER_SHA and sha256(body)==BODY_SHA,'Voice source header/body hash differs')
    require(header==data(original,native[12]) and body==data(original,native[13]),'Voice differs from original')
    bank=parse_bank(header,body,True)
    require((bank['slot'],bank['wave_count'],bank['command_count'],bank['tone_count'],bank['program_count'])==(3,12,13,13,1),
            'Unsupported voice bank command/wave structure')
    require(bank['initial_padding_bytes']==0,'Unexpected voice bank padding')
    mapped={t['wave_id'] for c in bank['commands'] for t in c['tones']}
    require(mapped==set(range(1,13)),'Voice commands do not cover exactly all waves')
    require(all((int(c['command_hex'][:2],16)&63)==3 for c in bank['commands']),'Command points to a nonvoice bank')
    muted=bytearray(body);cursor=0;wave_proof=[]
    for wave in bank['waves']:
        off,size=wave['body_offset'],wave['bytes']
        require(off==cursor and off+size<=len(body),'Overlapping or incomplete wave coverage')
        raw=body[off:off+size];capacity=validate_oneshot_template(raw)
        quiet=silence_fixed_oneshot(raw)
        decoded=decode_spu(quiet)
        require(not any(decoded.pcm) and len(decoded.pcm)==capacity,'Voice is not same-duration exact silence')
        require(quiet[:16]==raw[:16] and quiet[-16:]==raw[-16:] and quiet[1::16]==raw[1::16],
                'Reserved blocks or playback flags changed')
        muted[off:off+size]=quiet;cursor+=size
        wave_proof.append({**wave,'before_decoded_peak':max(abs(v) for v in decode_spu(raw).pcm),
            'after_sha256':sha256(quiet),'decoded_peak_lsb':0,'pcm_samples':capacity,
            'played_blocks':decoded.played_blocks,'end_flag':decoded.end_flag,'flags_and_reserved_blocks_preserved':True})
    require(cursor==len(body),'Unaccounted voice bytes')
    output=bytearray(current);lo=body_entry['offset'];hi=lo+len(body);output[lo:hi]=muted;output=bytes(output)
    require(output[:lo]==current[:lo] and output[hi:]==current[hi:],'Nonvoice archive bytes changed')
    structure=lambda raw:[{k:v for k,v in e.items() if k!='sha256'} for e in psx_arc(raw)]
    require(structure(output)==structure(current),'ARC layout changed')
    for e in layout:
        if e['index']!=13:require(data(output,e)==data(current,e),'Other entry changed')
    require(parse_bank(header,bytes(muted),True)['commands']==bank['commands'],'Voice command mapping changed')
    return output,{'bank':bank,'waves':wave_proof,'voice_body_entry':body_entry,'voice_header_entry':head,
        'after_body_sha256':sha256(muted),'voice_commands_silenced':13,'unique_waves_silenced':12,
        'changed_voice_bytes':sum(a!=b for a,b in zip(body,muted)),
        'nonvoice_entries_graphics_hud_text_and_padding_preserved':True,
        'header_pitch_pan_adsr_flags_lengths_preserved':True,'runtime_verified':False}

def build():
    game=PARENT/'shibuki_riko.bin'
    require(digest(SOURCE)==SOURCE_SHA and digest(game)==PARENT_SHA,'Unsupported original or accepted parent hash')
    original,current={},{}
    for path,values in ((SOURCE,original),(game,current)):
        with path.open('rb') as stream:
            reader=DiscReader(stream,path.stat().st_size)
            for name,rec in RECORDS.items():values[name]=reader.read(rec['lba'],rec['size'])
    changes,checks={},{}
    for name in RECORDS:changes[name],checks[name]=mute_archive(current[name],original[name])
    require(checks['PL00_U.ARC']['after_body_sha256']==checks['PL02_U.ARC']['after_body_sha256'],'Armor voice copies differ')
    # Reproduce real outputs and reject invalid sources before any game output.
    negative=[]
    for name in RECORDS:
        require(mute_archive(current[name],original[name])[0]==changes[name],'Mute output does not reproduce')
        corrupt=bytearray(current[name]);corrupt[710674]^=1
        for label,wrong in [('already_muted',changes[name]),('modified_wave',bytes(corrupt)),('truncated',current[name][:-1])]:
            try:mute_archive(wrong,original[name])
            except ValueError:negative.append(name+':'+label)
            else:raise ValueError('Invalid voice source accepted: '+label)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    package=WORK/stamp;output=ROOT/'out/ver_buki_riko'/('shibuki_voice_mute_'+stamp)
    require(not package.exists() and not output.exists(),'Output collision')
    package.mkdir(parents=True,exist_ok=False);output.mkdir(exist_ok=False)
    updates=[]
    for name,changed in changes.items():
        (package/name).write_bytes(changed)
        updates.append(({**RECORDS[name],'sha256':sha256(current[name])},changed))
    save(package/'recipe.json',{'kind':'shibuki_gameplay_voice_muted_v1','source_sha256':SOURCE_SHA,
        'parent_sha256':PARENT_SHA,'parent_build':str(PARENT.relative_to(ROOT)),'checks':checks,
        'files':{n:{'before':sha256(current[n]),'after':sha256(d),'record':RECORDS[n]} for n,d in changes.items()},
        'reproduced_archives':2,'negative_cases_rejected':negative,'runtime_verified':False})
    result=write_archive_copies(game,output/'shibuki_riko.bin',updates,PARENT_SHA)
    actual=[]
    with game.open('rb') as before,(output/'shibuki_riko.bin').open('rb') as after:
        for lba in range(game.stat().st_size//2352):
            a,b=before.read(2352),after.read(2352)
            if a==b:continue
            require(a[:24]==b[:24],'Sector header changed');validate_checks(b)
            hit=[(name,rec) for name,rec in RECORDS.items() if rec['lba']<=lba<rec['lba']+(rec['size']+2047)//2048]
            require(len(hit)==1,'Nonplayer sector changed')
            name,rec=hit[0];e=checks[name]['voice_body_entry'];arc_off=(lba-rec['lba'])*2048
            for i in range(2048):
                if a[24+i]!=b[24+i]:require(e['offset']<=arc_off+i<e['offset']+e['size'],'Nonvoice disc payload changed')
            actual.append(lba)
        require(not after.read(1),'Output disc grew')
    require(set(actual)=={r['lba'] for r in result['changed_sectors']},'Changed sector set mismatch')
    with (output/'shibuki_riko.bin').open('rb') as stream:
        reader=DiscReader(stream,result['size'])
        for name,rec in RECORDS.items():require(reader.read(rec['lba'],rec['size'])==changes[name],'BIN ARC readback differs')
    require(digest(SOURCE)==SOURCE_SHA and digest(game)==PARENT_SHA,'Protected input changed')
    for name,data in changes.items():(output/name).write_bytes(data)
    (output/'shibuki_riko.cue').write_text(working_cue((PARENT/'shibuki_riko.cue').read_text('ascii'),'shibuki_riko.bin'),'ascii')
    save(output/'sector_changes.json',result)
    manifest={'project':'ver_buki_riko','task':'x_shibuki_audio','kind':'shibuki_gameplay_voice_muted_v1',
        'source_sha256':SOURCE_SHA,'parent_build':str(PARENT.relative_to(ROOT)),'parent_bin_sha256':PARENT_SHA,
        'modified_bin':{k:v for k,v in result.items() if k!='changed_sectors'},'changed_resources':list(changes),
        'changed_sectors':len(actual),'full_disc_sectors_compared':game.stat().st_size//2352,
        'recipe':str((package/'recipe.json').relative_to(ROOT)),'source_script_sha256':digest(Path(__file__)),
        'voice_commands_silenced_per_archive':13,'unique_waveforms_silenced_per_archive':12,
        'gameplay_sfx_bgm_xa_fmv_graphics_text_exe_and_riko_preserved':True,
        'header_timing_pitch_pan_flags_preserved':True,'runtime_verified':False,'user_test_pending':True}
    save(output/'manifest.json',manifest)
    print(json.dumps({'build':str(output.relative_to(ROOT)),'sha256':result['sha256'],
        'changed_sectors':len(actual),'package':str(package.relative_to(ROOT)),'negative_cases_passed':len(negative)}))
    return output

if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    build()
