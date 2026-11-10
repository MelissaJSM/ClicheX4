"""Continue the new airborne sequence; keep the 24-reference accepted candidate."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_run as core
base=core.base
SHA='1607afe355fb8fe62258d9002cd6157952c225b770d20bce27be1300fdf03534'
PARENT=D/'rin_extension/prepared_air_wall_v3/PL01_U.ARC'
ART=D/'rin_extension/air_continuation_registered_v2'
MANIFEST=D/'rin_extension/air_continuation_sources_v1.json'
OUT=D/'rin_extension/prepared_air_continuation_v1'
EXPECTED={22,23,24,25,26}

def targets():
    meta=json.loads(MANIFEST.read_text('utf8'));base.need(meta['parent_sha256']==SHA,'Wrong manifest parent')
    for row in meta['inputs']:base.need(base.sha((ROOT/row['path']).read_bytes())==row['sha256'],'Changed authored or registered input')
    result={}
    for n in sorted(EXPECTED):
        p=ART/f'b0_{22 if n==23 else n:03d}_indices.png';a=np.array(Image.open(p));base.need(a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15,'Bad native target');result[n]=a
    master=np.array(Image.open(ROOT/'work/sprite_style_unification_20261107/rin/locomotion01/native/b0_008_indices.png'));master[152,144]=0
    for n,dx,dy in [(22,6,-4),(24,5,-8),(25,5,-6),(26,5,-10)]:
        q=np.zeros_like(master,bool);q[140:148,144:168]=True;q[148:153,144:162]=True;q[153:154,147:157]=True;q=np.roll(np.roll(q,dx,axis=1),dy,axis=0)
        shifted=np.roll(np.roll(master,dx,axis=1),dy,axis=0);auth=np.array(Image.open(D/f'rin_extension/air_continuation01/native/b0_{n:03d}_indices.png'))
        base.need(np.array_equal(result[n][q],shifted[q]),'Semantic head/negative pixels changed');base.need(np.array_equal(result[n][~q],auth[~q]),'New body changed')
    return result

def main():
    arc=PARENT.read_bytes();base.need(base.sha(arc)==SHA,'Wrong parent ARC')
    base.need(np.array_equal(base.render(arc,0,0,22)[0],base.render(arc,0,0,23)[0]),'Original22/23 no longer exact')
    for n in (22,24,25,26):base.need(np.array_equal(base.render(arc,0,0,n)[0],np.array(Image.open(D/f'rin_extension/air_continuation01/b0_{n:03d}_indices.png'))),'Pose source differs from current parent')
    base.SHA=SHA;core.EXPECTED=EXPECTED;core.get_targets=targets;core.CACHE=D/'rin_extension/air_continuation_pack_cache_v1'
    tt=targets();out,proof=core.build(arc,tt);again,_=core.build(arc,tt);base.need(out==again,'Reproduction mismatch')
    rejects=[]
    for case in ['wrong_source','missing_ref','changed_pixel','out_of_palette']:
        aa=arc;bb={n:a.copy()for n,a in tt.items()}
        if case=='wrong_source':aa=bytes([aa[0]^1])+aa[1:]
        elif case=='missing_ref':del bb[23]
        elif case=='changed_pixel':bb[22][150,150]^=1
        else:bb[24][150,150]=16
        try:core.build(aa,bb)
        except ValueError as exc:rejects.append({'case':case,'error':str(exc)})
        else:raise ValueError('Unsafe input accepted')
    proof.pop('head_overrides',None);proof['same_angle_new_head_master']=True;proof['head_negative_space_exact']=True;proof['previous_24_references_exact']=True
    OUT.mkdir(exist_ok=True);(OUT/'PL01_U.ARC').write_bytes(out)
    for label,row in [('normal',0),('black',13)]:
        pal=struct.unpack_from('<16H',base.entry(arc,9),row*32)
        for offset in range(0,5,3):
            ns=sorted(EXPECTED)[offset:offset+3];sheet=Image.new('RGB',(1200,428*len(ns)),'#64717b');draw=ImageDraw.Draw(sheet)
            for iy,n in enumerate(ns):
                for ix,(title,a)in enumerate([('idle',base.render(arc,0,0,147)[0]),('previous',base.render(arc,0,0,n)[0]),('packed new',base.render(out,0,0,n)[0])]):
                    pic=base.rgba(a,pal).crop((120,120,200,200)).resize((400,400),Image.Resampling.NEAREST);sheet.paste(pic,(ix*400,iy*428+28),pic);draw.text((ix*400+4,iy*428+5),f'{n} {title}',fill='white')
            sheet.save(OUT/f'{label}_readback_{offset//3:02d}.png')
    report={'source_arc':str(PARENT.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':base.sha(out),'references':sorted(EXPECTED),'cumulative_refs':29,'art_manifest':str(MANIFEST.relative_to(ROOT)),'art_manifest_sha256':base.sha(MANIFEST.read_bytes()),'verification':proof,'reproducible':True,'rejections':rejects,'game_changed':False,'runtime_verified':False}
    (OUT/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':base.sha(out),'verification':proof}))

if __name__=='__main__':main()
