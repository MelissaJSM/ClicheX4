"""시험용 F1 사본을 채취하고 사용자의 슬롯/미리보기는 즉시 복원한다."""
import argparse, gzip, json, shutil, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.project import digest

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--project',choices=['ver_buki_riko','ver_rin_nana'],required=True)
    p.add_argument('--session',type=Path,required=True)
    p.add_argument('--expected-f1',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();session=a.session.resolve();out=a.output.resolve()
    if not session.is_relative_to(ROOT/'work'/a.project/'emulator_sessions') or not out.is_relative_to(ROOT/'work/overhaul_20261105') or out.exists():raise ValueError('Unexpected paths')
    rec=json.loads((session/'session.local.json').read_text('utf8'))
    folder=Path(rec['executable']).parent/'sstates';active=folder/'SLUS_005.61.000';pic=folder/'SLUS_005.61.000.pic'
    if digest(active)!=a.expected_f1:raise ValueError('User F1 changed; no save key sent')
    before={q.name:q.read_bytes() if q.exists() else None for q in (active,pic)}
    out.mkdir(parents=True);backup=out/'user_backup';backup.mkdir()
    for name,data in before.items():
        if data is not None:(backup/name).write_bytes(data)
    result=None;new=None
    try:
        result=subprocess.run([sys.executable,str(ROOT/'scripts/korean_runtime_control.py'),'--project',a.project,'key','--session',str(session),'--scan','0x3b'],check=True,capture_output=True,text=True)
        last=None;stable=0
        for _ in range(20):
            data=active.read_bytes()
            if data!=before[active.name]:
                stable=stable+1 if data==last else 0
                if stable>=2:
                    gzip.decompress(data);new=data;break
            last=data;time.sleep(.15)
        if new is None:raise RuntimeError('No stable new F1 captured')
        (out/active.name).write_bytes(new)
        if pic.exists():shutil.copyfile(pic,out/pic.name)
    finally:
        for q in (active,pic):
            data=before[q.name]
            if data is not None:q.write_bytes(data)
            elif q.exists():q.unlink()
        if any((q.read_bytes() if q.exists() else None)!=before[q.name] for q in (active,pic)):raise RuntimeError('Original slot restore failed')
    proof=dict(session=str(session),bin_sha256=rec['bin_sha256'],snapshot_sha256=digest(out/active.name),original_f1_sha256=a.expected_f1,original_slot_and_preview_restored=True,cards_written=False,process_memory_written=False,key_result=json.loads(result.stdout))
    (out/'evidence.json').write_text(json.dumps(proof,indent=2),'utf8');print(json.dumps(proof))

if __name__=='__main__':main()
