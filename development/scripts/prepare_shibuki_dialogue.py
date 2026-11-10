"""Prepare review-only same-size ARC proposals; never write a game BIN."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import sha256
from src.psx_shibuki_text import rename_shibuki
from src.psx_ui_text_space import expand_dialogue,expand_dialogue_from_parts

def prepare(candidate,out):
    if out.exists():raise ValueError('Review output exists')
    recipe=json.loads((candidate/'recipe.json').read_text('utf8'));items={r['file']:r for r in recipe['files']};prepared=[]
    for name,fn in [('PL00_U.ARC',expand_dialogue),('PL02_U.ARC',expand_dialogue_from_parts)]:
        raw=(candidate/name).read_bytes()
        if sha256(raw)!=items[name]['sha256']:raise ValueError('UI source changed')
        text,changes=rename_shibuki(entry(raw,0x15));arc,proof=fn(raw,text)
        if rename_shibuki(entry(arc,0x15))[1]['name_count']:raise ValueError('Character name remains')
        prepared.append((name,arc,dict(proof,dialogue=changes)))
    out.mkdir()
    report={'kind':'review_only_not_in_game','approval_received':False,'source_candidate':str(candidate.relative_to(ROOT)),'source_recipe_sha256':sha256((candidate/'recipe.json').read_bytes()),'files':{}}
    for name,arc,proof in prepared:
        (out/name).write_bytes(arc);report['files'][name]=proof
    (out/'proposal.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({'output':str(out),'approval_received':False,'game_bin_written':False,'hashes':{n:sha256(a) for n,a,p in prepared}}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.candidate.resolve(),a.output.resolve())
