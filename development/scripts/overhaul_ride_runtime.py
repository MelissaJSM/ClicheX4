"""검증된 탑승 그래픽 시험 사본을 잠시 F3로 읽고 기존 F1 파일은 즉시 복원한다."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest

def main():
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);a=p.parse_args()
    session=a.session.resolve()
    if not session.is_relative_to(ROOT/'work/ver_buki_riko/emulator_sessions'):raise ValueError('Unexpected session')
    rec=json.loads((session/'session.local.json').read_text('utf8'))
    if rec['bin_sha256']!='3344f2a94a3a88beeb2b6906ee8f2c3d28d1400d2478fc77a395d24af0fce275':raise ValueError('Unexpected mounted candidate')
    source=ROOT/'work/overhaul_20261105/audio/riko_ride_clone_from_rin_v2/SLUS_005.61.000'
    if digest(source)!='4138e294d1ea53c2b776edc5dae97353cac1dff5b0726d3e6e180c3774eebffd':raise ValueError('Unexpected test state')
    active=Path(rec['executable']).parent/'sstates/SLUS_005.61.000'
    if digest(active)!='2d3f00042b10b8512fa3417d57f0e375df2c92cf4203674c98a391866eb4ee64':raise ValueError('User state changed')
    out=ROOT/'work/overhaul_20261105/runtime/riko_ride_v2';out.mkdir(parents=True,exist_ok=False)
    backup=out/'original_f1.000';shutil.copyfile(active,backup);before=digest(active)
    result=None
    try:
        shutil.copyfile(source,active)
        if digest(active)!=digest(source):raise ValueError('Test state installation differs')
        result=subprocess.run([sys.executable,str(ROOT/'scripts/korean_runtime_control.py'),'--project','ver_buki_riko','key','--session',str(session),'--scan','0x3d'],check=True,capture_output=True,text=True)
    finally:
        shutil.copyfile(backup,active)
        if digest(active)!=before:raise RuntimeError('Original F1 restore failed')
    report=dict(scope='Riko graphics runtime on genuine Rin RideArmor progress, not fresh BIN loading',
                source_state=str(source.relative_to(ROOT)),source_state_sha256=digest(source),session=str(session),
                original_f1_sha256=before,original_f1_restored=True,card_files_written=False,
                result=json.loads(result.stdout) if result else None)
    (out/'evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(report))

if __name__=='__main__':main()
