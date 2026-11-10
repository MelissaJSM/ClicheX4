"""새 사다리14참조를 동결 벽/정면/저체력 자원 위에 누적 무손실 패킹한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE_SHA,sha,need,write
from probe_ladder_capacity import mirror
from register_ladder_parts import compose
from native_pose_pack import shared_components
from scripts.prepare_shibuki_armor_remaining import pack_many_patterns
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import composition_frame,bank_offsets
import pack_lowhp_return as backend

PARENT_SHA='db508292c2746b5c4a12e60e9cf28f5ebe558e7998788c3d1d5440a4f8fd481a'
BASELINE_SHA='b6a4f2a5a321e8c37575e6593c3b86f396151c16a16690e16054c86e75f3fd59'
SELECTION_SHA='80da6cbfa706a3fce1f79133390ed12b719940046e7670eebda81977d1e2325b'
SELECTED=set(range(143,156))|{183}
ALIASES={145:(144,-1),147:(146,0),148:(149,0),152:(151,0)}

def targets():
    aliases=ALIASES;result={}
    for n in sorted(SELECTED):
        key,delta=aliases.get(n,(n,None));folder=H/('ladder_shots_registered01'if n in(150,155)else'ladder_parts04')
        result[n]={b:np.array(Image.open(folder/f'{key:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)}
        if delta is not None:result[n]={b:mirror(v,delta)for b,v in result[n].items()}
    return result

def mirror_safe_pack(images):
    usable=set(range(1,32))-{16}
    try:
        raw,parts=pack_many_patterns(bytes(4096),32,images,usable,[24]*len(images))
        return raw,parts,'canonical_mirror_whole_patterns'
    except ValueError as initial:
        components,mapping=shared_components(images)
        try:raw,rr=pack_many_patterns(bytes(4096),32,components,usable,[24]*len(components))
        except ValueError as final:raise ValueError(str(initial)+'; shared-components: '+str(final))from final
        parts=[[p for k in ks for p in rr[k]]for ks in mapping]
        need(all(len(v)<=24 for v in parts),'Shared parts exceed limit')
        return raw,parts,'canonical_mirror_shared_texels'

def pack(data,desired):
    need(sha(data)==PARENT_SHA,'Wrong frozen wall/front/lowHP parent')
    need(set(desired)==SELECTED,'Only ladder143..155 and183 allowed')
    for layers in desired.values():
        need(set(layers)=={0,5,6,7,8},'Exactly five costume layers required')
        for v in layers.values():need(v.shape==(384,384)and v.dtype==np.uint8 and int(v.max())<16,'Wrong indexed target')
    normalized={n:{b:v.copy()for b,v in layers.items()}for n,layers in desired.items()}
    for alias,(key,delta)in ALIASES.items():
        for b in(0,5,6,7,8):
            need(np.array_equal(desired[alias][b],mirror(desired[key][b],delta)),'Mirror alias pixels changed')
            normalized[alias][b]=desired[key][b].copy()
    old_sha,old_selected,old_pack=backend.ARC_SHA,backend.SELECTED,backend.lossless_pack
    try:
        backend.ARC_SHA=PARENT_SHA;backend.SELECTED=SELECTED;backend.lossless_pack=mirror_safe_pack
        canonical,proof=backend.pack(data,normalized)
    finally:backend.ARC_SHA=old_sha;backend.SELECTED=old_selected;backend.lossless_pack=old_pack
    stage=Archive(canonical);nc=stage.c;slack={}
    for b in(0,5,6,7,8):
        changes={}
        for alias,(key,delta)in ALIASES.items():
            rr=[]
            for p in composition_frame(stage.c,b,alias)['parts']:
                nx=delta-p['x']-15;need(-128<=nx<=127,'Mirrored part coordinate overflow')
                rr.append(struct.pack('<BBbb',p['flags']^64,p['tile'],nx,p['y']))
            changes[alias]=b''.join(rr)
        nc,slack[b]=repack_parts(nc,b,changes)
    result=replace_entry(canonical,3,nc);a=Archive(result);layer_checks=mask_checks=other_parts=0
    for n in SELECTED:
        for b in(0,5,6,7,8):need(np.array_equal(a.layer(n,b)[0],desired[n][b]),'Mirror readback target mismatch');layer_checks+=1
        for mask in range(16):
            for arm in(1,2):need(a.composite(n,mask,arm)[0].tobytes()==compose(a,desired[n],mask).tobytes(),'Final partial target mismatch');mask_checks+=1
    for b in range(len(bank_offsets(stage.c))):
        for n in range(composition_frame(stage.c,b,0)['bank_frame_count']):
            if b in(0,5,6,7,8)and n in ALIASES:continue
            need(records(stage.c,b,n)==records(nc,b,n),'Nonalias composition changed');other_parts+=1
    proof.update({'result_arc_sha256':sha(result),'parts_slack':slack,'canonical_mirror_aliases':ALIASES,'mirror_exact_layer_checks':layer_checks,'final_partial_mask_arm_checks':mask_checks,'nonalias_composition_records_preserved':other_parts,'tile16_reserved_transparent':True})
    return result,proof

def main():
    data=(H/'prepared_wall_front01/PL00_U.ARC').read_bytes();selection=(H/'prepared_wall_front01/ST0E_U1.ARC').read_bytes();need(sha(selection)==SELECTION_SHA,'Selection changed')
    out=H/'prepared_ladder_wall_front02';need(not out.exists(),'Output exists');out.mkdir();desired=targets()
    try:result,proof=pack(data,desired)
    except ValueError as exc:
        write(out/'capacity_failure.json',{'passed':False,'reason':str(exc),'source_sha256':sha(data),'art_not_simplified':True,'arc_not_written':True});raise
    a=Archive(result);before=Archive(data);(out/'PL00_U.ARC').write_bytes(result);(out/'ST0E_U1.ARC').write_bytes(selection)
    proof.update({'new_body_and_accepted_idle_head':False,'new_full_heads_and_outfits':True,'includes_frozen_wall55_66_lowhp120_125_front156_158_selection19_21':True,'source_bin_sha256':SOURCE_SHA,'target_hashes':{str(n):{str(b):sha(v.tobytes())for b,v in layers.items()}for n,layers in desired.items()},'body_or_arm_resizing':False,'game_runtime_verified':False})
    write(out/'verification.json',proof)
    write(out/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{'PL00_U.ARC':{'path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':BASELINE_SHA,'after':sha(result)},'ST0E_U1.ARC':{'path':(out/'ST0E_U1.ARC').relative_to(ROOT).as_posix(),'before':'131645e5e28f51411bfa192a45b967f69097f805d060aaa8351273c89e9dec46','after':SELECTION_SHA}}})
    for mask,name in((0,'base'),(15,'fourth')):
        items=[]
        for n in sorted(SELECTED):
            pic=a.composite(n,mask)[0];need(pic.tobytes()==compose(a,desired[n],mask).tobytes(),'Actual readback differs');pic.save(out/f'{name}_{n:03}.png');items.extend([(f'{n} current',before.composite(n,mask)[0]),(f'{n} actual new ARC',pic)])
        for k in range(0,len(items),12):page(items[k:k+12],a.composite(0,mask)[0],out/f'{name}_comparison{k//12:02}.png',cols=2,scale=4)
    for n in sorted(SELECTED):page([(f'{n} mask{m:X}',a.composite(n,m)[0])for m in range(16)],a.composite(0,15)[0],out/f'partial_{n:03}.png',cols=4,scale=3)
    print(json.dumps({'sha256':sha(result),'groups':proof['groups'],'parts_slack':proof['parts_slack'],'gfx_slack':proof['graphics']['remaining_slack']}))

if __name__=='__main__':main()
