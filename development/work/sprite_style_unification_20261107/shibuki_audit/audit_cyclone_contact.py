"""실제 EXE initializer의 발원점과 원본 효과 마스크를 새 손에 대조한다.

에뮬레이터/게임 입력 없음. MIPS의 draw/spawn 외부 경계만 격리하며
생성 위치/방향/초기 애니메이션 설정은 원래 명령을 실행한다.
"""
from pathlib import Path
import sys,struct,json,hashlib,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn.mips_const import UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3,UC_MIPS_REG_RA,UC_MIPS_REG_SP,UC_MIPS_REG_PC
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.export_sprite_playback import parse_sequence
from src.psx_disc import file_hash
SOURCE=ROOT/'out/ver_buki_riko/sprite_reaudit_20261106_v1/shibuki_riko.bin'
SOURCE_SHA='21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a'
def need(ok,s):
    if not ok:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')

def run(exe,arc,charged,subtype,facing):
    u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,0x1000);u.mem_write(0x10000,exe[2048:]);wr=lambda p,b:u.mem_write(p&0x1fffffff,b)
    obj,player,stop=0x801c0000,0x801418c8,0x801ff000
    gb,cb=0x80190000,0x801d0000
    # Only bank directories are read by the initializer; the actual native offsets are retained.
    wr(gb,arc.g[:64]);wr(cb,arc.c[:96]);wr(0x1f800014,struct.pack('<I',gb));wr(0x1f80001c,struct.pack('<I',cb))
    wr(obj+2,bytes([subtype&255]));wr(player+0x15,bytes([facing]));wr(player+0xa,struct.pack('<H',1000));wr(player+0xe,struct.pack('<H',500))
    u.reg_write(UC_MIPS_REG_A0,obj);u.reg_write(UC_MIPS_REG_SP,0x801ff800);u.reg_write(UC_MIPS_REG_RA,stop)
    skipped=[];count=[0]
    def hook(uu,address,size,user):
        count[0]+=1;need(count[0]<2000,'Unexpected initializer loop')
        if address==stop:uu.emu_stop();return
        if address in (0x8001540c,0x80097328,0x800977d4,0x8002b318):
            skipped.append({'address':hex(address),'args':[uu.reg_read(q)for q in(UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3)]})
            uu.reg_write(UC_MIPS_REG_PC,uu.reg_read(UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x80097430 if charged else 0x80096ea4,stop,count=2000)
    d=bytes(u.mem_read(obj&0x1fffffff,0xa0));x,y=struct.unpack_from('<H',d,10)[0]-1000,struct.unpack_from('<H',d,14)[0]-500
    need(struct.unpack_from('<I',d,0x38)[0]==gb+struct.unpack_from('<I',arc.g,32)[0],'Wrong native gfx bank')
    need(struct.unpack_from('<I',d,0x3c)[0]==cb+struct.unpack_from('<I',arc.c,64)[0],'Wrong native composition bank')
    return {'charged':charged,'subtype':subtype,'player_facing_flag':facing,'spawn_world':[x,y],'flip_x':bool(d[0x15]&64),'animation':d[0x17],'initial_frame':d[0x47],'tpage':hex(struct.unpack_from('<H',d,0x40)[0]),'clut':hex(struct.unpack_from('<H',d,0x42)[0]),'instruction_count':count[0],'isolated_calls':skipped}

def translate(a,dx,dy,flip=False):
    b=np.zeros_like(a);yy,xx=np.nonzero(a);wx=xx-160
    if flip:wx=-wx-1
    nx=160+wx+dx;ny=yy+dy;need((nx>=0).all()and(nx<384).all()and(ny>=0).all()and(ny<384).all(),'Effect outside canvas');b[ny,nx]=a[yy,xx];return b

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',choices=('01','02'),default='01');args=ap.parse_args();expected={'01':'0ff7d79339627e01cf1a7d59e42c392640cce4c350fa82f7db55772b623a0454','02':'61495a2aaf002efc32492a4e12c3724a77c82b3f42464538ae1e2cc855da74c0'}[args.version]
    out=H/f'double_cyclone_contact{args.version}'
    if out.exists()and not any(out.iterdir()):out.rmdir()
    need(not out.exists(),'Fresh output required');out.mkdir()
    need(file_hash(SOURCE)==SOURCE_SHA,'Wrong source BIN');exe=read_disc(SOURCE,['SLUS_005.61'])[0]['SLUS_005.61'];need(sha(exe)=='93a8f0cab28034bd7d5b93fe4362c7c56c8c2bfba5ccb764e7bf547a02ae1616','Wrong EXE')
    orig=(ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z/original.exe').read_bytes();off=lambda v:v-0x80010000+2048
    for start,end in[(0x80096ea4,0x80097048),(0x80097430,0x800975dc),(0x801089bc,0x801089fc),(0x8011bc20,0x8011bccc),(0x80015d60,0x80015dc8)]:need(exe[off(start):off(end)]==orig[off(start):off(end)],'Native cyclone changed')
    parent=Archive((H/'prepared_air01/PL00_U.ARC').read_bytes());candidate=Archive((H/f'double_cyclone_base_pack{args.version}/PL00_U.ARC').read_bytes());need(sha(candidate.data)==expected,'Candidate changed')
    # Nonzero indices define native effect occupancy. Display them in cyan solely for contact review;
    # a runtime weapon CLUT/color match is deliberately not claimed.
    cases=[run(exe,parent,charged,st,f)for charged in(False,True)for st in((0,-128)if charged else(0,1))for f in(0,64)]
    cases=[dict(c,initial_index_sha256=sha(parent.layer(c['initial_frame'],16,8)[0].tobytes()))for c in cases]
    rows=[];panels=[];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
    for charged in(False,True):
        cc=[c for c in cases if c['charged']==charged and c['player_facing_flag']==0];effects=[]
        for c in cc:
            seq=parse_sequence(exe,0x8011c0f0,c['animation']);frames=list(dict.fromkeys(s['frame_ref']for s in seq['steps']))
            for n in frames:
                arr,_=parent.layer(n,16,8);need(np.array_equal(arr,candidate.layer(n,16,8)[0]),'Effect pixels changed');effects.append((c,n,translate(arr,*c['spawn_world'],c['flip_x'])))
        for mask in(0,15):
            for ref in(98,99):
                for version,a in(('old',parent),('new',candidate)):
                    body=a.composite(ref,mask)[0];b=np.array(body);points=[]
                    for side in('left','right'):
                        hand=np.zeros((384,384),bool);hand[148:164,134:146] = True if side=='left' else False
                        if side=='right':hand[148:164,177:186]=True
                        hand&=b[:,:,3]>0
                        subset=[(c,n,e)for c,n,e in effects if(c['spawn_world'][0]<0)==(side=='left')]
                        for c,n,e in subset:
                            overlap=int((hand&(e>0)).sum());hp=np.column_stack(np.nonzero(hand));ep=np.column_stack(np.nonzero(e));dist=float(np.sqrt(((hp[:,None,:]-ep[None,:,:])**2).sum(2).min()));points.append({'side':side,'effect_ref':n,'initial':n==c['initial_frame'],'hand_overlap_pixels':overlap,'nearest_hand_to_effect_distance':dist})
                    row={'charged':charged,'mask':mask,'ref':ref,'version':version,'contacts':points};rows.append(row)
                    composite=body.copy()
                    for c,n,e in effects:
                        if n!=c['initial_frame']:continue
                        rgba=np.zeros((384,384,4),np.uint8);rgba[e>0]=[60,220,230,175];composite.alpha_composite(Image.fromarray(rgba))
                    crop=composite.crop((124,124,200,192)).resize((380,340),Image.Resampling.NEAREST);panel=Image.new('RGB',(380,374),(27,32,43));panel.paste(crop,(0,34),crop);draw=ImageDraw.Draw(panel);draw.text((6,3),f'{"charge"if charged else"normal"} mask{mask:X} ref{ref} {version}',font=font,fill='white');draw.text((6,18),'Cyan: native initial effect mask, diagnostic color',font=font,fill='white');panels.append(panel)
    board=Image.new('RGB',(380*4,374*4),(27,32,43))
    for i,p in enumerate(panels):board.paste(p,(i%4*380,i//4*374))
    board.save(out/'initial_effect_overlay.png')
    write(out/'report.json',{'passed':True,'source_exe_sha256':sha(exe),'parent_arc_sha256':sha(parent.data),'candidate_sha256':sha(candidate.data),'native_initializers_executed':len(cases),'cases':cases,'effect_graphics_bank':8,'effect_composition_bank':16,'rows':rows,'scope':'원본 초기화 MIPS의 발원점·방향·첫참조 + 실제 원본 이펙트 인덱스 마스크. 플레이어 상태/물리/그리기 전체 시뮬레이션 아님.','visual_effect_color':'접점용 청록색 진단색. 실제 장착 무기 CLUT 색상 검증 아님.','runtime_verified':False,'external_calls_isolated':True,'game_or_effect_data_changed':False})
    print(json.dumps({'cases':len(cases),'initial_contacts':[{k:v for k,v in r.items()if k!='contacts'}|{'contacts':[x for x in r['contacts']if x['initial']]}for r in rows]},ensure_ascii=False))
if __name__=='__main__':main()
