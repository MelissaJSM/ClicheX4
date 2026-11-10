"""사용자 최신 Nana F1을 보존하며 인증된 자원 캐시만 새 시험 파일로 갱신한다."""
import argparse,gzip,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.inventory_riko_voice import parse_bank
from scripts.overhaul_audio_verify_cpu import banks
from src.psx_player import graphics_bank,bank_offsets,decode_stream,composition_frame
from src.epsxe_state import locate_vram
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m

SOURCE_STATE=ROOT/'work/overhaul_20261105/baseline/current_progress/SLUS_005.61.000'
STATE_SHA='736cdc2dc277767d2e4c8b935137bc9ad5ab07ff8074323e0b2f710070657719'
SOURCE_BIN=ROOT/'out/ver_rin_nana/nana_ultimate_nova_20261104T185708218838Z/rin_nana.bin'
SOURCE_SHA='5dd089c181cd141955f8e98e3a6b028f24253f2ca4179ed34e194f6a276047f0'
DEFAULT_TARGET=ROOT/'out/ver_rin_nana/overhaul_20261105_candidate02/rin_nana.bin'
DEFAULT_SHA='610ebea71ad54569f081f03b96a7178cae91e2038f43eaa498412c9dac4773fd'
RP=442;VR=2569183
NAMES=('PL02_U.ARC','MOJIPAT.ARC','LOAD_U.ARC','SLUS_005.61','ST6_1_1.ARC')
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def require(v,msg):
    if not v:raise ValueError(msg)
def read_assets(p):
    with p.open('rb') as f:
        d=DiscReader(f,p.stat().st_size);rows={r['name'].split(';')[0]:r for r in d.inspect()['files'] if r['name'].split(';')[0] in NAMES}
        require(set(rows)==set(NAMES),'Missing disc resource')
        return {n:d.read(r['lba'],r['size']) for n,r in rows.items()}
def entry(a,kind):
    e=next(e for e in psx_arc(a) if e['type']==hex(kind));return a[e['offset']:e['offset']+e['size']]
def ranges(a,b):
    require(len(a)==len(b),'Resource size changed');out=[]
    for n,(x,y) in enumerate(zip(a,b)):
        if x==y:continue
        if out and out[-1][1]==n:out[-1][1]+=1
        else:out.append([n,n+1])
    return out

def loaded_vab_header(header,body,spu_start):
    """US 0x800E43F8의 program 인덱스/파형 SPU 주소 생성과 동일한 결과."""
    q=parse_bank(header,body,False);v=q['vab_offset'];require(struct.unpack_from('<I',header,v+4)[0]>=5,'Unsupported VAB revision')
    dst=bytearray(header);table=v+32;program_index=0
    for n in range(128):
        struct.pack_into('<I',dst,table+n*16+8,program_index)
        if header[table+n*16]:program_index+=1
    lengths=struct.unpack_from('<256H',header,table+128*16+q['program_count']*512);total=0
    for n in range(q['wave_count']+1):
        total+=lengths[n]*8
        require((spu_start+total)%8==0 and spu_start+total<=0x80000,'SPU wave pointer outside RAM')
        struct.pack_into('<H',dst,table+(n//2)*16+12+(n%2)*2,(spu_start+total)//8)
    require(total==len(body),'SPU transfer size differs')
    return bytes(dst)

def native_audio_check(ram,stage6):
    """실제 SDK까지 실행하되 하드웨어/실제 프로세스는 건드리지 않는다."""
    checks=[]
    for slot,command,voice,expected_pitch,expected_start in ((3,0,20,0x800,0x2b7e),(3,1,20,0x800,0x2b7e),(3,12,20,0x800,0x1114),(2,196,16,0x400,0xaf20),(2,199,16,0x400,0xb268)):
        u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f801000,0x1000);u.mem_write(0,ram)
        if slot==2:
            h,_,q=banks(stage6)[2];u.mem_write(0x5000,h)
            u.mem_write(0x141f58,struct.pack('<I',0x80005008));u.mem_write(0x141ef0,struct.pack('<I',0x80005000+q['vab_offset']))
        u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);u.reg_write(m.UC_MIPS_REG_RA,0x80008000)
        for reg,val in ((m.UC_MIPS_REG_A0,slot),(m.UC_MIPS_REG_A1,command),(m.UC_MIPS_REG_A2,0)):u.reg_write(reg,val)
        def stop(cpu,address,size,data):
            if address==0x80008000:cpu.emu_stop()
        u.hook_add(UC_HOOK_CODE,stop);u.emu_start(0x8001540c,0,count=200000)
        require(u.reg_read(m.UC_MIPS_REG_PC)==0x80008000 and u.reg_read(m.UC_MIPS_REG_V0)==0,'Native audio call failed')
        values=struct.unpack('<8H',u.mem_read(0x166d90+voice*16,16));left,right,pitch,address,adsr1,adsr2,env,repeat=values
        require(pitch==expected_pitch and address==expected_start and left>0 and right>0,'Native SDK chose wrong waveform/pitch/volume')
        checks.append(dict(bank=slot,command=command,voice=voice,left=left,right=right,pitch=pitch,start_register=address,adsr1=adsr1,adsr2=adsr2,native_sdk_executed=True,spu_sdk_mocked=False,stage6_command_table_injected_only_in_cpu_harness=slot==2))
    return checks

