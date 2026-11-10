"""확인한 무기 획득 저장 한 개의 비활성 플레이어 ARC 캐시만 갱신한다."""
import gzip, json, sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.prepare_nana_fourth_pilot import entry,require,write
from scripts.project import digest
from scripts.discover_inputs import sha256
D=R/'work/ver_rin_nana/nana_ultimate_armor'
SOURCE=R/'work/ver_rin_nana/checkpoints/before_ultimate_special_20261104T113151940404Z/current_progress/SLUS_005.61.000'
SOURCE_SHA='b0ad8ae3fe1934dff04cd27706fe172b18d2111da8d117258612eb68c9bd467c'
PARENT=R/'out/ver_rin_nana/nana_ultimate_victory_edge_20261104T111230439476Z'
BUILD=R/'out/ver_rin_nana/nana_ultimate_special_20261104T113013217294Z'

def refresh(data,old,new):
    require(sha256(data)==sha256(gzip.decompress(SOURCE.read_bytes())),'Only inspected menu snapshot allowed')
    require(len(data)==4254418 and data.startswith(b'ePSXe\x06\x00SLUS_005.61'),'Unsupported state')
    anchor=bytes.fromhex('150001000c0001922a0001930c00019436000100');hit=data.find(anchor)
    require(hit>=0 and data.find(anchor,hit+1)<0,'Ambiguous RAM');rp=hit-0x11a2f8
    require(rp==442,'RAM position differs');ram=data[rp:rp+0x200000];p=ram[0x1418c8:0x1418c8+228]
    require(all(p[x]==0 for x in(2,0x17,0x47,0x5c,0xa7)) and ram[0x1721f7]==1,'Inspected non-player menu state changed')
    require(entry(old,9)==entry(new,9),'Palette changed')
    out=bytearray(data);allow=bytearray(len(data));ranges=[]
    for kind,expected in((2,1542560),(3,1734644)):
        before,after=entry(old,kind),entry(new,kind);pos=ram.find(before)
        require(len(before)==len(after) and pos==expected and ram.find(before,pos+1)<0,'ARC cache range differs')
        out[rp+pos:rp+pos+len(after)]=after;allow[rp+pos:rp+pos+len(after)]=b'\x01'*len(after)
        ranges.append(dict(kind=kind,offset=rp+pos,size=len(after),before_sha256=sha256(before),after_sha256=sha256(after)))
    changed=[i for i,(a,b) in enumerate(zip(data,out)) if a!=b]
    require(all(allow[i] for i in changed),'Non-cache state changed')
    require(out[rp+0x1418c8:rp+0x1418c8+228]==p,'Player state changed')
    return bytes(out),dict(changed_bytes=len(changed),asset_ranges=ranges,all_nonasset_bytes_preserved=True,
        menu_vram_and_all_progress_preserved=True,active_player_texture_not_changed=True,
        reason='Player inactive on visually inspected Aiming Laser Weapon Get; only two exact ARC cache matches replaced')

if __name__=='__main__':
    require(digest(SOURCE)==SOURCE_SHA,'Source changed')
    old=(PARENT/'PL02_U.ARC').read_bytes();new=(BUILD/'PL02_U.ARC').read_bytes()
    require(sha256(old)=='720c5e6745a7d97a653f925654e042e966907127233490378f0e9210df6c5648' and sha256(new)=='4d47a3ea8bd6eb8e21f1c94ee6540164fdc2c813a649009a62324c47ea2874e1','Wrong archives')
    original=gzip.decompress(SOURCE.read_bytes());result,proof=refresh(original,old,new);again,_=refresh(original,old,new)
    require(result==again,'Independent refresh differs')
    dst=R/'work/ver_rin_nana/checkpoints/nana_ultimate_special_v1/SLUS_005.61.000'
    require(not dst.exists(),'Fresh output required');dst.parent.mkdir();dst.write_bytes(gzip.compress(result,mtime=0))
    proof.update(source=SOURCE.relative_to(R).as_posix(),source_sha256=SOURCE_SHA,output=dst.relative_to(R).as_posix(),output_sha256=digest(dst),reproduced_identical=True)
    write(dst.parent/'refresh.json',proof);print(json.dumps(proof))
