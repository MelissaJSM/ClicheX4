"""현재 BIN의 저장 그림과 캡슐 잔상을 수용된 플레이어 자원과 읽기 전용 대조한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from scripts.prepare_riko_ui import entry
from scripts.prepare_shibuki_ui import actual
from scripts.prepare_shibuki_ultimate_save_ui import render as ultimate_icon
from scripts.verify_shibuki_save_icon import icon,rgba
from scripts.prepare_shibuki_capsule_nova import raster,silhouette_frames
from scripts.prepare_nana_fourth_pilot import require,write
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import aliased_composition,local_composition

SOURCE_SHA='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
NAMES=('MOJIPAT.ARC','LOAD_U.ARC','PL00_U.ARC','PL01_U.ARC','PL02_U.ARC')

def read_assets(path,names=NAMES):
    with path.open('rb') as stream:
        disc=DiscReader(stream,path.stat().st_size)
        iso={q['path']:q for q in disc.inspect()['files']};assets={};records={}
        for name in names:
            q=iso['/ARC/'+name+';1'];assets[name]=disc.read(q['lba'],q['size']);records[name]=q
    return assets,records

def canvas(frame):
    pixels,size,bounds=frame[:3];a=np.frombuffer(pixels,np.uint8).reshape(size[1],size[0]);v=np.zeros((160,160),np.uint8)
    x,y,x2,y2=[i+80 for i in bounds];require(0<=x<x2<=160 and 0<=y<y2<=160,'Sprite exceeds audit canvas')
    v[y:y2,x:x2]=a;return v

def verify(assets,original):
    menu=assets['MOJIPAT.ARC'];tex=entry(assets['LOAD_U.ARC'],0x10008);po=struct.unpack_from('<I',menu,4)[0]
    base,rin,ult=[assets[n] for n in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC')]
    pairs=((8,entry(base,9)[:32]),(9,entry(base,9)[32:64]),(11,entry(base,9)[64:96]),(10,entry(rin,9)[:32]),(30,entry(ult,9)[32:64]),(31,entry(ult,9)[:32]))
    for row,pal in pairs:require(menu[po+row*32:po+(row+1)*32]==pal,f'Save palette {row} differs')
    expected_base=canvas(actual(base,0));layers={b:canvas(actual(base,0,b)) for b in (5,6,7,8)};pal=entry(base,9)
    checks=0;images={}
    for arm in (1,2):
        for mask in range(16):
            expected=np.array(struct.unpack_from('<16H',pal),np.uint16)[expected_base]
            for bit,b in ((1,5),(2,6),(4,7),(8,8)):
                if mask&bit:
                    colors=np.array(struct.unpack_from('<16H',pal,64 if b==7 and arm==2 else 32),np.uint16)
                    expected=np.where(layers[b],colors[layers[b]],expected)
            got=icon(menu,tex,mask,arm)
            for flip in (False,True):
                require(np.array_equal(got[:,::-1] if flip else got,expected[:,::-1] if flip else expected),'Fourth/base save differs');checks+=1
            images[f'fourth_{mask:02}_arm{arm}']=got
    base_layer=canvas(actual(ult,0));overlay=canvas(actual(ult,0,5));pal=entry(ult,9)
    for mask in range(16):
        expected=np.array(struct.unpack_from('<16H',pal),np.uint16)[base_layer]
        if mask:expected=np.where(overlay,np.array(struct.unpack_from('<16H',pal,32),np.uint16)[overlay],expected)
        got=ultimate_icon(menu,tex,mask)
        for flip in (False,True):
            require(np.array_equal(got[:,::-1] if flip else got,expected[:,::-1] if flip else expected),'Ultimate save differs');checks+=1
        images[f'ultimate_{mask:02}']=got
    rin_frame=canvas(compose_static(tex,local_composition(aliased_composition(menu,2,43))))
    require(np.array_equal(rin_frame,canvas(actual(rin,147))),'Rin save world pixels differ')
    images['rin']=np.array(struct.unpack_from('<16H',entry(rin,9)),np.uint16)[rin_frame]
    body=(base_layer>0)|(overlay>0);og,oc=entry(original,2),entry(original,3);g,c=entry(ult,2),entry(ult,3);cap=[]
    for gb in range(10,14):
        targets=silhouette_frames(og,oc,gb,gb+8,body)
        for n,want in enumerate(targets):
            got=raster(g,c,gb,gb+8,n);require(np.array_equal(got,want),f'Capsule {gb}:{n} differs from body/effect target');cap.append([gb,gb+8,n])
    return {'save_direction_equipment_combinations':checks,'rin_native_world_pixels_identical':True,'palette_rows':[r for r,_ in pairs],
            'capsule_references':len(cap),'capsule_original_particles_preserved':True,'capsule_body_matches_current_idle':True,
            'capsule_runtime_verified':False,'game_data_written':False},images

def main(build,out):
    build,out=build.resolve(),out.resolve()
    require(build.is_relative_to(ROOT/'out/ver_rin_nana') and out.is_relative_to(ROOT/'work/ver_rin_nana/nana_ultimate_armor') and not out.exists(),'Unexpected paths')
    manifest=json.loads((build/'manifest.json').read_text('utf8'));before=digest(build/'rin_nana.bin')
    require(manifest['task']=='ultimate_armor_nana' and before==manifest['modified_bin']['sha256'],'Unsupported or changed build')
    protection=json.loads((build/'preservation.json').read_text('utf8'))
    for q in protection['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed')
    original_path=ROOT/'MegaMan X4.bin';require(digest(original_path)==SOURCE_SHA,'Unsupported original')
    assets,records=read_assets(build/'rin_nana.bin');native,_=read_assets(original_path,('PL02_U.ARC',));proof,images=verify(assets,native['PL02_U.ARC'])
    for name,file in [('PL00_U.ARC','modified.arc'),('PL01_U.ARC','PL01_U.ARC'),('PL02_U.ARC','PL02_U.ARC')]:
        require(assets[name]==(build/file).read_bytes(),'Disc/sidecar resource differs')
    # Reject plausible palette, atlas and silhouette corruptions.
    rejected=[];menu=assets['MOJIPAT.ARC'];po=struct.unpack_from('<I',menu,4)[0]
    mutations=[('ultimate_palette','MOJIPAT.ARC',po+30*32+2),('rin_palette','MOJIPAT.ARC',po+10*32+2)]
    p=aliased_composition(menu,2,52)['parts'][0];mutations.append(('ultimate_anchor','MOJIPAT.ARC',p['record_offset']+2))
    for label,name,off in mutations:
        bad=dict(assets);v=bytearray(bad[name]);v[off]^=1;bad[name]=bytes(v)
        try:verify(bad,native['PL02_U.ARC'])
        except ValueError:rejected.append(label)
        else:raise AssertionError('Corrupt input accepted: '+label)
    require(digest(build/'rin_nana.bin')==before,'Build changed during audit')
    out.mkdir(parents=True);board=Image.new('RGB',(1200,330),'#253546');draw=ImageDraw.Draw(board)
    for i,name in enumerate(('rin','fourth_00_arm1','fourth_15_arm1','fourth_15_arm2','ultimate_00','ultimate_15')):
        im=rgba(images[name]);im.save(out/(name+'.png'));crop=im.crop(im.getbbox());large=crop.resize((crop.width*4,crop.height*4),Image.Resampling.NEAREST);board.paste(large,(i*200+30,50),large);draw.text((i*200+8,15),name,fill='white')
    board.save(out/'save_review.png');proof.update(build=build.relative_to(ROOT).as_posix(),bin_sha256=before,source_sha256=SOURCE_SHA,protected_files=len(protection['files']),rejected_corruptions=rejected,assets={n:{**records[n],'sha256':sha256(v)} for n,v in assets.items()})
    write(out/'verification.json',proof);print(json.dumps({'output':str(out),**{k:v for k,v in proof.items() if k!='assets'}}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.build,a.output)
