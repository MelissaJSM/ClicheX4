"""원본/기존/수정 특수 기술의 월드 좌표와 변경 범위를 비교한다. 실행 영상은 아니다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_rin_idle import entry,sha
from scripts.assemble_rin_special_frames import world
from scripts.prepare_rin_specials import GROUPS
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch
from src.rin_registration import contact_span

def render(arc,bi,n):
    g=entry(arc,2)[1];parts=entry(arc,3)[1];f=graphics_bank(g,bi)['frames'][n]
    raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
    c=composition_frame(parts,0 if bi==0 else 5,n)
    pic=compose_launch(raw,f['tile_count'],c)
    return world(pic[:2],pic[2]),c

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,required=True);ap.add_argument('--after',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve()
    if not out.is_relative_to(ROOT/'work/ver_rin_nana'):raise ValueError('Unexpected report output')
    out.mkdir(exist_ok=True,parents=True)
    arcs={'original':(ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z/original.arc').read_bytes(),'before':a.before.read_bytes()}
    if a.after:arcs['after']=a.after.read_bytes()
    report={'archives':{k:sha(v) for k,v in arcs.items()},'groups':{},'runtime_video':False}
    for group in ('thrust','dashslash'):
        bi,ids=GROUPS[group];ids=sorted(ids);metrics={};cols=len(arcs)
        sheet=Image.new('RGB',(cols*288,len(ids)*240),(34,37,47));d=ImageDraw.Draw(sheet)
        for i,n in enumerate(ids):
            metrics[n]={}
            for j,(label,arc) in enumerate(arcs.items()):
                w,c=render(arc,bi,n);words=struct.unpack_from('<16H',entry(arc,9)[1]);pal=np.array([[(v>>s&31)*255//31 for s in (0,5,10)]+[255 if k else 0] for k,v in enumerate(words)],np.uint8)
                im=Image.fromarray(pal[w[80:152,80:176]]).resize((288,216),Image.Resampling.NEAREST)
                x=j*288;y=i*240;d.line((x+144,y+24,x+144,y+239),fill=(64,90,110));d.line((x,y+239,x+287,y+239),fill=(64,90,110));sheet.paste(im,(x,y+24),im)
                r=contact_span(w);metrics[n][label]=r;d.text((x+4,y+4),f'{label} {bi}:{n} contact X{r["center_x"]} Y{r["floor_y"]}',fill='white')
        sheet.save(out/(group+'_comparison.png'));report['groups'][group]=metrics
    if a.after:
        changed=[];preserved=0
        for bi in (0,1):
            ag=entry(arcs['before'],2)[1];bg=entry(arcs['after'],2)[1]
            for af,bf in zip(graphics_bank(ag,bi)['frames'],graphics_bank(bg,bi)['frames']):
                n=af['index']
                if bi==1 and 42<=n<=49:
                    ar=decode_stream(ag,af['offset'],af['limit'],af['tile_count']*128).data;br=decode_stream(bg,bf['offset'],bf['limit'],bf['tile_count']*128).data
                    if ar!=br or composition_frame(entry(arcs['before'],3)[1],5,n)!=composition_frame(entry(arcs['after'],3)[1],5,n):raise ValueError('Unresolved original reference changed')
                    preserved+=1;continue
                aw,ac=render(arcs['before'],bi,n);bw,bc=render(arcs['after'],bi,n)
                if not np.array_equal(aw,bw) or ac!=bc:changed.append([bi,n])
                else:preserved+=1
        allowed={(bi,n) for key in ('thrust','dashslash') for bi,ids in [GROUPS[key]] for n in ids}
        if any(tuple(q) not in allowed for q in changed):raise ValueError(f'Unrelated display changed {changed}')
        if entry(arcs['before'],0x10206)[1]!=entry(arcs['after'],0x10206)[1]:raise ValueError('Static burst/effects changed')
        if entry(arcs['before'],9)[1]!=entry(arcs['after'],9)[1]:raise ValueError('Palette changed')
        report['display_delta']={'changed':changed,'other_compressed_refs_unchanged':preserved,'static_texture_and_palettes_exact':True}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n','utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
