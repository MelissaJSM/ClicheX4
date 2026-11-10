"""새 공중 의상과 정확히 동일한 공유 본체를 최신 리코 작업 ARC 위에 넣는다."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
W=ROOT/'work/sprite_style_unification_20261107'
Z=W/'zero_audit'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Z))
import pack_riko_cloth as engine
from scripts.overhaul_sprites_audit import render
from src.psx_disc import file_hash

def main():
    p=argparse.ArgumentParser();p.add_argument('parent_proposal',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
    proposal_path=args.parent_proposal.resolve();out=args.output.resolve()
    assert proposal_path.is_relative_to(W) and out.is_relative_to(W) and not out.exists()
    parent=json.loads(proposal_path.read_text('utf8'))
    source=ROOT/parent['resource'];parent_hash=parent['after_sha256']
    assert file_hash(source)==parent_hash
    arc=source.read_bytes()
    art=W/'riko/air_wall_cloth01/registered02'
    reg=json.loads((art/'registration.json').read_text('utf8'))
    reference=(ROOT/reg['source_arc']).read_bytes()
    assert engine.native.sha(reference)==reg['source_sha256']
    aliases=json.loads((art.parent/'aliases.json').read_text('utf8'))['matches']
    masters={}
    for r in reg['frames']:
        f=ROOT/r['target'];assert file_hash(f)==r['target_sha256']
        a=np.array(Image.open(f));assert a.shape==(384,384) and a.dtype==np.uint8 and a.max()<=15
        n=r['ref'];assert np.array_equal(render(arc,0,0,n)[0],render(reference,0,0,n)[0])
        masters[n]=a
    keys={(r['bank'],r['ref']):(r['master'],*r['translation']) for r in aliases}
    targets={}
    for (b,n),(master,dx,dy) in keys.items():
        old=render(arc,b,b*5,n)[0];key_old=render(arc,0,0,master)[0]
        assert np.array_equal(old,engine.shifted(key_old,dx,dy)),(b,n,'shared pose no longer exact')
        targets[b,n]=engine.shifted(masters[master],dx,dy)
    engine.PARENT_SHA=parent_hash;engine.PARENT=source;engine.KEYS=keys
    engine.OUT=out;engine.CACHE=art.parent/'pack_cache02'
    def expected(data):
        engine.native.need(engine.native.sha(data)==parent_hash,'Wrong current parent')
        return {k:v.copy() for k,v in targets.items()}
    engine.get_targets=expected
    result,proof=engine.build(arc,targets)
    repeated,_=engine.build(arc,targets)
    assert result==repeated
    rejections=[]
    for case in ('parent','missing','pixel'):
        data=arc;bad={k:v.copy() for k,v in targets.items()}
        if case=='parent':data=bytes([arc[0]^1])+arc[1:]
        elif case=='missing':del bad[next(iter(bad))]
        else:bad[0,21][135,145]^=1
        try:engine.build(data,bad)
        except ValueError as e:rejections.append({'case':case,'reason':str(e)})
        else:raise AssertionError('Invalid candidate accepted')
    proof.pop('heads_preserved_pixels_per_reference',None)
    proof['head_and_game_contact_regions']=reg['frames']
    proof['source_prior_changes_preserved']=True
    out.mkdir();(out/'PL01_U.ARC').write_bytes(result);engine.boards(arc,result)
    report={'source_arc':str(source.relative_to(ROOT)),'source_arc_sha256':parent_hash,
            'resource':str((out/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':engine.native.sha(result),
            'target_references':[f'b{b}_{n:03d}' for b,n in keys], 'verification':proof,
            'registration':str((art/'registration.json').relative_to(ROOT)),
            'reproducible':True,'rejections':rejections,'game_changed':False,'runtime_verified':False}
    (out/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'sha256':report['after_sha256'],'refs':report['target_references'],'counts':proof['counts']}))

if __name__=='__main__':main()
