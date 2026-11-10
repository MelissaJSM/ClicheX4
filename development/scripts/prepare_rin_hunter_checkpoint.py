"""Preserve the HQ checkpoint and refresh only verified graphics in a copy."""
import argparse,gzip,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_hunter import ART,PAL,LO,HI
from scripts.prepare_riko_ui import entry
from scripts.project import digest

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    source=ROOT/'work/ver_rin_nana/checkpoints/before_hq_direction_20261029/current_hq/SLUS_005.61.000'
    if digest(source)!='bb97d6a680ecfde4abd122de9f1a67c79e9a26d99daf042fc9dc932c7646bc7d':raise ValueError('Saved HQ source changed')
    build=ROOT/json.loads((ROOT/'projects/ver_rin_nana/current_build.json').read_text('utf8'))['build']
    if not build.is_relative_to(ROOT/'out/ver_rin_nana'):raise ValueError('Unexpected build')
    recipe=json.loads((build/'hunter/recipe.json').read_text('utf8'))
    for r in recipe['files']:
        if digest(build/'hunter'/r['file'])!=r['sha256']:raise ValueError('HQ candidate changed')
    before=ROOT/'out/ver_rin_nana/rin_hunter_20261029T020955077526Z/hunter'
    oldarc=(before/'ST0D_0Z.ARC').read_bytes();newarc=(build/'hunter/ST0D_0Z.ARC').read_bytes()
    state=gzip.decompress(source.read_bytes())
    if len(state)!=4254418:raise ValueError('Unexpected state size')
    data=bytearray(state);allowed=bytearray(len(state));changes=[]
    def put(pos,old,new,label):
        if len(old)!=len(new) or state[pos:pos+len(old)]!=old:raise ValueError('Unexpected checkpoint '+label)
        data[pos:pos+len(new)]=new;allowed[pos:pos+len(new)]=bytes([1])*len(new);changes.append({'label':label,'offset':pos,'size':len(new),'changed_bytes':sum(a!=b for a,b in zip(old,new))})
    oldp,newp=entry(oldarc,10),entry(newarc,10);pos=state.find(oldp)
    if pos<0 or state.find(oldp,pos+1)>=0:raise ValueError('HQ parts not unique')
    put(pos,oldp,newp,'HQ composition RAM')
    old,new=entry(oldarc,0x10102)[LO:HI],entry(newarc,0x10102)[LO:HI];vram=2569183
    for row in range(144):
        x,y=(512,144+row) if row<32 else (576,row-32)
        put(vram+y*2048+x*2,old[row*128:(row+1)*128],new[row*128:(row+1)*128],'texture row '+str(row))
    oldcol=entry((before/'COL0D_0Z.ARC').read_bytes(),5);newcol=entry((build/'hunter/COL0D_0Z.ARC').read_bytes(),5)
    put(vram+482*2048+96,oldcol[35*32:36*32],PAL,'CLUT 0x7883')
    pos=state.find(oldcol)
    if pos>=0:
        if state.find(oldcol,pos+1)>=0:raise ValueError('Ambiguous palette RAM')
        put(pos,oldcol,newcol,'HQ palette RAM')
    if any(a!=b and not ok for a,b,ok in zip(state,data,allowed)):raise ValueError('Non-graphic state modified')
    output=args.output.resolve()
    if not output.is_relative_to(ROOT/'work/ver_rin_nana/checkpoints'):raise ValueError('Expected isolated preview path')
    output.mkdir(exist_ok=False)
    target=output/source.name;target.write_bytes(gzip.compress(bytes(data),mtime=0))
    report={'source':str(source),'source_sha256':digest(source),'output_sha256':digest(target),'build':str(build),'changes':changes,
            'all_other_state_bytes_unchanged':True,'texture_rows':144,'purpose':'graphics-refreshed checkpoint preview; not a fresh BIN load'}
    (output/'preview.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps({'output':str(target),'changes':sum(q['changed_bytes'] for q in changes)}))

if __name__=='__main__':main()
