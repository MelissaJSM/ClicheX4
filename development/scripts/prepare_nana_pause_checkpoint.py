"""현재 진행의 작업 사본에서 확인된 일시정지 그래픽만 갱신한다."""
import argparse,gzip,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_pause import PARENT,verify,entry
from scripts.project import digest
from PIL import Image

def main(source,build,output):
    source,build,output=(p.resolve() for p in (source,build,output))
    if not source.is_relative_to(ROOT/'work/ver_rin_nana/checkpoints') or not output.is_relative_to(ROOT/'work/ver_rin_nana/checkpoints') or not build.is_relative_to(ROOT/'out/ver_rin_nana'):raise ValueError('Unexpected checkpoint paths')
    m=json.loads((build/'manifest.json').read_text('utf8'));old=(PARENT/'modified.arc').read_bytes();new=(build/'modified.arc').read_bytes()
    if digest(build/'rin_nana.bin')!=m['modified_bin']['sha256'] or digest(build/'modified.arc')!=m['modified_archive_sha256']:raise ValueError('Build binding differs')
    verify(old,new,Image.open(build/'pause/portrait.png').tobytes())
    state=gzip.decompress(source.read_bytes());vram=2569183
    if len(state)!=4254418:raise ValueError('Unknown state layout')
    data=bytearray(state);allowed=bytearray(len(state));changes=[]
    def put(pos,before,after,label):
        if len(before)!=len(after) or state[pos:pos+len(before)]!=before:raise ValueError('Unexpected checkpoint '+label)
        data[pos:pos+len(after)]=after;allowed[pos:pos+len(after)]=bytes([1])*len(after)
        changes.append({'label':label,'offset':pos,'size':len(after),'changed_bytes':sum(a!=b for a,b in zip(before,after))})
    g,ng=entry(old,0x10007),entry(new,0x10007);row=max(range(256),key=lambda r:len(set(g[r*128:(r+1)*128])))
    sig=g[row*128:(row+1)*128];cursor=vram;bases=[]
    while (cursor:=state.find(sig,cursor,vram+1048576))>=0:
        base=cursor-row*2048
        if vram<=base and base+255*2048+128<=vram+1048576 and all(state[base+r*2048:base+r*2048+128]==g[r*128:(r+1)*128] for r in range(256)):bases.append(base)
        cursor+=1
    if len(bases)!=1:raise ValueError('Menu VRAM atlas is not uniquely present')
    for r in range(256):
        if g[r*128:(r+1)*128]!=ng[r*128:(r+1)*128]:put(bases[0]+r*2048,g[r*128:(r+1)*128],ng[r*128:(r+1)*128],'menu texture row '+str(r))
    palette,npal=entry(old,0x11),entry(new,0x11);pos=state.find(palette)
    if pos<0 or state.find(palette,pos+1)>=0 or pos+len(palette)>vram:raise ValueError('Menu palette RAM is not unique')
    put(pos,palette,npal,'menu palette RAM')
    before,after=palette[320:352],npal[320:352];pos=state.find(before,vram,vram+1048576)
    if pos<0 or state.find(before,pos+1,vram+1048576)>=0:raise ValueError('Menu portrait VRAM palette is not unique')
    put(pos,before,after,'menu portrait VRAM palette')
    if any(a!=b and not ok for a,b,ok in zip(state,data,allowed)):raise ValueError('Non-graphic state changed')
    output.mkdir(exist_ok=False);target=output/source.name;target.write_bytes(gzip.compress(bytes(data),mtime=0))
    report={'source':source.relative_to(ROOT).as_posix(),'source_sha256':digest(source),'output_sha256':digest(target),'build':build.relative_to(ROOT).as_posix(),
        'changes':changes,'changed_bytes':sum(q['changed_bytes'] for q in changes),'other_state_bytes_exact':True,
        'vram_offset':vram,'atlas_xy':[(bases[0]-vram)%2048//2,(bases[0]-vram)//2048],
        'purpose':'graphics-only checkpoint preview; not a fresh disk load of portrait'}
    (output/'preview.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps({'output':str(target),'changed_bytes':report['changed_bytes']}))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('source','build','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();main(a.source,a.build,a.output)
