"""공중 검토기의 별도 사본에 실제 벽 시간표와 복귀39/40을 연결한다."""
from pathlib import Path
D=Path(__file__).resolve().parent
for name in('make_native_cycle.py','verify_native_cycle.py'):
 dst=D/name
 if dst.exists():raise ValueError('Fresh local helper required')
 t=(D.parent/'ultimate_air_repaint'/name).read_text('utf8')
 if name=='make_native_cycle.py':
  edits=[("D.parent/'native_restore/nova_sync_v1/PL02_U.ARC'","D.parent/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC'"),('packed_air_candidate_v1','packed_wall_candidate_v1'),('122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18','e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031'),("[(10,'상승'),(11,'하강'),(12,'착지'),(122,'상승 사격'),(123,'하강 사격'),(124,'착지 사격')]","[(13,'벽 13'),(14,'벽 14 / 공중39 복귀'),(15,'벽 15'),(125,'벽 사격125'),(126,'벽 사격126 / 공중40 복귀'),(127,'벽 사격127')]"),('s[\'ref\']in range(33,55)','s[\'ref\']in {39,40,*range(55,67)}'),('range(33,55,2)','range(55,67,2)'),('range(34,55,2)','range(56,67,2)'),('(0,*range(33,55))','(0,39,40,*range(55,67))'),('공중','벽'),('10·11·12·122·123·124','13·14·15·125·126·127'),('native air review','native wall review')]
 else:
  edits=[('page.wait_for_timeout(650)','page.wait_for_timeout(max(650,round(seq[0][\'calls\']/60*1000)+120))'),('review.selectRef(52)','review.selectRef(64)'),('headless_052','headless_064'),('review.selectRef(39)','review.selectRef(57)'),('headless_039','headless_057')]
 for old,new in edits:
  if old not in t:raise ValueError(name+' template changed '+old)
  t=t.replace(old,new)
 dst.write_text(t,encoding='utf8')
 print(dst)
