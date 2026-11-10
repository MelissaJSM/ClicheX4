"""나나 추가 공중/분신17참조의 원래 압축 슬롯을 사용한다."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import optimize_nana_arrival as optimizer
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--frames',type=int,nargs='*');args=p.parse_args();a=args.art.resolve()
 if not a.is_relative_to(ROOT/'work/ver_rin_nana/nana_art/vehicle_hurt_v1'):raise ValueError('Isolated Nana air/clone art required')
 art=json.loads((a/'art.json').read_text('utf8'))
 if art['task']!='x_nana'or art['scope']!='base_nana_vehicle_hurt_37':raise ValueError('Wrong art scope')
 optimizer.a=a
 for n in args.frames or[r['frame']for r in art['groups']]:print(optimizer.run(n),flush=True)
