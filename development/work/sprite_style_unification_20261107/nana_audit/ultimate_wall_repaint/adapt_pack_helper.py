"""동결 공중 패커를 변경하지 않고 벽 전용 독립 사본을 만든다."""
from pathlib import Path
D=Path(__file__).resolve().parent
src=D.parent/'ultimate_air_repaint/pack_native.py';dst=D/'pack_native.py'
if dst.exists():raise ValueError('Fresh local script required')
t=src.read_text('utf8')
changes=[('새 얼티밋 공중 전후 22참조','새 얼티밋 벽 전후 12참조'),('range(33,55)','range(55,67)'),('range(33,55,2)','range(55,67,2)'),("bced7f9086a9e6a72440bab25cda7e0c87ccc121a2ffbbc970f750dee257da45","122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18"),("len(manifest['frames'])==22","len(manifest['frames'])==12"),('packed_air_diagnostic_v1','packed_wall_diagnostic_v1'),('joint_native_targets_v2','joint_native_targets_v1'),("D.parent/'native_restore/nova_sync_v1/PL02_U.ARC'","D.parent/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC'"),('(33,39,45,51)','(55,61)'),('min(start+6,55)','min(start+6,67)'),("f'air {n}/{n+1}'","f'wall {n}/{n+1}'")]
for old,new in changes:
 if old not in t:raise ValueError('Template changed '+old)
 t=t.replace(old,new)
dst.write_text(t,encoding='utf8')
print(dst)
