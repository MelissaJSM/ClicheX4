"""Add the remaining detailed run poses to the frozen Riko clothing branch."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_riko_cloth as core
native=core.native
PARENT=D/'riko_restore/prepared_cloth_v1/PL01_U.ARC';PARENT_SHA='6ebb0239f27253bdd37b16c54b66a5b2044ba8191f41b8cc9f29cfbe15a440dc'
ART=D/'riko_cloth_inputs/run_registered_v3';REGSHA='ff6e7afafd93e5b107dccf02cd5aab93ae483111130fadfe15c903d08beede47'
OUT=D/'riko_restore/prepared_run_complete_v1';REFS=set(range(7,21))-{8,14}

def targets(arc):
    native.need(native.sha(arc)==PARENT_SHA,'Wrong source ARC')
    path=ART/'registration.json';native.need(native.sha(path.read_bytes())==REGSHA,'Registration changed')
    info=json.loads(path.read_text('utf8'));native.need(info['source_arc_sha256']==PARENT_SHA,'Registration parent changed');result={}
    for row in info['frames']:
        n=row['ref'];source=ROOT/row['source_native'];p=ART/f'b0_{n:03d}_indices.png'
        native.need(native.sha(source.read_bytes())==row['source_native_sha256'],'Native source changed')
        native.need(native.sha((source.parent.parent/'generated.png').read_bytes())==row['source_generated_sha256'],'Generated source changed')
        native.need(native.sha(p.read_bytes())==row['target_sha256'],'Target changed')
        a=np.array(Image.open(p));native.need(a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15,'Invalid indexed art')
        mask=np.array(Image.open(ART/f'b0_{n:03d}_protected_head.png'))>0;old=native.render(arc,0,0,n)[0]
        native.need(int(mask.sum())==309 and np.array_equal(a[mask],old[mask]),'Accepted head changed')
        native.need((0,n)not in result,'Duplicate reference');result[0,n]=a
    native.need({n for b,n in result}==REFS,'Run scope');return result

def cycle(arc,out):
    for name,row in(('normal',0),('black',13)):
        pal=struct.unpack_from('<16H',native.entry(arc,9),row*32)
        sheet=Image.new('RGB',(400*7,428*4),'#64717b');draw=ImageDraw.Draw(sheet)
        for i,n in enumerate(range(7,21)):
            for pair,(label,a)in enumerate([('before',arc),('new detailed',out)]):
                x=(i%7)*400;y=((i//7)*2+pair)*428;pic=native.rgba(native.render(a,0,0,n)[0],pal).crop((120,112,200,192)).resize((400,400),Image.Resampling.NEAREST);sheet.paste(pic,(x,y+28),pic);draw.text((x+5,y+5),f'{n} {label}',fill='white')
        sheet.save(OUT/(name+'_run_cycle.png'))
        for side in range(2):sheet.crop((0,side*856,2800,(side+1)*856)).save(OUT/f'{name}_run_cycle_{side}.png')

def main():
    core.PARENT_SHA=PARENT_SHA;core.PARENT=PARENT;core.KEYS={(0,n):(n,0,0)for n in sorted(REFS)};core.CACHE=D/'riko_restore/run_pack_cache_v1';core.OUT=OUT;core.get_targets=targets
    arc=PARENT.read_bytes();art=targets(arc);out,proof=core.build(arc,art);again,_=core.build(arc,art);native.need(out==again,'Reproduction differs')
    rejected=[]
    for case in('parent','missing_ref','head_pixel','out_of_palette'):
        aa=arc;tt={k:a.copy()for k,a in art.items()}
        if case=='parent':aa=bytes([arc[0]^1])+arc[1:]
        elif case=='missing_ref':del tt[0,20]
        elif case=='head_pixel':tt[0,7][140,150]^=1
        else:tt[0,18][160,160]=16
        try:core.build(aa,tt)
        except ValueError as exc:rejected.append({'case':case,'reason':str(exc)})
        else:raise ValueError('Invalid input accepted')
    OUT.mkdir(exist_ok=True);(OUT/'PL01_U.ARC').write_bytes(out);core.boards(arc,out);cycle(arc,out)
    proof['previous_55_references_exact']=True
    report={'source_arc':str(PARENT.relative_to(ROOT)),'source_arc_sha256':PARENT_SHA,'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':native.sha(out),'registration':str((ART/'registration.json').relative_to(ROOT)),'registration_sha256':REGSHA,'new_run_refs':sorted(REFS),'cumulative_authored_or_restored_refs':67,'verification':proof,'reproducible':True,'rejections':rejected,'game_changed':False,'runtime_verified':False}
    (OUT/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':native.sha(out),'verification':proof}))

if __name__=='__main__':main()
