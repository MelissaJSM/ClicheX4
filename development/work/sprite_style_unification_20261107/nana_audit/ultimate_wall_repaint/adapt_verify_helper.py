"""공중 검사 스크립트의 변경 없는 원본을 읽어 벽 전용 사본을 생성한다."""
from pathlib import Path
D=Path(__file__).resolve().parent;dst=D/'verify_native_candidate.py'
if dst.exists():raise ValueError('Fresh local script required')
t=(D.parent/'ultimate_air_repaint/verify_native_candidate.py').read_text('utf8')
changes=[('packed_air_candidate_v1','packed_wall_candidate_v1'),('packed_air_diagnostic_v1','packed_wall_diagnostic_v1'),('joint_native_targets_v2','joint_native_targets_v1'),("D.parent/'native_restore/nova_sync_v1/PL02_U.ARC'","D.parent/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC'"),('122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18','e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031'),('range(33,55,2)','range(55,67,2)'),('(33,0)','(55,0)'),('[33,0]','[55,0]')]
for old,new in changes:
 if old not in t:raise ValueError('Template changed '+old)
 t=t.replace(old,new)
dst.write_text(t,encoding='utf8');print(dst)
