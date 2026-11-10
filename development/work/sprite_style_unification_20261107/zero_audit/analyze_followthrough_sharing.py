"""다음 다섯 참조의 실제 공유 소유/소비 타일과 정확 사본을 읽기 조사."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame
D=Path(__file__).parent/'rin_extension';P=D/'prepared_spin01/PL01_U.ARC';arc=P.read_bytes()
assert hashlib.sha256(arc).hexdigest()=='cf0b079549ea6f1968f3eeb8be37541583f070c134a628c7ea5131fc745dee2a'
selected={(1,146),(1,156),(1,158),(0,197),(0,212)};rows=[];done=set()
for b,n in sorted(selected):
 bank=graphics_bank(entry(arc,2),b);frame=bank['frames'][n];identity=(b,frame['offset'])
 if identity in done:continue
 done.add(identity);owners=[f['index']for f in bank['frames']if f['offset']==frame['offset']]
 targets=[k for k in owners if(b,k)in selected];support=[k for k in owners if(b,k)not in selected]
 parts={k:composition_frame(entry(arc,3),b*5,k)['parts']for k in owners}
 owned={p['tile']for k in targets for p in parts[k]};protected={p['tile']for k in support for p in parts[k]}
 rows.append({'bank':b,'owners':owners,'targets':targets,'support':support,'tile_count':frame['tile_count'],'parts':{str(k):len(v)for k,v in parts.items()},'owned_tiles':sorted(owned),'all_consumed_support_tiles':sorted(protected),'safe_pool':sorted(owned-protected),'partial_group':b==1 and any(42<=k<=49 for k in owners)})
assert np.array_equal(render(arc,0,0,197)[0],render(arc,0,0,212)[0])
out={'source':P.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(arc).hexdigest(),'exact_display_aliases':{'b0_212':'b0_197'},'groups':rows,'future_policy':'모든 비대상 소유자의 전체 소비 타일(가려진 셀 포함) 보존. 새 원화 미수용/미패킹. 은행 끝과 32타일 한계 유지.','source_changed':False}
(D/'followthrough01/sharing_plan.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(out,ensure_ascii=False))