def active_composite(packed,count,parts,palette_rows,player):
    """원래 X 레이어 순서로 현재 플레이어만 합성한다. 게임 화면 캡처가 아니다."""
    import numpy as np
    from PIL import Image
    image=Image.new('RGBA',(160,160));frame=player[0x47];mask=player[0xa7];arm=player[0xb8]
    body=struct.unpack_from('<H',player,0x42)[0];body=0x7840 if body&0x8000 else body
    for bit,bank in ((0,0),(8,8),(1,5),(4,7),(2,6)):
        if bit and not mask&bit:continue
        clut=body if bank==0 else 0x7844 if bank==7 and arm==2 else 0x7843
        colors=struct.unpack('<16H',palette_rows(clut));indices=canvas_from_parts(packed,count,local_composition(composition_frame(parts,bank,frame)))
        lookup=np.array([((v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31,0 if n==0 else 255) for n,v in enumerate(colors)],dtype=np.uint8)
        image.alpha_composite(Image.fromarray(lookup[indices%16],'RGBA'))
    return image

def refresh(raw,old,new):
    require(len(raw)==4254418 and raw.startswith(b'ePSXe\x06\x00SLUS_005.61'),'Unsupported ePSXe snapshot')
    ram=raw[RP:RP+0x200000];player=ram[0x1418c8:0x1418c8+228]
    require(player[2]==0 and player[0xa7]==15 and ram[0x1721f7]==1 and player[0x17]==5 and player[0x47] in (0,115,116,117,118,119),'Expected user Ultimate Nana idle')
    for addr in (0x1540c,0x3dc1c,0x233c8):require(ram[addr:addr+64]==old['SLUS_005.61'][addr-0x10000+2048:addr-0x10000+2112],'Snapshot source EXE differs')
    dst=bytearray(raw);allowed=bytearray(len(raw));changes=[]
    def update(label,start,before,after):
        require(len(before)==len(after) and raw[start:start+len(before)]==before,'Source bytes differ: '+label)
        if before==after:return
        require(not any(allowed[start:start+len(before)]),'Overlapping update ranges: '+label)
        dst[start:start+len(after)]=after;allowed[start:start+len(after)]=bytes([1])*len(after)
        changes.append(dict(label=label,state_offset=start,size=len(after),changed_bytes=sum(a!=b for a,b in zip(before,after)),before_sha256=sha(before),after_sha256=sha(after)))
    def resident(label,before,after):
        at=ram.find(before);require(at>=0 and ram.find(before,at+1)<0,'Resident resource missing or ambiguous: '+label)
        update(label,RP+at,before,after);return at
    a,b=old['PL02_U.ARC'],new['PL02_U.ARC'];oe,ne=psx_arc(a),psx_arc(b)
    require([(e['type'],e['size']) for e in oe]==[(e['type'],e['size']) for e in ne],'Resident archive structure changed')
    supported={0x9,0x10206,0x2,0x3,0x4,0x20000,0x6,0x20101,0x20301,0x15}
    for before,after in zip(oe,ne):
        if int(before['type'],16) not in supported:
            require(a[before['offset']:before['offset']+before['size']]==b[after['offset']:after['offset']+after['size']],'Target changes an unsupported resident resource: '+before['type'])
    require(entry(a,9)==entry(b,9),'Player palette changes require a separate verified cache mapping')
    gfx_banks=bank_offsets(entry(a,2),allow_aliases=True);part_banks=bank_offsets(entry(a,3))
    require(gfx_banks==bank_offsets(entry(b,2),allow_aliases=True),'Graphics bank relocation unsupported')
    require(part_banks==bank_offsets(entry(b,3)),'Composition bank relocation unsupported')
    # This authenticated user snapshot is idle in graphics/composition bank0.
    # Repacking within those banks is supported, relocating cached bases is not.
    gfx_at=ram.find(entry(a,2));parts_at=ram.find(entry(a,3))
    require(gfx_at>=0 and parts_at>=0,'Missing source player bank resources')
    gp,cp=struct.unpack_from('<II',player,0x38)
    require(gp==0x80000000+gfx_at+gfx_banks[0],'Active graphics pointer is not authenticated bank0')
    require(cp==0x80000000+parts_at+part_banks[0],'Active composition pointer is not authenticated bank0')
    require(player[0x49]==3,'Active player does not use authenticated decode buffer0')
    bank_layout=dict(graphics_offsets=gfx_banks,composition_offsets=part_banks,
        source_target_bank_offsets_equal=True,active_graphics_bank=0,active_composition_bank=0,
        active_graphics_pointer=hex(gp),active_composition_pointer=hex(cp),active_decode_buffer=hex(0x8016dea8))
    for kind in (2,3,9,0x15):resident(f'PL02 entry {hex(kind)}',entry(a,kind),entry(b,kind))
    # Runtime static image: eleven 64-word-wide strips, each y=176..255.
    old_static,new_static=entry(a,0x10206),entry(b,0x10206)
    require(len(old_static)==len(new_static)==112640,'Unexpected static atlas')
    static_offsets=[VR+(176+y%80)*2048+640+(y//80)*128 for y in range(len(old_static)//128)]
    require(b''.join(raw[at:at+128] for at in static_offsets)==old_static,'Stale/unknown static GPU atlas')
    for y,at in enumerate(static_offsets):update('GPU static atlas row '+str(y),at,old_static[y*128:(y+1)*128],new_static[y*128:(y+1)*128])
    frame=player[0x47];decoded=[];frames=[]
    for arc in (a,b):
        g=entry(arc,2);f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][frame];frames.append(f);decoded.append(decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data)
    counts=[f['tile_count'] for f in frames];growth=None
    require(counts[0]==counts[1] or frame==0 and counts==[15,16],'Unsupported active GPU tile count change')
    require(locate_vram(raw,decoded[0],frames[0]['tile_count'])==VR,'Player GPU upload not authenticated')
    require(raw[RP+0x16dea8:RP+0x16dea8+len(decoded[0])]==decoded[0],'Active old decoded RAM differs')
    if counts==[15,16]:
        # Exact source frame119 left 16 tiles in this same native buffer/page.
        # Frame0 uploaded only 15, so its unused tail/column retain frame119.
        old_g=entry(a,2);previous=graphics_bank(old_g,0,allow_bank_aliases=True)['frames'][119]
        require(previous['tile_count']==16,'Unexpected source idle119 layout')
        retained=decode_stream(old_g,previous['offset'],previous['limit'],2048).data
        tail=raw[RP+0x16dea8+1920:RP+0x16dea8+2048]
        column=b''.join(raw[VR+y*2048+760:VR+y*2048+768] for y in range(16))
        prior_column=b''.join(retained[y*128+120:y*128+128] for y in range(16))
        require(tail==retained[1920:] and column==prior_column,'Expanded player region is not authenticated source idle119 cache')
        require(player[0x49]==3 and struct.unpack_from('<H',player,0x40)[0]==0x500,'Unexpected native player buffer/page allocation')
        require(struct.unpack_from('<I',ram,0x141f68)[0]==0x801659d0 and ram[0x1659d0:0x1659d0+8*12]==bytes(8*12),'Pending old-width GPU upload queue cannot be preserved')
        growth=dict(old_tiles=15,new_tiles=16,source_residual_frame=119,ram_extra_offset=hex(0x16dea8+1920),ram_extra_bytes=128,ram_extra_sha256=sha(tail),gpu_extra_word_x=380,gpu_extra_word_width=4,gpu_extra_y=0,gpu_extra_height=16,gpu_extra_sha256=sha(column),gpu_extra_all_transparent=not any(column),source_frame119_ram_and_gpu_residue_exact=True,native_upload_queue_all8records_empty=True,native_upload_queue_pointer_at_start=True,ownership='Native object_update.c:443 loads player at x320/y0 using buffer0 [0x16DEA8,0x16EEA8). Light-capsule independent upload starts y32. Expanded tile remains in player first16 rows; static atlas starts y176.')
    ram_before=raw[RP+0x16dea8:RP+0x16dea8+len(decoded[1])]
    update('Active player decoded RAM',RP+0x16dea8,ram_before,decoded[1]);cursor=0
    for first in range(0,frames[1]['tile_count'],16):
        width=min(16,frames[1]['tile_count']-first)*8
        for y in range(16):
            at=VR+(first//16*16+y)*2048+640;update('Active player GPU row',at,raw[at:at+width],decoded[1][cursor:cursor+width]);cursor+=width
    resident('MOJIPAT menu resource',old['MOJIPAT.ARC'],new['MOJIPAT.ARC'])
    old_load,new_load=old['LOAD_U.ARC'],new['LOAD_U.ARC']
    require([(e['type'],e['size']) for e in psx_arc(old_load)]==[(e['type'],e['size']) for e in psx_arc(new_load)],'Persistent LOAD layout changed')
    for e in psx_arc(old_load):
        k=int(e['type'],16)
        if k!=0x10008:require(entry(old_load,k)==entry(new_load,k),'Unmapped persistent LOAD change')
    atlases=[entry(x,0x10008) for x in (old_load,new_load)];require(all(len(x)==32768 for x in atlases),'Persistent LOAD atlas size')
    for y in range(256):update('Persistent save UI GPU row',VR+(256+y)*2048+1792,atlases[0][y*128:(y+1)*128],atlases[1][y*128:(y+1)*128])
    exe_changes=ranges(old['SLUS_005.61'],new['SLUS_005.61']);require(all(lo>=2048 for lo,hi in exe_changes),'EXE file header changed')
    for lo,hi in exe_changes:
        addr=lo-2048+0x10000;start=max(0,addr-8);end=addr+(hi-lo)+8
        require(ram[start:end]==old['SLUS_005.61'][start-0x10000+2048:end-0x10000+2048],'EXE change overlaps live writable data or unknown source')
        update('Immutable loaded EXE delta',RP+addr,old['SLUS_005.61'][lo:hi],new['SLUS_005.61'][lo:hi])
    source_banks,target_banks=banks(a),banks(b);require(set(source_banks)==set(target_banks)=={0,1,3},'Unexpected player sound bank set')
    starts=struct.unpack_from('<4I',ram,0x141f30);cmds=struct.unpack_from('<4I',ram,0x141f50)
    h0,b0,q0=source_banks[0];needle=b0[64:192];spu_candidates=[];pos=raw.find(needle)
    while pos>=0:
        at=pos-starts[0]-64
        if at>=0 and at+0x80000<=len(raw) and all(raw[at+starts[sl]:at+starts[sl]+len(bb)]==bb for sl,(hh,bb,qq) in source_banks.items()):spu_candidates.append(at)
        pos=raw.find(needle,pos+1)
    require(len(spu_candidates)==1,'SPURAM not uniquely authenticated by all three player banks');spu=spu_candidates[0];audio=[]
    reclaimed=[]
    for slot,(oh,ob,oq) in source_banks.items():
        nh,nb,nq=target_banks[slot];at=(cmds[slot]&0x1fffffff)-8
        require(len(oh)==len(nh) and len(ob)==len(nb) and oq['vab_offset']==nq['vab_offset'] and oq['program_count']==nq['program_count'],'Audio relocation/size change unsupported')
        for table,expected in ((0x141840,at+oq['vab_offset']),(0x1406b8,at+oq['vab_offset']+32),(0x141888,at+oq['vab_offset']+32+2048)):
            require(struct.unpack_from('<I',ram,table+slot*4)[0]&0x1fffffff==expected,'SDK VAB pointer cache differs')
        require(struct.unpack_from('<I',ram,0x175ea8+slot*4)[0]==starts[slot] and struct.unpack_from('<I',ram,0x175e58+slot*4)[0]==len(ob),'SDK SPU transfer cache differs')
        oh_live=loaded_vab_header(oh,ob,starts[slot]);nh_live=loaded_vab_header(nh,nb,starts[slot])
        update(f'Audio bank{slot} loaded header including SDK program/wave cache',RP+at,oh_live,nh_live)
        update(f'Audio bank{slot} SPURAM body',spu+starts[slot],ob,nb)
        if ob!=nb:
            for w in oq['waves']:
                begin=w['body_offset'];end=begin+w['bytes']
                if ob[begin:end]!=nb[begin:end]:reclaimed.append([starts[slot]+begin,starts[slot]+end])
        audio.append(dict(slot=slot,ram_header=at,spu_start=starts[slot],body_size=len(ob),old_wave_count=oq['wave_count'],new_wave_count=nq['wave_count'],old_header_sha256=sha(oh_live),new_header_sha256=sha(nh_live),sdk_pointer_and_transfer_caches_preserved=True))
    current_voices=[]
    for ch in range(24):
        regs=struct.unpack_from('<8H',ram,0x166d90+ch*16);address=regs[3]*8
        require(not any(lo<=address<hi for lo,hi in reclaimed),'Existing voice points into replaced waveform storage')
        current_voices.append(dict(channel=ch,start_byte=address,left=regs[0],right=regs[1],pitch=regs[2]))
    require(all(a==b or allowed[n] for n,(a,b) in enumerate(zip(raw,dst))),'Unexpected nonasset byte change')
    require(dst[RP+0x1418c8:RP+0x1418c8+228]==player and dst[RP+0x1721c0:RP+0x172220]==ram[0x1721c0:0x172220],'Player or progress state changed')
    require(dst[spu+0x80000:]==raw[spu+0x80000:],'SPU plugin playback/decoder state changed')
    changed_ram=bytes(dst[RP:RP+0x200000]);native=native_audio_check(changed_ram,new['ST6_1_1.ARC'])
    require(locate_vram(bytes(dst),decoded[1],counts[1])==VR,'Updated player GPU upload differs')
    gpu_packed=b''.join(dst[VR+(first//16*16+y)*2048+640:VR+(first//16*16+y)*2048+640+min(16,counts[1]-first)*8] for first in range(0,counts[1],16) for y in range(16))
    require(gpu_packed==changed_ram[0x16dea8:0x16dea8+len(decoded[1])]==decoded[1],'Updated active RAM/GPU differs')
    clut_sources={}
    def target_palette(clut):
        # Armor CLUTs are selected/copied by the engine, not uploaded as a
        # linear whole-entry atlas. Authenticate their exact source rows.
        at=VR+(clut>>6)*2048+(clut&63)*32;colors=raw[at:at+32]
        rows=[n for n in range(len(entry(a,9))//32) if entry(a,9)[n*32:(n+1)*32]==colors]
        require(rows,'Active CLUT not found in source player palettes')
        wanted=entry(b,9)[rows[0]*32:(rows[0]+1)*32]
        require(all(entry(b,9)[n*32:(n+1)*32]==wanted for n in rows),'Ambiguous revised active palette')
        clut_sources[hex(clut)]=dict(source_palette_rows=rows,colors_sha256=sha(colors))
        return wanted
    def gpu_palette(clut):
        at=VR+(clut>>6)*2048+(clut&63)*32;colors=bytes(dst[at:at+32]);require(colors==target_palette(clut),'Active GPU palette differs');return colors
    expected_image=active_composite(decoded[1],counts[1],entry(b,3),target_palette,player)
    refreshed_image=active_composite(gpu_packed,counts[1],changed_ram[parts_at:parts_at+len(entry(b,3))],gpu_palette,player)
    require(refreshed_image.tobytes()==expected_image.tobytes(),'Refreshed active composite differs from target')
    for slot,(h,b,q) in target_banks.items():
        at=(cmds[slot]&0x1fffffff)-8;require(changed_ram[at:at+len(h)]==loaded_vab_header(h,b,starts[slot]),'Updated SDK VAB mismatch')
        require(dst[spu+starts[slot]:spu+starts[slot]+len(b)]==b,'Updated SPURAM mismatch')
    proof=dict(scope='User Nana progress preserved; source-authenticated asset cache refresh, not fresh disc loading',ram_offset=RP,vram_offset=VR,spu_state_offset=spu,player_sha256_before=sha(player),player_sha256_after=sha(changed_ram[0x1418c8:0x1418c8+228]),game_progress_region_sha256=sha(ram[0x1721c0:0x172220]),character=player[2],hp=player[0x5c],weapon=player[0x93],boss_flags=player[0xb9],armor=player[0xa7],ultimate=ram[0x1721f7],stage=ram[0x1721cc],area=ram[0x1721cd],frame=frame,world=[struct.unpack_from('<i',player,o)[0]/65536 for o in (8,12)],audio_banks=audio,replaced_wave_ranges=reclaimed,existing_voice_registers=current_voices,native_audio_sdk_checks=native,allowed_changes=changes,changed_bytes=sum(a!=b for a,b in zip(raw,dst)),all_nonasset_bytes_preserved=True,all_player_weapon_boss_progress_bytes_preserved=True,all_spu_playback_decoder_state_preserved=True,external_cards_opened=False,active_F1_modified=False,keys_sent=False,runtime_verified=False,limitations=['Current player palette changes are rejected until cache addresses are authenticated.','Future target changes outside supported resident resources require another audit.','Stage5/6/7 boss banks and title XA are reloaded from target disc when visited; current stage1 data and stream decoder state stay unchanged.'])
    proof['player_bank_layout']=bank_layout
    proof['active_frame_growth']=growth
    proof['active_composite_check']=dict(target_and_refreshed_rgba_sha256=sha(expected_image.tobytes()),size=list(expected_image.size),authenticated_clut_sources=clut_sources,exact_ram_gpu_parts_palette_composite=True,actual_game_framebuffer_test=False)
    return bytes(dst),proof

def main(a):
    out=a.output.resolve();target=a.target_bin.resolve()
    require(out.is_relative_to(ROOT/'work/overhaul_20261105/audio') and not out.exists(),'Fresh isolated output required')
    require(target.is_relative_to(ROOT/'out/ver_rin_nana') and digest(target)==a.target_sha,'Target BIN/hash mismatch')
    require(digest(SOURCE_STATE)==STATE_SHA and digest(SOURCE_BIN)==SOURCE_SHA,'Protected baseline differs')
    old,new=read_assets(SOURCE_BIN),read_assets(target);raw=gzip.decompress(SOURCE_STATE.read_bytes())
    result,proof=refresh(raw,old,new);require(refresh(raw,old,new)[0]==result,'Independent reproduction differs')
    rejected=[]
    tests=[('resident_sprite',RP+raw[RP:RP+0x200000].find(entry(old['PL02_U.ARC'],2))),('static_gpu',VR+176*2048+640),('vab_header',RP+0x1b2348+60+20),('sdk_wave_cache',RP+0x1b2348+60+32+6*16+12),('spu_body',proof['spu_state_offset']+315888+42768),('save_atlas',VR+256*2048+1792),('active_graphics_bank_pointer',RP+0x1418c8+0x38),('active_composition_bank_pointer',RP+0x1418c8+0x3c)]
    if proof['active_frame_growth']:
        tests.extend([('expanded_ram_tail_source',RP+0x16dea8+1920),('expanded_gpu_column_source',VR+760),('active_gpu_clut_source',VR+480*2048+2),('pending_gpu_upload_queue',RP+0x1659d0)])
    for label,at in tests:
        bad=bytearray(raw);bad[at]^=1
        try:refresh(bytes(bad),old,new)
        except (ValueError,AssertionError):rejected.append(label)
        else:raise AssertionError('Accepted invalid input '+label)
    for kind,index,label in ((2,3,'relocated_graphics_bank'),(3,1,'relocated_composition_bank')):
        bad=dict(new);arc=bytearray(new['PL02_U.ARC']);record=next(e for e in psx_arc(arc) if int(e['type'],16)==kind)
        pos=record['offset']+index*4;value=struct.unpack_from('<I',arc,pos)[0];struct.pack_into('<I',arc,pos,value+4);bad['PL02_U.ARC']=bytes(arc)
        try:refresh(raw,old,bad)
        except (ValueError,AssertionError):rejected.append(label)
        else:raise AssertionError('Accepted unsupported relocation '+label)
    out.mkdir(parents=True);dest=out/'SLUS_005.61.000';packed=gzip.compress(result,mtime=0)
    with dest.open('xb') as f:f.write(packed)
    require(gzip.decompress(dest.read_bytes())==result and digest(SOURCE_STATE)==STATE_SHA and digest(SOURCE_BIN)==SOURCE_SHA and digest(target)==a.target_sha,'Input/output preservation failed')
    proof.update(source_state=SOURCE_STATE.relative_to(ROOT).as_posix(),source_state_sha256=STATE_SHA,source_bin=SOURCE_BIN.relative_to(ROOT).as_posix(),source_bin_sha256=SOURCE_SHA,target_bin=target.relative_to(ROOT).as_posix(),target_bin_sha256=a.target_sha,output=dest.relative_to(ROOT).as_posix(),output_sha256=sha(packed),raw_output_sha256=sha(result),reproduced_identical=True,rejected_inputs=rejected)
    p=result[RP+0x1418c8:RP+0x1418c8+228];frame=graphics_bank(entry(new['PL02_U.ARC'],2),0,allow_bank_aliases=True)['frames'][p[0x47]]
    image=active_composite(result[RP+0x16dea8:RP+0x16dea8+frame['tile_count']*128],frame['tile_count'],entry(new['PL02_U.ARC'],3),lambda c:result[VR+(c>>6)*2048+(c&63)*32:VR+(c>>6)*2048+(c&63)*32+32],p)
    image.save(out/'active_composite_preview.png');proof['active_composite_check']['preview']='active_composite_preview.png'
    (out/'manifest.json').write_text(json.dumps(proof,indent=2),encoding='utf8')
    print(json.dumps({k:proof[k] for k in ('output','output_sha256','target_bin_sha256','changed_bytes','reproduced_identical','all_nonasset_bytes_preserved','rejected_inputs')}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--target-bin',type=Path,default=DEFAULT_TARGET);p.add_argument('--target-sha',default=DEFAULT_SHA);p.add_argument('--output',type=Path,required=True);main(p.parse_args())
