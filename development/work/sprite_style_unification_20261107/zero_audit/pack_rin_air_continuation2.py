"""Add the four raised-arm air poses and their two exact display aliases."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_run as core
base=core.base
SHA='713d4e7eae5475d8c9a3bce71fac290af9b00e01a801131745ca09dac3852512'
PARENT=D/'rin_extension/prepared_dash_v2/PL01_U.ARC'
ART=D/'rin_extension/air_continuation02/native'
MANIFEST=D/'rin_extension/air_continuation2_sources_v1.json'
OUT=D/'rin_extension/prepared_air_continuation2_v2'
MAP={28:28,29:29,30:29,31:31,32:31,33:33}
EXPECTED=set(MAP);ORIGINAL_REPACK=core.repack_variable;JOINT_REPORT=[]

def targets():
    meta=json.loads(MANIFEST.read_text('utf8'));base.need(meta['parent_sha256']==SHA,'Wrong manifest parent')
    for row in meta['inputs']:base.need(base.sha((ROOT/row['path']).read_bytes())==row['sha256'],'Changed authored or registered input')
    result={}
    for n,s in MAP.items():
        a=np.array(Image.open(ART/f'b0_{s:03d}_indices.png'));base.need(a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15,'Bad native target');result[n]=a
    return result

def joint_repack(g,replacements,counts):
    c=base.entry(PARENT.read_bytes(),3);bank=base.graphics_bank(g,0);want=targets();rr=dict(replacements)
    for group in[(29,30),(31,32)]:
        first=bank['frames'][group[0]]
        if any(bank['frames'][n]['offset']!=first['offset']or counts[n]!=first['tile_count']for n in group):continue
        raw=base.decode_stream(g,first['offset'],first['limit'],first['tile_count']*128).data;edits=[];local=bytearray(c)
        # Use the exact updated windows selected by one_frame, including an
        # unused old lower tile relocated to the new upper sleeve in29/30.
        for n in group:
            original=base.composition_frame(c,0,n)
            _,ct,rec,_=core.one_frame(c,n,raw,first['tile_count'],want[n])
            base.need(ct==counts[n] and len(rec)==len(original['parts'])*4,'Joint part/count change')
            for i,p in enumerate(original['parts']):local[p['record_offset']:p['record_offset']+4]=rec[i*4:i*4+4]
        for n in group:
            cp=base.composition_frame(local,0,n);_,size,bb,_=base.compose_indices(raw,first['tile_count'],cp)
            crop=want[n][160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]
            if base.compose_indices(rr[n],counts[n],cp)[:2]!=(crop.tobytes(),size):break
            edits.append((cp,crop.tobytes(),size))
        if len(edits)!=len(group):continue
        try:joint=base.packer.edit_visible_set(raw,first['tile_count'],edits)
        except ValueError:continue
        for n in group:rr[n]=joint
        JOINT_REPORT.append({'refs':list(group),'original_alias_preserved':True,'all_targets_exact':True,'joint_raw_sha256':base.sha(joint)})
    return ORIGINAL_REPACK(g,rr,counts)

def main():
    arc=PARENT.read_bytes();base.need(base.sha(arc)==SHA,'Wrong parent ARC')
    for n,s in MAP.items():base.need(np.array_equal(base.render(arc,0,0,n)[0],base.render(arc,0,0,s)[0]),'Original alias differs')
    for n in set(MAP.values()):base.need(np.array_equal(base.render(arc,0,0,n)[0],np.array(Image.open(D/f'rin_extension/air_continuation02/b0_{n:03d}_indices.png'))),'Pose input is stale')
    base.SHA=SHA;core.EXPECTED=EXPECTED;core.get_targets=targets;core.CACHE=D/'rin_extension/air_continuation2_pack_cache_v1';core.repack_variable=joint_repack
    tt=targets();out,proof=core.build(arc,tt);again,_=core.build(arc,tt);base.need(out==again,'Reproduction mismatch');rejects=[]
    for case in['wrong_source','missing_ref','changed_pixel','out_of_palette']:
        aa=arc;bb={n:a.copy()for n,a in tt.items()}
        if case=='wrong_source':aa=bytes([aa[0]^1])+aa[1:]
        elif case=='missing_ref':del bb[30]
        elif case=='changed_pixel':bb[28][150,150]^=1
        else:bb[29][150,150]=16
        try:core.build(aa,bb)
        except ValueError as exc:rejects.append({'case':case,'error':str(exc)})
        else:raise ValueError('Unsafe input accepted')
    proof['previous_36_references_exact']=True;proof['old_head_override_pixels']=0;proof['joint_alias_groups']=JOINT_REPORT[:len(JOINT_REPORT)//2]
    OUT.mkdir(exist_ok=True);(OUT/'PL01_U.ARC').write_bytes(out)
    for label,row in[('normal',0),('black',13)]:
        pal=struct.unpack_from('<16H',base.entry(arc,9),row*32)
        for offset in range(0,len(EXPECTED),3):
            ns=sorted(EXPECTED)[offset:offset+3];sheet=Image.new('RGB',(1200,508*len(ns)),'#64717b');draw=ImageDraw.Draw(sheet)
            for iy,n in enumerate(ns):
                for ix,(title,a)in enumerate([('idle',base.render(arc,0,0,147)[0]),('previous',base.render(arc,0,0,n)[0]),('packed new',base.render(out,0,0,n)[0])]):
                    pic=base.rgba(a,pal).crop((120,104,200,200)).resize((400,480),Image.Resampling.NEAREST)
                    base.need(np.count_nonzero(np.array(pic.getchannel('A')))==np.count_nonzero(a)*25,'Preview clips pose')
                    sheet.paste(pic,(ix*400,iy*508+28),pic);draw.text((ix*400+4,iy*508+5),f'{n} {title}',fill='white')
            sheet.save(OUT/f'{label}_readback_{offset//3:02d}.png')
    report={'source_arc':str(PARENT.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':base.sha(out),'references':sorted(EXPECTED),'cumulative_refs':42,'art_manifest':str(MANIFEST.relative_to(ROOT)),'art_manifest_sha256':base.sha(MANIFEST.read_bytes()),'verification':proof,'reproducible':True,'rejections':rejects,'game_changed':False,'runtime_verified':False,'visual_acceptance_required':True}
    (OUT/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':base.sha(out),'verification':proof}))

if __name__=='__main__':main()
