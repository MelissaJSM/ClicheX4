"""Register the four authored dash poses and their proven identical aliases."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_run as core
base=core.base
SHA='1c7a4e24b7dc83af5a26433af95a15bf94319bb4fd3b315d82c2bbcfab68d08e'
PARENT=D/'rin_extension/prepared_air_continuation_v1/PL01_U.ARC'
ART=D/'rin_extension/dash_continuation01/native'
MANIFEST=D/'rin_extension/dash_sources_v1.json'
OUT=D/'rin_extension/prepared_dash_v2'
MAP={44:44,46:46,47:46,48:46,50:50,51:51,52:51}
EXPECTED=set(MAP)
ORIGINAL_REPACK=core.repack_variable
JOINT_REPORT=[]

def targets():
    meta=json.loads(MANIFEST.read_text('utf8'));base.need(meta['parent_sha256']==SHA,'Wrong manifest parent')
    for row in meta['inputs']:
        base.need(base.sha((ROOT/row['path']).read_bytes())==row['sha256'],'Changed authored or registered input')
    result={}
    for n,s in MAP.items():
        a=np.array(Image.open(ART/f'b0_{s:03d}_indices.png'))
        base.need(a.shape==(384,384) and a.dtype==np.uint8 and a.max()<=15,'Bad native target');result[n]=a
    return result

def joint_repack(g,replacements,counts):
    """Reuse only the two existing alias groups after exact joint readback."""
    arc=PARENT.read_bytes();base.need(base.sha(arc)==SHA,'Wrong joint source')
    c=base.entry(arc,3);bank=base.graphics_bank(g,0);want=targets();rr=dict(replacements)
    for group in [(46,47,48),(51,52)]:
        first=bank['frames'][group[0]];edits=[]
        raw=base.decode_stream(g,first['offset'],first['limit'],first['tile_count']*128).data
        for n in group:
            f=bank['frames'][n];base.need(f['offset']==first['offset'],'Joint group is not original alias')
            base.need(counts[n]==f['tile_count'],'Joint tile count changed')
            cp=base.composition_frame(c,0,n);_,size,bb,_=base.compose_indices(raw,f['tile_count'],cp)
            crop=want[n][160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]
            # These two groups have no sampling-window changes. Prove that the
            # one-frame result already has the requested display under old parts.
            actual,sz,_,_=base.compose_indices(rr[n],counts[n],cp)
            base.need(actual==crop.tobytes() and sz==size,'Joint group has different windows')
            edits.append((cp,crop.tobytes(),size))
        joint=base.packer.edit_visible_set(raw,first['tile_count'],edits)
        for n in group:rr[n]=joint
        JOINT_REPORT.append({'refs':list(group),'original_alias_preserved':True,'all_targets_exact':True,'joint_raw_sha256':base.sha(joint)})
    return ORIGINAL_REPACK(g,rr,counts)

def main():
    arc=PARENT.read_bytes();base.need(base.sha(arc)==SHA,'Wrong parent ARC')
    for n,s in MAP.items():
        base.need(np.array_equal(base.render(arc,0,0,n)[0],base.render(arc,0,0,s)[0]),'Original alias differs')
    for n in set(MAP.values()):
        old=np.array(Image.open(D/f'rin_extension/dash_continuation01/b0_{n:03d}_indices.png'))
        base.need(np.array_equal(base.render(arc,0,0,n)[0],old),'Pose input is stale')
    base.SHA=SHA;core.EXPECTED=EXPECTED;core.get_targets=targets;core.CACHE=D/'rin_extension/dash_pack_cache_v1';core.repack_variable=joint_repack
    tt=targets();out,proof=core.build(arc,tt);again,_=core.build(arc,tt);base.need(out==again,'Reproduction mismatch')
    rejects=[]
    for case in ['wrong_source','missing_ref','changed_pixel','out_of_palette']:
        aa=arc;bb={n:a.copy()for n,a in tt.items()}
        if case=='wrong_source':aa=bytes([aa[0]^1])+aa[1:]
        elif case=='missing_ref':del bb[47]
        elif case=='changed_pixel':bb[44][150,150]^=1
        else:bb[46][150,150]=16
        try:core.build(aa,bb)
        except ValueError as exc:rejects.append({'case':case,'error':str(exc)})
        else:raise ValueError('Unsafe input accepted')
    proof['previous_29_references_exact']=True;proof['old_head_override_pixels']=0
    proof['joint_alias_groups']=JOINT_REPORT[:2]
    OUT.mkdir(exist_ok=True);(OUT/'PL01_U.ARC').write_bytes(out)
    for label,row in [('normal',0),('black',13)]:
        pal=struct.unpack_from('<16H',base.entry(arc,9),row*32)
        for offset in range(0,len(EXPECTED),3):
            ns=sorted(EXPECTED)[offset:offset+3];sheet=Image.new('RGB',(1200,428*len(ns)),'#64717b');draw=ImageDraw.Draw(sheet)
            for iy,n in enumerate(ns):
                for ix,(title,a)in enumerate([('idle',base.render(arc,0,0,147)[0]),('previous',base.render(arc,0,0,n)[0]),('packed new',base.render(out,0,0,n)[0])]):
                    pic=base.rgba(a,pal).crop((120,120,200,200)).resize((400,400),Image.Resampling.NEAREST)
                    sheet.paste(pic,(ix*400,iy*428+28),pic);draw.text((ix*400+4,iy*428+5),f'{n} {title}',fill='white')
            sheet.save(OUT/f'{label}_readback_{offset//3:02d}.png')
    report={'source_arc':str(PARENT.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':base.sha(out),'references':sorted(EXPECTED),'cumulative_refs':36,'art_manifest':str(MANIFEST.relative_to(ROOT)),'art_manifest_sha256':base.sha(MANIFEST.read_bytes()),'verification':proof,'reproducible':True,'rejections':rejects,'game_changed':False,'runtime_verified':False,'visual_acceptance_required':True}
    (OUT/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':base.sha(out),'verification':proof}))

if __name__=='__main__':main()
