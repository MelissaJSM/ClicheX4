"""실제 린 탑승 체크포인트의 그래픽만 Riko로 교환한 격리 시험 복사본."""
import argparse,gzip,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader
from scripts.build_rin_idle import entry
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.epsxe_state import locate_vram

SOURCE=ROOT/'work/ver_rin_nana/checkpoints/ride_armor_accepted_20261029T005856936087Z/accepted_ride_armor/SLUS_005.61.000'
SOURCE_SHA='a07e488ce7ed48a69af7d5175e7f16794e2c2a196810d395ab71a5ac78fdbf46'
OLD=ROOT/'out/ver_rin_nana/rin_ride_heads_20261029T003329979054Z'
OLD_ARC_SHA='8b12aef9402e0fb8d7a240b777a654bca62bd6815a23b531960fe6d7c63ff572'
TARGET=ROOT/'out/ver_buki_riko/overhaul_20261105_candidate02/shibuki_riko.bin'
TARGET_SHA='3344f2a94a3a88beeb2b6906ee8f2c3d28d1400d2478fc77a395d24af0fce275'
OUT=ROOT/'work/overhaul_20261105/audio/riko_ride_clone_from_rin_v1'
RP=442;VR=2569183
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def require(v,msg):
    if not v:raise ValueError(msg)

def refresh(s,old,new,preserve_source_ui=False):
    require(len(s)==4254418 and s.startswith(b'ePSXe\x06\x00SLUS_005.61'),'Unsupported state')
    ram=s[RP:RP+0x200000];player=ram[0x1418c8:0x1418c8+228]
    require((player[2],player[5],player[0x17],player[0x47],player[0xc5],player[0xd4])==(1,18,41,66,255,41),'Expected actual character1 RideArmor state')
    require(ram[0x1721cc:0x1721ce]==bytes([4,1]),'Unexpected stage')
    result=bytearray(s);allowed=bytearray(len(s));ranges=[]
    def update(label,start,before,after):
        require(len(before)==len(after) and s[start:start+len(before)]==before,'Range source differs: '+label)
        require(not any(allowed[start:start+len(before)]),'Overlapping ranges')
        result[start:start+len(after)]=after;allowed[start:start+len(after)]=bytes([1])*len(after)
        ranges.append(dict(label=label,state_offset=start,bytes=len(before),before_sha256=sha(before),after_sha256=sha(after)))
    locations={2:0x1789a0,3:0x1ace9c,9:0x178000}
    old_entries={k:entry(old,k)[1] for k in locations};new_entries={k:entry(new,k)[1] for k in locations}
    if preserve_source_ui:
        # All vehicle head compositions already agree. Preserve the original
        # complete Rin composition resource, including its resident HUD/UI.
        for frame in range(66,86):require(composition_frame(old_entries[3],5,frame)==composition_frame(new_entries[3],5,frame),'Head composition differs')
        new_entries[3]=old_entries[3]
    for k,at in locations.items():
        before=old_entries[k];require(ram.find(before)==at and ram.find(before,at+1)<0,'Resident entry not unique')
        if k==3 and preserve_source_ui:continue
        update(f'PL01 entry {k}',RP+at,before,new_entries[k])
    frames=[];compositions=[]
    for es in (old_entries,new_entries):
        f=graphics_bank(es[2],1)['frames'][66];require(f['tile_count']==1,'Active head tile count changed')
        frames.append(decode_stream(es[2],f['offset'],f['limit'],128).data)
        compositions.append(composition_frame(es[3],5,66))
    require(compositions[0]==compositions[1],'Active composition pointers/pose changed')
    require(locate_vram(s,frames[0],1)==VR,'Unique GPU texture source differs')
    update('Active decoded head frame66',RP+0x16dea8,frames[0],frames[1])
    for y in range(16):update(f'GPU head row {y}',VR+y*2048+640,frames[0][y*8:y*8+8],frames[1][y*8:y*8+8])
    old_pal,new_pal=old_entries[9][:32],new_entries[9][:32]
    require(ram.find(old_pal)==0x178000 and ram.find(old_pal,0x178001)==0x1d3880 and ram.find(old_pal,0x1d3881)<0,'Unexpected active palette copies')
    update('Player palette upload copy',RP+0x1d3880,old_pal,new_pal)
    update('GPU player CLUT row480 x0',VR+480*2048,old_pal,new_pal)
    changed=[i for i,(a,b) in enumerate(zip(s,result)) if a!=b]
    require(all(allowed[i] for i in changed),'Nonresource bytes changed')
    require(result[RP+0x1418c8:RP+0x1418c8+228]==player,'Player progression/position/HP/ride values changed')
    require(locate_vram(result,frames[1],1)==VR,'Refreshed GPU texture does not match')
    require(bytes(result[RP+0x16dea8:RP+0x16dea8+128])==frames[1],'Active decoded head differs')
    for k,at in locations.items():require(result[RP+at:RP+at+len(new_entries[k])]==new_entries[k],'New resident resource differs')
    report=dict(scope='Riko graphics rendering on genuine Rin RideArmor progress; not Riko gameplay progress or fresh BIN loading',source_character=1,target_character=1,character_selection_modified=False,stage=4,area=1,animation=41,frame=66,ride_state=255,ride_animation=41,hp=player[0x5c],world=[struct.unpack_from('<i',player,o)[0]/65536 for o in (8,12)],ram_offset=RP,vram_offset=VR,source_player_sha256=sha(player),output_player_sha256=sha(bytes(result[RP+0x1418c8:RP+0x1418c8+228])),source_frame66_sha256=sha(frames[0]),target_frame66_sha256=sha(frames[1]),compositions=compositions,source_entry3_whole_preserved=preserve_source_ui,head_compositions_66_through_85_equal=preserve_source_ui,resource_ranges=ranges,changed_bytes=len(changed),all_outside_resource_ranges_byte_identical=True,all_npc_progress_engine_audio_text_bytes_preserved=True,source_exe_and_fonts_are_old_rin_build=True,graphics_only_test_not_fresh_disc_loading=True,active_sstates_modified=False,emulator_keys_sent=False,runtime_verified=False)
    return bytes(result),report

