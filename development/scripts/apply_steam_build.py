"""Install/restore reviewed local ARC builds with verified backups and rollback."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.steam_arc import SteamArc
from src.steam_executable import validate_executable
from src.steam_region_routes import SHARED,HQ_PRIVATE
from src.steam_audio import wave_info,bank_records,sequence_events,stream_records
from src.steam_stream import TITLE_STREAMS,decode_sngw,ogg_info,clear_records,native_title_info,vorbis_comments
WORK=ROOT/'work/steam_port_20261109'
STEAM=Path('C:/Program Files (x86)/Steam/steamapps/common/Mega Man X Legacy Collection')


def sha(b):return hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['apply','restore'])
    p.add_argument('--manifest',type=Path,default=WORK/'zero_builds.json')
    args=p.parse_args()
    running=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-Process RXC1 -ErrorAction SilentlyContinue).Count"],capture_output=True,text=True,check=True)
    if running.stdout.strip()!='0':raise ValueError('Close RXC1 before changing loaded game files')
    backup=json.loads((WORK/'backup_manifest.json').read_text(encoding='utf-8'))
    baseline={r['relative_path']:r for r in backup['originals']}
    exe=STEAM/'RXC1.exe'
    validate_executable(exe.read_bytes())
    statepath=WORK/'install_state.json'
    previous=json.loads(statepath.read_text(encoding='utf-8')) if statepath.exists() else {'files':[]}
    known={r['relative_path']:r['installed_sha256'] for r in previous['files']}
    private={'nativeDX10/X4/romPC/cliche_br_'+n+'.arc' for n in SHARED}|{'nativeDX10/X4/romPC/'+n for n in HQ_PRIVATE}
    if args.action=='apply':
        builds=json.loads(args.manifest.read_text(encoding='utf-8'))
        if any(r.get('install_eligible') is False for r in builds):raise ValueError('Build requires unresolved native adaptation')
        planned=[(r['relative_path'] if 'relative_path' in r else 'nativeDX10/X4/romPC/'+r['target_arc'],ROOT/r['output'],r['output_sha256']) for r in builds]
        metadata={r.get('relative_path','nativeDX10/X4/romPC/'+r.get('target_arc','')):r for r in builds}
    else:
        planned=[(r['relative_path'],WORK/'original'/r['relative_path'],baseline[r['relative_path']]['sha256']) if r['relative_path'] in baseline else (r['relative_path'],None,None) for r in previous['files']]
    if len({rel for rel,_,_ in planned})!=len(planned):raise ValueError('Duplicate installation target')
    transaction=[]
    for rel,source,expected in planned:
        dest=(STEAM/rel).resolve()
        if not dest.is_relative_to(STEAM.resolve()) or rel not in baseline and rel not in private:raise ValueError('Unapproved target')
        if rel in baseline:
            backup_bytes=(WORK/'original'/rel).read_bytes()
            if sha(backup_bytes)!=baseline[rel]['sha256']:raise ValueError('Original backup invalid')
        old=dest.read_bytes() if dest.exists() else None
        new=source.read_bytes() if source else None
        if old is None:
            if rel not in private or rel in known:raise ValueError('Installed original/mode file missing')
        elif sha(old) not in (baseline.get(rel,{}).get('sha256'),known.get(rel)):raise ValueError('Unrecognized installed asset')
        if new is None:
            if args.action!='restore' or rel not in private:raise ValueError('Unexpected file removal')
            transaction.append((rel,dest,old,new));continue
        if sha(new)!=expected:raise ValueError('Build artifact hash mismatch')
        if dest.suffix.lower()=='.arc':SteamArc(new).validate_stream_order()
        elif rel=='RXC1.exe':validate_executable(new)
        elif rel.startswith('nativeDX10/X4/sound/') and rel in baseline:
            if dest.suffix=='.xsew':wave_info(new)
            elif dest.suffix=='.sbkr':bank_records(new)
            elif dest.suffix=='.srqr':sequence_events(new)
            elif dest.suffix=='.stqr':
                if rel in TITLE_STREAMS.values():
                    clear_records(new)
                    if backup_bytes[:60]!=new[:60] or backup_bytes[64:]!=new[64:]:
                        raise ValueError('Title bank may only change first stream byte size')
                    clip=next(k for k,v in TITLE_STREAMS.items() if v==rel)
                    clip_source=next((p for r,p,_ in planned if r==clip),None)
                    if clip_source is None or clear_records(new)[0]['size']!=clip_source.stat().st_size:
                        raise ValueError('Title stream/bank must be installed together')
                else:stream_records(new)
            elif dest.suffix=='.sngw':
                # Only an exact existing local stream may be installed. No
                # unverified encoder or arbitrary opaque stream is accepted.
                donor=metadata[rel].get('original_audio_source') if args.action=='apply' else rel
                if rel in TITLE_STREAMS and args.action=='apply' and metadata[rel].get('reviewed_title_stream'):
                    info=native_title_info(new);oldinfo=native_title_info(backup_bytes)
                    if vorbis_comments(decode_sngw(new))!=vorbis_comments(decode_sngw(backup_bytes)):
                        raise ValueError('Native title comments changed')
                    if any(info[k]!=oldinfo[k] for k in ('frames','channels','rate','serial')):
                        raise ValueError('Title stream duration/format changed')
                    if not any(r==TITLE_STREAMS[rel] for r,_,_ in planned):
                        raise ValueError('Missing title stream metadata')
                elif donor not in baseline or sha(new)!=baseline[donor]['sha256'] or (WORK/'original'/donor).read_bytes()!=new:
                    raise ValueError('Unverified native sound stream')
            else:raise ValueError('Unsupported audio extension')
        else:raise ValueError('Installer target format is not implemented')
        if source.resolve()==dest:raise ValueError('Source/destination overlap')
        transaction.append((rel,dest,old,new))
    written=[]
    try:
        for rel,dest,old,new in transaction:
            if new is None:
                dest.unlink();written.append((dest,old));continue
            temporary=dest.with_name(dest.name+'.cliche-tmp')
            if temporary.exists():raise ValueError('Temporary file collision')
            temporary.write_bytes(new)
            if sha(temporary.read_bytes())!=sha(new):raise ValueError('Staged file checksum failed')
            os.replace(temporary,dest);written.append((dest,old))
            if dest.read_bytes()!=new:raise ValueError('Installed read-back failed')
    except Exception:
        for dest,old in reversed(written):
            if old is None:dest.unlink()
            else:dest.write_bytes(old)
        raise
    updated={r['relative_path']:r for r in previous['files']}
    for rel,dest,old,new in transaction:
        if new is None:updated.pop(rel,None)
        else:updated[rel]={'relative_path':rel,'original_sha256':baseline.get(rel,{}).get('sha256'),'installed_sha256':sha(new)}
    state={'action':args.action,'build_manifest':str(args.manifest),'files':list(updated.values()),'verified':True}
    statepath.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(state))


if __name__=='__main__':main()
