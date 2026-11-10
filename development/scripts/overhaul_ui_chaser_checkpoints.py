"""저장된 실제 stage5 체이서 진행을 찾는 읽기 전용 상태 감사."""
import gzip,json,hashlib,struct,sys,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'work/overhaul_20261105/ui/riko_chaser/checkpoint_scan.json'

def main():
    paths=set()
    for folder in ('work/ver_buki_riko','work/ver_rin_nana','work/overhaul_20261105','out','completed','ePSXe2018'):
        for parent,dirs,names in os.walk(ROOT/folder):
            for name in names:
                if re.fullmatch(r'SLUS_005\.61\.\d{3}',name) or name=='current_progress' or name.endswith(('.state','.state.gz')):
                    paths.add(Path(parent)/name)
    extra=json.loads((ROOT/'work/overhaul_20261105/audio/ride_checkpoint_scan_extra.json').read_text('utf8'))
    paths.update(ROOT/r['path'] for r in extra['extra_states'])
    paths=sorted(paths)
    cache={};candidates=[];errors=[]
    for p in paths:
        data=p.read_bytes();h=hashlib.sha256(data).hexdigest()
        if h not in cache:
            try:
                s=gzip.decompress(data)
                if len(s)!=4254418 or not s.startswith(b'ePSXe\x06\x00SLUS_005.61'):raise ValueError('Unsupported format')
                ram=s[442:442+0x200000];player=ram[0x1418c8:0x1418c8+228]
                cache[h]={'character':player[2],'stage':ram[0x1721cc],'area':ram[0x1721cd],
                          'animation':player[0x17],'frame':player[0x47],'ride_state':player[0xc5],
                          'ride_animation':player[0xd4],'player_state':list(player[4:8]),'hp':player[0x5c],
                          'world':[struct.unpack_from('<i',player,o)[0]/65536 for o in (8,12)],
                          'player_sha256':hashlib.sha256(player).hexdigest()}
            except (ValueError,OSError) as e:cache[h]={'error':str(e)}
        q=cache[h]
        if 'error' in q:errors.append({'path':p.relative_to(ROOT).as_posix(),**q})
        elif q['stage']==5 or (q['ride_state'] and 65<=q['ride_animation']<=76):candidates.append({'path':p.relative_to(ROOT).as_posix(),'sha256':h,**q})
    report={'files_scanned':len(paths),'unique_states':len(cache),'stage5_or_chaser_candidates':candidates,
            'actual_chaser_candidates':[r for r in candidates if r['ride_state'] and 65<=r['ride_animation']<=76],
            'errors':errors,'source_modified':False,'character_modified':False,'emulator_control':False}
    OUT.write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(report))

if __name__=='__main__':main()
