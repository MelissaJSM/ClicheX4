from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent.parent)]
from prepare_run_repaint import page,RUN_PAGES,Archive
D=Path(__file__).parent
a=Archive((D/'baseline_PL00_U.ARC').read_bytes())
for i,refs in enumerate(RUN_PAGES,1):
    page(a,[n+1 for n in refs],D/'inputs'/f'paired_shot_page{i}.png','이동 사격 원래 위치')
print('4 paired firing reference sheets prepared')
