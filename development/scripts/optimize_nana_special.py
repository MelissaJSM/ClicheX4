"""나나 특수 자세의 원래 압축 슬롯만 탐색한다."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import optimize_nana_arrival as optimizer
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--frames',type=int,nargs='*');args=p.parse_args();a=args.art.resolve()
 if not a.is_relative_to(ROOT/'work/ver_rin_nana/nana_art/special_v1'):raise ValueError('Isolated Nana special art required')
 art=json.loads((a/'art.json').read_text('utf8'))
 if art['task']!='x_nana'or art['scope']!='base_nana_special_7':raise ValueError('Wrong art scope')
 optimizer.a=a
 for n in args.frames or[r['frame']for r in art['groups']]:print(optimizer.run(n),flush=True)
