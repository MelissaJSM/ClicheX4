"""탑승 중 진행 저장의 상주 그래픽만 새 UI/캡슐 자원으로 갱신한다."""
import argparse,gzip,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_fourth_ui import read_sources,entry,verify
from scripts.prepare_nana_fourth_pilot import require,write
from scripts.discover_inputs import sha256
from scripts.project import digest
from src.psx_player import graphics_bank,decode_stream

SOURCE_SHA='bd3d65875313196a476327a04c18a50850e5d4eb625c2900c830144f5b400bff'
BUILD_SHA='c7fc576c68a4c4bc2f55090bfccf47d4e03a11489fa49c9b824399cbcab11d8a'

def refresh(raw,old,new):
    require(len(raw)==4254418 and raw.startswith(b'ePSXe\x06\x00SLUS_005.61'),'Unsupported checkpoint')
    rp=442;ram=raw[rp:rp+0x200000];player=ram[0x1418c8:0x1418c8+228]
    require(player[2]==0 and player[0x17]==41 and player[0x47]==184 and player[0xa7]==15,'Expected captured vehicle state')
    # 이번 변경은 별도 캡슐 스트림이며 현재 탑승 텍스처는 동일하다.
    decoded=[]
    for a in (old['PL00_U.ARC'],new['PL00_U.ARC']):
        g=entry(a,2);f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][184]
        decoded.append(decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data)
    require(decoded[0]==decoded[1],'Active texture changed')
    require(ram[0x16dea8:0x16dea8+len(decoded[0])]==decoded[0],'Captured texture differs')
    ranges=[];dst=bytearray(raw);allowed=set()
    assets=[('MOJIPAT.ARC',old['MOJIPAT.ARC'],new['MOJIPAT.ARC'])]
    assets += [(f'PL00 entry {k}',entry(old['PL00_U.ARC'],k),entry(new['PL00_U.ARC'],k)) for k in (2,3)]
    for name,a,b in assets:
        pos=ram.find(a);require(len(a)==len(b) and pos>=0 and ram.find(a,pos+1)<0,'Nonunique or missing RAM resource: '+name)
        start=rp+pos;dst[start:start+len(a)]=b;allowed.update(range(start,start+len(a)))
        ranges.append({'name':name,'offset':start,'size':len(a),'before_sha256':sha256(a),'after_sha256':sha256(b)})
    diff=[i for i,(a,b) in enumerate(zip(raw,dst)) if a!=b]
    require(all(i in allowed for i in diff),'Nonasset state changed')
    require(dst[rp+0x1418c8:rp+0x1418c8+228]==player,'Progress changed')
    return bytes(dst),{'ram_offset':rp,'asset_ranges':ranges,'changed_bytes':len(diff),'player_bytes_preserved':True,'all_nonasset_bytes_preserved':True,
        'vram_preserved':True,'active_vehicle_texture_preserved':True,'world':[struct.unpack_from('<i',player,o)[0]/65536 for o in (8,12)],
        'hp':player[0x5c],'armor':player[0xa7],'arm_type':player[0xb8],'animation':player[0x17],'frame':player[0x47],
        'scope':'graphics-refreshed vehicle checkpoint; save UI fresh boot evidence is separate'}

def main(source,build,output):
    source,build,output=source.resolve(),build.resolve(),output.resolve()
    require(source.is_relative_to(ROOT/'work/ver_rin_nana/checkpoints') and output.is_relative_to(ROOT/'work/ver_rin_nana/checkpoints') and not output.exists(),'Isolated fresh checkpoint required')
    require(build.is_relative_to(ROOT/'out/ver_rin_nana') and digest(build/'rin_nana.bin')==BUILD_SHA and digest(source)==SOURCE_SHA,'Unsupported build or source')
    old,_=read_sources();new={n:(build/'fourth_ui'/n).read_bytes() for n in old};verify(old,new)
    raw=gzip.decompress(source.read_bytes());edited,report=refresh(raw,old,new);again,_=refresh(raw,old,new);require(edited==again,'Reproduction differs')
    rejected=[]
    for name,a,b in [('missing_menu',old['MOJIPAT.ARC'],None),('missing_graphics',entry(old['PL00_U.ARC'],2),None),('active_texture',raw[442+0x16dea8:442+0x16dea8+64],442+0x16dea8)]:
        test=bytearray(raw);pos=raw.find(a) if b is None else b;require(pos>=0,'Missing negative test anchor');test[pos]^=1
        try:refresh(bytes(test),old,new)
        except ValueError:rejected.append(name)
        else:raise AssertionError('Accepted corrupted checkpoint '+name)
    output.parent.mkdir(parents=True,exist_ok=True);packed=gzip.compress(edited,mtime=0);output.write_bytes(packed)
    report.update(source=source.relative_to(ROOT).as_posix(),source_sha256=SOURCE_SHA,output_sha256=sha256(packed),build=build.relative_to(ROOT).as_posix(),build_sha256=BUILD_SHA,reproduced_identical=True,rejected_inputs=rejected)
    write(output.parent/'refresh.json',report);print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.source,a.build,a.output)
