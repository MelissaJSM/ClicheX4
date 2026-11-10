"""Use a preserved Hunter HQ checkpoint for a graphics-only expression preview."""
import argparse,gzip,json
from pathlib import Path
from scripts.prepare_riko_ui import entry
from scripts.project import digest

ROOT=Path(__file__).resolve().parents[1]


def prepare(source,before,after,output):
    source,before,after,output=(p.resolve() for p in (source,before,after,output))
    if not all(p.is_relative_to(ROOT/'work/ver_buki_riko') for p in (source,before,after,output)):
        raise ValueError('Expected local work paths')
    state=gzip.decompress(source.read_bytes())
    if len(state)!=4254418:raise ValueError('Unexpected ePSXe state layout')
    oldarc,newarc=before.read_bytes(),after.read_bytes()
    old,new=entry(oldarc,0x10102)[63488:81920],entry(newarc,0x10102)[63488:81920]
    parts,newparts=entry(oldarc,10),entry(newarc,10)
    pos=state.find(parts)
    if pos<0 or state.find(parts,pos+1)>=0 or len(parts)!=len(newparts):raise ValueError('Parts not uniquely located in checkpoint')
    data=bytearray(state);data[pos:pos+len(parts)]=newparts;allowed=set(range(pos,pos+len(parts)))
    vram=2569183;rows=[]
    # Verified in the saved US HQ scene: source row0 at x512/y144;
    # source row32 begins the next 64-word upload strip at x576/y0.
    for row in range(144):
        x,y=(512,144+row) if row<32 else (576,row-32)
        start=vram+y*2048+x*2
        if state[start:start+128]!=old[row*128:(row+1)*128]:raise ValueError('Unexpected Hunter HQ VRAM placement')
        data[start:start+128]=new[row*128:(row+1)*128];allowed.update(range(start,start+128))
        rows.append([x,y])
    changed=[i for i,(a,b) in enumerate(zip(state,data)) if a!=b]
    if not changed or any(i not in allowed for i in changed):raise ValueError('Preview escaped graphics-only ranges')
    output.parent.mkdir(exist_ok=False)
    with output.open('xb') as f:f.write(gzip.compress(bytes(data),mtime=0))
    report={'source':str(source),'source_sha256':digest(source),'output':str(output),'output_sha256':digest(output),
        'parts_state_offset':pos,'parts_changed_bytes':sum(a!=b for a,b in zip(parts,newparts)),
        'vram_changed_bytes':len(changed)-sum(a!=b for a,b in zip(parts,newparts)),
        'texture_rows_verified':len(rows),'all_other_state_bytes_unchanged':True,
        'purpose':'Graphics-only checkpoint preview, not fresh BIN resource loading proof'}
    (output.parent/'preview.local.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('source','before','after','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();prepare(a.source,a.before,a.after,a.output)
