"""나나 포스아머 체크포인트의 그래픽만 갱신하고 게임 진행은 보존한다."""
import argparse, gzip, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_fourth_pilot import entry,require,write
from scripts.discover_inputs import sha256
from scripts.project import digest
from src.psx_player import graphics_bank,decode_stream
from src.epsxe_state import locate_vram


def refresh(data,old,new,*,allow_low_health=False,allow_unchanged_ladder=False):
    require(len(data)==4254418 and data.startswith(b'ePSXe\x06\x00SLUS_005.61'),'Unsupported state')
    cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text())
    exe=(ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.exe').read_bytes()
    addr=cfg['idle_sequence_address'];off=2048+addr-cfg['executable']['load_address'];anchor=exe[off:off+48]
    hit=data.find(anchor);require(hit>=0 and data.find(anchor,hit+1)<0,'Ambiguous RAM')
    rampos=hit-(addr&0x1fffff);ram=data[rampos:rampos+0x200000];player=ram[0x1418c8:0x1418c8+0xe4]
    n=player[0x47]
    idle=player[0x17]==5 and n in (0,115,116,117,118,119)
    low=allow_low_health and player[0x17]==6 and n in range(120,126) and player[0x5c]>0
    ladder=allow_unchanged_ladder and player[0x17]==31 and n==147 and player[0x5c]>0
    require(player[2]==0 and player[0xa7]==15 and (idle or low or ladder),'Expected full armor idle or explicitly supported live state')
    require(entry(old,9)==entry(new,9),'Palette refresh not supported')
    dst=bytearray(data);allowed=bytearray(len(data));ranges=[]
    def replace(pos,before,after,name):
        require(len(before)==len(after) and data[pos:pos+len(before)]==before,'Asset range differs')
        dst[pos:pos+len(after)]=after;allowed[pos:pos+len(after)]=bytes([1])*len(after)
        ranges.append({'kind':name,'offset':pos,'size':len(after),'before_sha256':sha256(before),'after_sha256':sha256(after)})
    for kind in (2,3):
        a,b=entry(old,kind),entry(new,kind);pos=ram.find(a)
        require(pos>=0 and ram.find(a,pos+1)<0,'Parent graphics not unique in RAM')
        replace(rampos+pos,a,b,f'ARC entry {kind}')
    decoded=[];frames=[]
    for arc in (old,new):
        g=entry(arc,2);f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];frames.append(f)
        decoded.append(decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data)
    before,after=decoded;require(frames[0]['tile_count']==frames[1]['tile_count'],'Active texture size changed')
    if ladder:
        from scripts.prepare_shibuki_ultimate_production import records
        require(before==after and all(records(entry(old,3),cb,n)==records(entry(new,3),cb,n)for cb in(0,5,6,7,8)),'Active ladder graphics changed')
    replace(rampos+0x16dea8,before,after,'RAM active player texture')
    video=locate_vram(data,before,frames[0]['tile_count']);cursor=0
    for first in range(0,frames[0]['tile_count'],16):
        width=min(16,frames[0]['tile_count']-first)*8
        for y in range(16):
            pos=video+(first//16*16+y)*2048+640
            replace(pos,before[cursor:cursor+width],after[cursor:cursor+width],'VRAM player texture row');cursor+=width
    differences=[i for i,(a,b) in enumerate(zip(data,dst)) if a!=b]
    require(all(allowed[i] for i in differences),'Non-graphic state changed')
    require(dst[rampos+0x1418c8:rampos+0x1418c8+0xe4]==player,'Player state changed')
    return bytes(dst),{'ram_offset':rampos,'vram_offset':video,'frame':n,'armor':player[0xa7],
        'arm_type':player[0xb8],'animation':player[0x17],'hp':player[0x5c],'low_health_checkpoint':bool(low),'unchanged_ladder_checkpoint':bool(ladder),'changed_bytes':len(differences),'asset_ranges':ranges,
        'gameplay_and_all_nonasset_bytes_preserved':True,
        'runtime_evidence_kind':'graphics-refreshed checkpoint; not fresh disc loading proof'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--source-sha256',required=True)
    p.add_argument('--parent',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();source,parent,build,output=[x.resolve() for x in (a.source,a.parent,a.build,a.output)]
    require(source.is_relative_to(ROOT/'work/ver_rin_nana/checkpoints') and output.is_relative_to(ROOT/'work/ver_rin_nana/checkpoints') and not output.exists(),'Isolated checkpoint paths required')
    require(all(x.is_relative_to(ROOT/'out/ver_rin_nana') for x in (parent,build)),'Unexpected build paths')
    require(digest(source)==a.source_sha256,'Source state hash differs')
    arcs=[]
    for b in (parent,build):
        m=json.loads((b/'manifest.json').read_text('utf8'));require(m['task'] in ('fourth_armor_nana','ultimate_armor_nana'),'Unsupported armor task')
        arc=(b/('PL02_U.ARC' if m['task']=='ultimate_armor_nana' else 'modified.arc')).read_bytes()
        require(sha256(arc)==m['modified_archive_sha256'],'Unsupported build')
        arcs.append(arc)
    old_task=json.loads((parent/'manifest.json').read_text('utf8'))['task'];new_task=json.loads((build/'manifest.json').read_text('utf8'))['task'];require(old_task==new_task,'Armor routes differ')
    allow_low_health=new_task=='ultimate_armor_nana' and m['kind'] in ('nana_ultimate_low_hp','nana_ultimate_low_hp_shape')
    allow_unchanged_ladder=False
    if new_task=='ultimate_armor_nana' and m['kind'] in ('nana_ultimate_ladder','nana_ultimate_ceremony'):
        import numpy as np
        from scripts.prepare_nana_ultimate_shot_arm import full
        require(all(np.array_equal(full(arcs[0],n),full(arcs[1],n))for n in range(120,126)),'Ladder checkpoint must preserve accepted low-health poses')
        allow_low_health=True
        if m['kind']=='nana_ultimate_ceremony':
            require(all(np.array_equal(full(arcs[0],n),full(arcs[1],n))for n in list(range(143,156))+[183]),'Ceremony checkpoint must preserve accepted ladder')
            allow_unchanged_ladder=True
    state=gzip.decompress(source.read_bytes());new,report=refresh(state,*arcs,allow_low_health=allow_low_health,allow_unchanged_ladder=allow_unchanged_ladder)
    if new_task=='ultimate_armor_nana':require(state[report['ram_offset']+0x1721f7]==1,'Expected native Ultimate flag')
    again,_=refresh(state,*arcs,allow_low_health=allow_low_health,allow_unchanged_ladder=allow_unchanged_ladder);require(again==new,'State reproduction differs')
    if new_task=='ultimate_armor_nana':
        # F3 also restores LOAD's persistent VRAM page. Refreshing player ARC
        # and MOJIPAT alone leaves obsolete X tiles visible in save previews.
        from scripts.verify_nana_ultimate_ui import read_assets
        from scripts.prepare_nana_save_atlas_checkpoint import atlas,refresh as refresh_ui,OLD_BUILD,OLD_SHA,VRAM_OFFSET
        require(report['vram_offset']==VRAM_OFFSET,'Unsupported UI atlas VRAM layout')
        require(digest(build/'rin_nana.bin')==m['modified_bin']['sha256'],'Target disc changed')
        ui,_=read_assets(build/'rin_nana.bin',('MOJIPAT.ARC','LOAD_U.ARC'));target=entry(ui['LOAD_U.ARC'],0x10008)
        if atlas(new)!=target:
            require(digest(OLD_BUILD/'rin_nana.bin')==OLD_SHA,'Unknown stale atlas source')
            old_ui,_=read_assets(OLD_BUILD/'rin_nana.bin',('LOAD_U.ARC',))
            new,ui_report=refresh_ui(new,entry(old_ui['LOAD_U.ARC'],0x10008),target,ui['MOJIPAT.ARC'])
            again,_=refresh_ui(again,entry(old_ui['LOAD_U.ARC'],0x10008),target,ui['MOJIPAT.ARC'])
            require(new==again,'Persistent UI reproduction differs')
            report['player_changed_bytes']=report['changed_bytes']
            report['changed_bytes']+=ui_report['changed_vram_bytes']
            report['persistent_ui_refresh']=ui_report
        else:report['persistent_ui_refresh']={'already_current':True,'changed_vram_bytes':0}
        require(atlas(new)==target,'Persistent save atlas differs after refresh')
    output.parent.mkdir(parents=True,exist_ok=True);packed=gzip.compress(new,mtime=0);output.write_bytes(packed)
    require(digest(source)==a.source_sha256,'Source changed')
    report.update(source=source.relative_to(ROOT).as_posix(),source_sha256=a.source_sha256,output_sha256=sha256(packed),
                  parent=parent.relative_to(ROOT).as_posix(),build=build.relative_to(ROOT).as_posix(),reproduced_identical=True)
    write(output.parent/'refresh.json',report);print(json.dumps({k:v for k,v in report.items() if k!='asset_ranges'}))


if __name__=='__main__':main()
