"""저장된 실제 화면에서 비동기 업로드로 놓친 세 사격 자세를 재검색한다."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from PIL import Image
from src.epsxe_state import match_sprite
from scripts.project import digest
d=ROOT/'work/ver_rin_nana/nana_batch_runtime/20261029T070329729527Z';results=[];screens={p.name:Image.open(p).convert('RGB') for p in d.glob('*.png') if p.name.startswith(('observed_','actual_'))}
for n in (34,52,54):
 targets={digest(p):p for p in d.glob(f'expected_{n:03d}_*.png')}
 for p in targets.values():
  im=Image.open(p)
  for name,screen in screens.items():
   matches=match_sprite(screen,im)
   if matches:results.append({'frame':n,'target':p.name,'observed_screen':name,'matches':matches,'capture_time_not_same_as_target_ram_sample':True})
out=Path(__file__).parent/'crosscheck_runtime.json';out.write_text(json.dumps({'evidence':d.relative_to(ROOT).as_posix(),'results':results,'matched_frames':sorted({r['frame'] for r in results})},indent=2),'utf8');print(out);print(sorted({r['frame'] for r in results}))
