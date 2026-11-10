"""Native readback candidate for four detailed air/wall keys plus exact alias40."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_run as core
base=core.base
PARENT=D/'rin_extension/prepared_run_v1/PL01_U.ARC'
SHA='61ce28a47ad537a9d9d6661af764fd97461d6584272a42e20f76c79049263078'
ART=D/'rin_extension/air_wall_head_candidate_v4'
OUT=D/'rin_extension/prepared_air_wall_v3'
MANIFEST=D/'rin_extension/air_wall_sources_v3.json'
EXPECTED={21,27,35,39,40}

def targets():
    meta=json.loads(MANIFEST.read_text('utf8'));base.need(meta['parent_sha256']==SHA,'Wrong manifest parent')
    for row in meta['inputs']:
        base.need(base.sha((ROOT/row['path']).read_bytes())==row['sha256'],'Changed source or registration input')
    result={}
    for n in sorted(EXPECTED):
        ref=39 if n==40 else n;p=ART/f'b0_{ref:03d}_indices.png';a=np.array(Image.open(p))
        base.need(a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15,'Invalid native image');result[n]=a
    master=np.array(Image.open(ROOT/'work/sprite_style_unification_20261107/rin/locomotion01/native/b0_008_indices.png'))
    master[152,144]=0 # explicit source glove exclusion from head-only master
    for n,dx,dy in [(21,4,-4),(27,8,-10),(35,8,-7),(39,-2,1)]:
        original=np.array(Image.open(D/f'rin_extension/air_wall01/native/b0_{n:03d}_indices.png'))
        roi=np.zeros_like(master,bool);roi[140:148,142:168]=True;roi[148:153,144:162]=True;roi[153:154,147:157]=True
        roi=np.roll(np.roll(roi,dx,axis=1),dy,axis=0)
        foreground=np.zeros_like(master,bool)
        if n==27:foreground[140:147,138:155]=True
        if n==35:foreground[134:145,138:154]=True
        if n==39:foreground[138:146,158:178]=True
        foreground &= original>0
        translated=np.roll(np.roll(master,dx,axis=1),dy,axis=0)
        base.need(np.array_equal(result[n][roi&~foreground],translated[roi&~foreground]),'Detailed head or internal negative space changed')
        base.need(np.array_equal(result[n][foreground],original[foreground]),'Foreground wrist/hand changed')
        base.need(np.array_equal(result[n][~roi],original[~roi]),'New body outside head changed')
    return result

def main():
    arc=PARENT.read_bytes();base.need(base.sha(arc)==SHA,'Wrong source ARC')
    base.need(np.array_equal(base.render(arc,0,0,39)[0],base.render(arc,0,0,40)[0]),'Alias39/40 not exact')
    base.SHA=SHA;core.EXPECTED=EXPECTED;core.get_targets=targets;core.CACHE=D/'rin_extension/air_wall_pack_cache_v1'
    tt=targets();out,proof=core.build(arc,tt);again,_=core.build(arc,tt);base.need(out==again,'Reproduction mismatch')
    rejects=[]
    for case in ['wrong_source','missing_ref','changed_pixel','invalid_index']:
        aa=arc;bb={n:a.copy()for n,a in tt.items()}
        if case=='wrong_source':aa=bytes([aa[0]^1])+aa[1:]
        elif case=='missing_ref':del bb[40]
        elif case=='changed_pixel':bb[21][150,150]^=1
        else:bb[27][150,150]=16
        try:core.build(aa,bb)
        except ValueError as exc:rejects.append({'case':case,'error':str(exc)})
        else:raise ValueError('Unsafe input accepted')
    # Reuse only the accepted, same-angle new head. Keep its negative space and
    # inspect foreground hands separately; this is not an old coarse-head copy.
    proof.pop('head_overrides',None)
    proof['same_angle_authored_head_master']='rin/locomotion01/native/b0_008_indices.png'
    proof['same_angle_master_with_negative_space_and_foreground_hand_protection']=True
    proof['previous_19_references_exact']=True
    OUT.mkdir(exist_ok=True);(OUT/'PL01_U.ARC').write_bytes(out)
    for name,row in [('normal',0),('black',13)]:
        pal=struct.unpack_from('<16H',base.entry(arc,9),row*32)
        for offset in range(0,5,3):
            ns=sorted(EXPECTED)[offset:offset+3];sheet=Image.new('RGB',(1200,428*len(ns)),'#64717b');draw=ImageDraw.Draw(sheet)
            for iy,n in enumerate(ns):
                for ix,(label,a)in enumerate([('idle',base.render(arc,0,0,147)[0]),('previous',base.render(arc,0,0,n)[0]),('packed detailed',base.render(out,0,0,n)[0])]):
                    pic=base.rgba(a,pal).crop((120,120,200,200)).resize((400,400),Image.Resampling.NEAREST);sheet.paste(pic,(ix*400,iy*428+28),pic);draw.text((ix*400+4,iy*428+5),f'{n} {label}',fill='white')
            sheet.save(OUT/f'{name}_readback_{offset//3:02d}.png')
    report={'source_arc':str(PARENT.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),
            'after_sha256':base.sha(out),'references':sorted(EXPECTED),'cumulative_refs':24,'art_manifest':str(MANIFEST.relative_to(ROOT)),
            'art_manifest_sha256':base.sha(MANIFEST.read_bytes()),'verification':proof,'reproducible':True,'rejections':rejects,'game_changed':False,'runtime_verified':False}
    (OUT/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'sha256':base.sha(out),'verification':proof}))

if __name__=='__main__':main()
