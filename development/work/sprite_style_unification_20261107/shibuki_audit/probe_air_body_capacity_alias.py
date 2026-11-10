"""11개 새 공중 몸체의 pinned head/arm 레코드 용량 시험. ARC 파일을 쓰지 않음.

사격짝은 원본 그대로 두고 임시 압축스트림 분리까지 시험한다. 최종 사격 미술/패킹 증거가 아니다.
"""
from pathlib import Path
import sys,json,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from inspect_air_layers import REFS,P
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_ultimate_production import records,repack_parts
from scripts.prepare_shibuki_armor_remaining import pack_many_patterns
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_riko_ui import entry,replace_entry
from src.psx_player import indexed_atlas,compose_indices,composition_frame,decode_stream,bank_offsets
from native_pose_pack import sha,need,write,crop
from probe_air_record_alias import decode_templates,solve

def candidates(c,b,target):
    yy,xx=np.nonzero(target)
    if not len(xx):return []
    box=(int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160))
    choices={records(c,b,n)[i:i+4] for n in range(composition_frame(c,b,0)['bank_frame_count'])for i in range(0,len(records(c,b,n)),4)}
    result=[]
    for r in choices:
        fl,t,x,y=struct.unpack('<BBbb',r)
        if fl==0 and t not in(0,16) and t<32 and x<=box[0]and y<=box[1]and x+16>=box[2]and y+16>=box[3]:result.append(r)
    return sorted(result,key=lambda r:(r[1],r))

def put(raw,r,target):
    fl,t,x,y=struct.unpack('<BBbb',r);need(fl==0,'Unverified pinned flip')
    atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256).copy()
    patch=target[y+160:y+176,x+160:x+176];need(np.count_nonzero(patch)==np.count_nonzero(target),'Pinned rectangle clips target')
    atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]=patch
    return bytes((atlas[:,0::2]|(atlas[:,1::2]<<4)).ravel())

def main():
    out=H/'air_body_capacity03';need(not out.exists(),'Fresh output required');out.mkdir();a=Archive(P.read_bytes());d=H/'air_body_layers01';changes={b:{}for b in(0,5,6,7,8)};raws={};counts={};expected={};reports=[];failures=[]
    templates=decode_templates(a,7,max_parts=4)
    for n in sorted(REFS):
        layers={b:np.array(Image.open(d/f'{n:03}_bank{b}_indices.png'))for b in changes}
        head=candidates(a.c,5,layers[5]);points=set(map(int,np.flatnonzero(layers[7])));pair=None
        for _,length,p,recs,cov in templates:
            if not points<=cov:continue
            armtiles={t for fl,t,x,y in recs if t};h=next((v for v in head if v[1]not in armtiles),None)
            if h is None:continue
            solution=solve(layers[7],recs)
            if solution is None:continue
            pair=h,a.c[p:p+length*4],solution[0],armtiles;break
        bs=(0,6,8)
        if pair is None:
            need(head,'No head template');h=head[0];r=None;raw=put(bytes(4096),h,layers[5]);pool=set(range(1,32))-{h[1]};bs=(0,6,7,8)
        else:
            h,r,raw,armtiles=pair;raw=put(raw,h,layers[5]);pool=set(range(1,32))-{h[1]}-armtiles
        try:raw,parts=pack_many_patterns(raw,32,[crop(layers[b])for b in bs],pool,[24]*len(bs))
        except ValueError as ex:failures.append({'ref':n,'reason':str(ex)});continue
        changes[5][n]=h
        if r is not None:changes[7][n]=r
        for b,rr in zip(bs,parts):changes[b][n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in rr)
        raws[n]=raw;counts[n]=32
        oldf=a.banks[0]['frames'][n]
        aliases=[f for f in a.banks[0]['frames']if f['offset']==oldf['offset']]
        for f in aliases:
            if f['index']==n:continue
            raws[f['index']]=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;counts[f['index']]=f['tile_count']
        expected[n]=layers;reports.append({'ref':n,'head_record_hex':h.hex(),'arm_record_hex':changes[7][n].hex(),'arm_record_reused':r is not None,'parts':{str(b):len(changes[b][n])//4 for b in changes},'nonshoot_source_art_exact':True,'old_shot_temporarily_preserved':True})
    result={'analysis_only':True,'parent_sha256':sha(P.read_bytes()),'reports':reports,'failures':failures,'resource_written':False,'shot_art_and_shared_stream_final_still_pending':True}
    if not failures:
        nc=a.c;slack={}
        try:
            for b,rr in changes.items():nc,slack[b]=repack_parts(nc,b,rr)
            ng,gr=repack_variable(a.g,raws,counts);data=replace_entry(replace_entry(a.data,2,ng),3,nc);readback=Archive(data)
            for n,ll in expected.items():
                for b,ar in ll.items():need(np.array_equal(readback.layer(n,b)[0],ar),'Actual native target differs')
            result.update(passed=True,part_slack=slack,graphics=gr,native_layers_exact=len(expected)*5,no_bank_boundary_change=bank_offsets(nc)==bank_offsets(a.c),trial_sha256=sha(data),arc_deliberately_not_saved=True)
        except ValueError as ex:result.update(passed=False,capacity_failure=str(ex),completed_part_slack=slack)
    else:result['passed']=False
    write(out/'report.json',result);print(json.dumps(result))
if __name__=='__main__':main()