def main(preserve_source_ui=False):
    out=OUT.with_name('riko_ride_clone_from_rin_v2') if preserve_source_ui else OUT
    require(not out.exists(),'Fresh clone destination required')
    require(digest(SOURCE)==SOURCE_SHA and digest(TARGET)==TARGET_SHA,'Unsupported state or target BIN')
    old=(OLD/'modified.arc').read_bytes();manifest=json.loads((OLD/'manifest.json').read_text(encoding='utf8'))
    require(sha(old)==OLD_ARC_SHA==manifest['modified_archive_sha256'],'Source asset manifest differs')
    with TARGET.open('rb') as f:
        d=DiscReader(f,TARGET.stat().st_size);record=next(r for r in d.inspect()['files'] if r['path']=='/ARC/PL01_U.ARC;1');new=d.read(record['lba'],record['size'])
    raw=gzip.decompress(SOURCE.read_bytes());changed,report=refresh(raw,old,new,preserve_source_ui)
    require(refresh(raw,old,new,preserve_source_ui)[0]==changed,'Reproduction differs')
    rejected=[]
    for name,offset in (('character',RP+0x1418ca),('ride',RP+0x1418c8+0xc5),('active_head',RP+0x16dea8),('resident_parts',RP+0x1ace9c),('palette_copy',RP+0x1d3880),('GPU',VR+640)):
        bad=bytearray(raw);bad[offset]^=1
        try:refresh(bytes(bad),old,new,preserve_source_ui)
        except ValueError:rejected.append(name)
        else:raise AssertionError('Accepted corrupted source '+name)
    out.mkdir(parents=True);packed=gzip.compress(changed,mtime=0);dest=out/'SLUS_005.61.000'
    with dest.open('xb') as f:f.write(packed)
    require(gzip.decompress(dest.read_bytes())==changed and digest(SOURCE)==SOURCE_SHA and digest(TARGET)==TARGET_SHA and digest(OLD/'modified.arc')==OLD_ARC_SHA,'Readback/input preservation failed')
    report.update(source=SOURCE.relative_to(ROOT).as_posix(),source_sha256=SOURCE_SHA,source_build=OLD.relative_to(ROOT).as_posix(),source_build_bin_sha256_from_manifest=manifest['modified_bin']['sha256'],source_arc_sha256=OLD_ARC_SHA,target_bin=TARGET.relative_to(ROOT).as_posix(),target_bin_sha256=TARGET_SHA,target_arc_sha256=sha(new),target_record=record,output=dest.relative_to(ROOT).as_posix(),output_sha256=sha(packed),uncompressed_sha256=sha(changed),reproduced_identical=True,rejected_corrupt_inputs=rejected,original_state_and_assets_preserved=True,full_bin_restored=False)
    (out/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k not in ('resource_ranges','compositions')}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--preserve-source-ui',action='store_true');a=p.parse_args();main(a.preserve_source_ui)
