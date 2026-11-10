"""217 새몸/새외곽과220 역사 전체 배경을 분리한10층 목표.218/219 보존."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from src.psx_player import indexed_atlas,composition_frame
from scripts.prepare_shibuki_ultimate_production import records
from pack_shibuki_hurt import raw
from prepare_lowhp_final import compose
from inspect_nova_strike_base import outline
P=H/'prepared_nova_base01/PL00_U.ARC';PARENT='619032d0b81ffc50e5f5664ff1e3d0c077f226a7d5a8ccfac081be6a2126c6c5'
PBS=(0,5,6,7,8);REFS=(217,220);TD=H/'nova_strike_base_targets01'

def main():
    need(not TD.exists(),'새 목표');TD.mkdir();a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'고정 부모');s=H/'nova_strike_layers_probe01';need(not json.loads((s/'report.json').read_text('utf8'))['unresolved'],'미정합 없음')
    ls={b:np.array(Image.open(s/f'217_bank{b}_indices.png'))for b in PBS};need(np.array_equal(ls[0],np.array(Image.open(H/'nova_strike_base_native01/base_217_indices.png'))),'새몸 보호')
    first=ls[0].copy();ls[0]=outline(first);targets={217:ls,220:{b:z.copy()for b,z in ls.items()}}
    source=H/'chaser_sources01/original_base.ARC';o=Archive(source.read_bytes());f=o.banks[0]['frames'][220];old=raw(o,0,220);need(f['tile_count']==29,'원정원')
    atlas=np.frombuffer(indexed_atlas(old,29)[0],np.uint8);seed=bytearray(4096);_,mapping,_=indexed_atlas(bytes(seed),32);tileproof=[]
    for t in range(18):
        tile=[]
        for y in range(16):
            for x in range(16):
                i=(t//16*16+y)*256+t%16*16+x;v=int(atlas[i]);v=0 if not v else 6 if v==12 else 9;tile.append(v);pos,shift=mapping[i];seed[pos]|=v<<shift
        tileproof.append({'source_tile':t,'stored_tile':t,'all256_nibbles_sha256':sha(bytes(tile))})
    prefix=records(o.c,0,220);need(len(prefix)==96 and {p['tile']for p in composition_frame(o.c,0,220)['parts']}==set(range(18)),'원효과24파트/18타일')
    bg=np.array(Image.open(H/'nova_strike_base_sources01/220_background_indices.png'));oldbody=outline(np.array(Image.open(H/'nova_strike_base_sources01/217_source_indices.png')))
    need(np.array_equal(bg[oldbody==0],a.layer(220)[0][oldbody==0]),'역사 외부효과 보호')
    z=bg.copy();z[ls[0]>0]=ls[0][ls[0]>0];targets[220][0]=z
    (TD/'effect220_seed32.raw').write_bytes(bytes(seed));(TD/'effect220_prefix.bin').write_bytes(prefix);Image.fromarray(bg).save(TD/'220_background_indices.png');Image.fromarray(ls[0]).save(TD/'220_body_with_outline_indices.png')
    hashes={}
    for n,layers in targets.items():
        hashes[str(n)]={}
        for b,v in layers.items():Image.fromarray(v).save(TD/f'{n:03}_bank{b}_indices.png');hashes[str(n)][str(b)]=sha(v.tobytes())
        for form,mask in(('base',0),('fourth',15)):compose(a,layers,mask).save(TD/f'{form}_{n:03}.png')
    for form,mask in(('base',0),('fourth',15)):page([(f'{n} 이전',a.composite(n,mask)[0])if k==0 else(f'{n} 새몸/원배경',compose(a,targets[n],mask))for n in REFS for k in(0,1)],a.composite(0,mask)[0],TD/f'{form}_comparison.png',cols=2,scale=4)
    files=[P,source,Path(__file__),H/'inspect_nova_strike_base.py',H/'probe_nova_strike_layers.py',H/'prepare_nova_strike_base.py',H/'register_nova_strike_base.py',H/'prepare_nova_strike_boot.py',H/'register_nova_strike_boot.py']
    for name in('nova_strike_base_sources01','nova_strike_base_inputs01','nova_strike_base_native01','nova_strike_boot_inputs01','nova_strike_boot_native01','nova_strike_layers_probe01'):files.extend(p for p in(H/name).rglob('*')if p.is_file())
    files.extend(p for p in TD.iterdir()if p.is_file())
    write(TD/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PARENT,'refs':list(REFS),'targets':hashes,'source_files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in sorted(set(files))},'effect220':{'source_arc':source.relative_to(ROOT).as_posix(),'source_arc_sha256':sha(o.data),'source_ref':220,'source_consumed_tiles':18,'native_parts':24,'all_full_tile_proofs':tileproof,'prefix_sha256':sha(prefix),'seed_sha256':sha(bytes(seed)),'native_index_mapping':{str(i):(0 if not i else 6 if i==12 else 9)for i in range(16)},'hidden_background_kept':True},'new217_body_pixels':int((first>0).sum()),'new217_outline_pixels':int(((ls[0]>0)&(first==0)).sum()),'effects218_219_unchanged':True,'policy':['217은 새몸의 Manhattan1 색6 외곽을 만든다. 기존 외곽158픽셀을 새몸에 억지로 늘리거나 복사하지 않는다.','220은 원US220 전체18타일에 역사 효과색 매핑을 적용한 배경을 전부 저장하고24파트 뒤에 새217 몸/외곽을 그리는 후보. 기존옛몸 내부651셀 색차이를 새머리에 복사하지 않는다.','현재 메모리 수납/파트 개수 검토 전 목표층이며 ARC를 작성하지 않았다.31개base파트의 실제 renderer 제약 확인은 별도다.']});print(json.dumps({'manifest':sha((TD/'manifest.json').read_bytes()),'files':len(set(files)),'new_outline':int(((ls[0]>0)&(first==0)).sum())}))
if __name__=='__main__':main()
