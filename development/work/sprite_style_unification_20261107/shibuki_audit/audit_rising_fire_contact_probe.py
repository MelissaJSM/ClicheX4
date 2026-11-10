"""원래 라이징 파이어 초기화 코드를 실행해 위치·효과 원형을 대조한다.

원화 후보의 접점 진단용이며 물리·게임 화면 전체를 실행했다는 뜻이 아니다.
"""
from pathlib import Path
import sys, struct, json, argparse
H=Path(__file__).resolve().parent; ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn.mips_const import UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3,UC_MIPS_REG_RA,UC_MIPS_REG_SP,UC_MIPS_REG_PC
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.export_sprite_playback import parse_sequence
from audit_cyclone_contact import translate,need,sha,write,SOURCE,SOURCE_SHA
from src.psx_disc import file_hash

def run(exe,arc,charged,subtype,facing):
    u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
    u.mem_map(0,0x200000);u.mem_map(0x1f800000,0x1000);u.mem_write(0x10000,exe[2048:])
    wr=lambda p,b:u.mem_write(p&0x1fffffff,b)
    obj,player,stop=0x801c0000,0x801418c8,0x801ff000
    gb,cb=0x80190000,0x801d0000
    wr(gb,arc.g[:64]);wr(cb,arc.c[:96])
    wr(0x1f800014,struct.pack('<I',gb));wr(0x1f80001c,struct.pack('<I',cb))
    wr(obj+2,bytes([subtype]));wr(player+0x15,bytes([facing]))
    wr(player+0xa,struct.pack('<H',1000));wr(player+0xe,struct.pack('<H',500))
    u.reg_write(UC_MIPS_REG_A0,obj);u.reg_write(UC_MIPS_REG_SP,0x801ff800);u.reg_write(UC_MIPS_REG_RA,stop)
    skipped=[];count=[0]
    def hook(uu,address,size,user):
        count[0]+=1;need(count[0]<2000,'Unexpected initializer loop')
        if address==stop:uu.emu_stop();return
        if address in(0x8001540c,0x8009547c,0x80095770):
            skipped.append({'address':hex(address),'args':[uu.reg_read(q)for q in(UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3)]})
            uu.reg_write(UC_MIPS_REG_PC,uu.reg_read(UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,hook)
    u.emu_start(0x80095538 if charged else 0x80095254,stop,count=2000)
    d=bytes(u.mem_read(obj&0x1fffffff,0xa0));x=struct.unpack_from('<H',d,10)[0]-1000;y=struct.unpack_from('<H',d,14)[0]-500
    need(struct.unpack_from('<I',d,0x38)[0]==gb+struct.unpack_from('<I',arc.g,20)[0],'Wrong native graphics bank')
    need(struct.unpack_from('<I',d,0x3c)[0]==cb+struct.unpack_from('<I',arc.c,52)[0],'Wrong native composition bank')
    return {'charged':charged,'subtype':subtype,'facing':facing,'spawn_world':[x,y],
            'flip_x':bool(d[0x15]&64),'animation':d[0x17],'initial_ref':d[0x47],
            'native_instruction_count':count[0],'isolated_calls':skipped,
            'tpage':hex(struct.unpack_from('<H',d,0x40)[0]),'clut':hex(struct.unpack_from('<H',d,0x42)[0])}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--corrected104',action='store_true');args=ap.parse_args()
    out=H/('rising_fire_contact_probe02'if args.corrected104 else'rising_fire_contact_probe01');need(not out.exists(),'Fresh output required');out.mkdir()
    need(file_hash(SOURCE)==SOURCE_SHA,'Wrong baseline BIN')
    exe=read_disc(SOURCE,['SLUS_005.61'])[0]['SLUS_005.61']
    orig=(ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z/original.exe').read_bytes()
    off=lambda x:x-0x80010000+2048
    ranges=[(0x800951c0,0x800957b0),(0x8010890c,0x80108944),(0x8011ba28,0x8011bb3c),(0x8011c0b0,0x8011c0c8)]
    for x,y in ranges:need(exe[off(x):off(y)]==orig[off(x):off(y)],'Native rising-fire code/table changed')
    arcpath=H/'prepared_double_cyclone_base01/PL00_U.ARC';arc=Archive(arcpath.read_bytes())
    need(sha(arc.data)=='61495a2aaf002efc32492a4e12c3724a77c82b3f42464538ae1e2cc855da74c0','Parent changed')
    cases=[run(exe,arc,c,s,f)for c in(False,True)for s in(0,1)for f in(0,64)]
    sequences={str(c['animation']):parse_sequence(exe,0x8011c0b0,c['animation'])for c in cases}
    effects=[]
    for c in cases:
        for step in sequences[str(c['animation'])]['steps']:
            n=step['frame_ref']
            if any(e['charged']==c['charged']and e['subtype']==c['subtype']and e['facing']==c['facing']and e['ref']==n for e in effects):continue
            idx,_=arc.layer(n,13,5)
            effects.append(c|{'ref':n,'index_sha256':sha(idx.tobytes()),'opaque':int((idx>0).sum())})
    fonts=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13);panels=[];contacts=[]
    # Normal release occurs on player232 or104; charged first visible flame samples are
    # shown with100/101 solely as a spatial probe, not an asserted frame-phase simulation.
    for charged,subtype,bodyref in[(False,0,232),(False,1,104),(True,0,100),(True,1,101)]:
        c=next(c for c in cases if(c['charged'],c['subtype'],c['facing'])==(charged,subtype,0))
        seq=sequences[str(c['animation'])]
        refs=list(dict.fromkeys(s['frame_ref']for s in seq['steps']))
        nonempty=[n for n in refs if np.any(arc.layer(n,13,5)[0])]
        sample=nonempty[0];eff=translate(arc.layer(sample,13,5)[0],*c['spawn_world'],c['flip_x'])
        for form,mask,pal in[('base',0,0),('fourth',15,16)]:
            source=H/f'rising_fire_native{"01"if bodyref in(100,101)else"02"}/{form}_{231 if bodyref==232 else bodyref:03}_indices.png'
            if args.corrected104 and bodyref==104:source=H/f'rising104_arm_native02/{form}_104_indices.png'
            idx=np.array(Image.open(source));idx=np.roll(idx,1,axis=0)if bodyref==232 else idx
            for version,body in[('old',arc.composite(bodyref,mask)[0]),('new',arc.rgba(idx,pal))]:
                b=np.array(body);hand=np.zeros((384,384),bool);hand[126:148,137:153]=True;hand&=b[:,:,3]>0
                hp=np.column_stack(np.nonzero(hand));ep=np.column_stack(np.nonzero(eff))
                distance=float(np.sqrt(((hp[:,None,:]-ep[None,:,:])**2).sum(2).min()))if len(hp)and len(ep)else None
                yy,xx=np.indices(hand.shape)
                skin=((np.all(b[:,:,:3]==[238,164,131],axis=2))|np.all(b[:,:,:3]==[255,222,189],axis=2))&(b[:,:,3]>0)&(xx<152)&(yy<142)
                sp=np.column_stack(np.nonzero(skin))
                skin_distance=float(np.sqrt(((sp[:,None,:]-ep[None,:,:])**2).sum(2).min()))if len(sp)and len(ep)else None
                contacts.append({'charged':charged,'subtype':subtype,'body_ref':bodyref,'form':form,'version':version,
                                 'effect_ref':sample,'body_effect_overlap':int(((b[:,:,3]>0)&(eff>0)).sum()),
                                 'upper_left_region_effect_distance':distance,'hand_region_includes_sleeve_and_hair':True,
                                 'fist_skin_pixels':int(skin.sum()),'fist_skin_effect_distance':skin_distance,
                                 'fist_skin_effect_overlap':int((skin&(eff>0)).sum())})
                overlay=body.copy();rgba=np.zeros((384,384,4),np.uint8);rgba[eff>0]=[45,220,235,180];overlay.alpha_composite(Image.fromarray(rgba))
                crop=overlay.crop((120,104,200,192)).resize((320,352),Image.Resampling.NEAREST)
                panel=Image.new('RGB',(320,390),(27,32,43));panel.paste(crop,(0,38),crop);d=ImageDraw.Draw(panel)
                d.text((4,3),f'{form} {bodyref} {version} / effect{sample}',font=fonts,fill='white')
                d.text((4,20),'cyan occupancy; charged phase not simulated',font=fonts,fill='white');panels.append(panel)
    board=Image.new('RGB',(1280,1560),(27,32,43))
    for i,p in enumerate(panels):board.paste(p,(i%4*320,i//4*390))
    board.save(out/'contact_spatial_probe.png')
    write(out/'report.json',{'native_initializer_passed':True,'source_exe_sha256':sha(exe),'source_arc_sha256':sha(arc.data),
          'original_native_ranges_exact':[list(map(hex,r))for r in ranges],'cases':cases,'sequences':sequences,'effects':effects,'contacts':contacts,
          'graphics_bank':5,'composition_bank':13,'normal_release_player_refs':[232,104],
          'charged_position_policy':'초기 원점은 플레이어 원점과 같고 상승 동안 매 갱신 복사. 0x67 복귀로 바뀐 뒤 분리 이동한다.',
          'limitations':['원래 초기화 MIPS/애니메이션 설정을 실행했고 draw·외부 생성 경계만 격리했다.',
                         'charge 이펙트/플레이어 프레임의 상대 갱신 위상은 아직 검증 전이다. 이 합성을 실기나 정확한 연속 재생으로 주장하지 않는다.',
                         '청록색은 실제 효과 알파 위치의 진단색이며 현재 무기 CLUT 실기 색상이 아니다.'],
          'corrected104':args.corrected104,'native_gameplay_test':False,'candidate_accepted':False,'game_or_exe_written':False})
    print(json.dumps({'cases':cases,'contacts':contacts}))
if __name__=='__main__':main()
