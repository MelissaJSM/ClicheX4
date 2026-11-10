"""Rebuild all proposed resources and compare exact bytes before disc work."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import D
from scripts.discover_inputs import sha256
from scripts.prepare_korean_dialogue import main as dialogue
from scripts.prepare_korean_ui import main as ui
from scripts.prepare_korean_menu import main as menu
from scripts.prepare_korean_ending import main as ending
from scripts.prepare_korean_stage_labels import main as stages
from scripts.prepare_korean_boss import main as bosses

def main(output):
    output.mkdir(exist_ok=False);results={}
    for source,fn in [('dialogue_full_v5',dialogue),('ui_proposal_v7',ui),('menu_proposal_v3',menu),('ending_proposal_v4',ending),('stage_proposal_v2',stages),('boss_proposal_v3',bosses)]:
        target=output/source;fn(target);report=json.loads((D/source/'proposal.json').read_text('utf-8'));checked={}
        for name in report['files']:
            a=(D/source/name).read_bytes();z=(target/name).read_bytes()
            if a!=z:raise ValueError(f'Non-reproducible resource {source}/{name}')
            checked[name]=sha256(z)
        results[source]=checked
    result={'exact_resource_reproduction':results,'resource_comparisons':sum(len(r) for r in results.values()),'game_bin_written':False}
    (output/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps({'reproduced':result['resource_comparisons'],'game_bin_written':False}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.output)
