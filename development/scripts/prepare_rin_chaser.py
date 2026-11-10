"""수용 대기와 원작 체이서 네 기울기를 공통 축척 제작 안내로 추출한다."""
import json,struct,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_rin_idle import entry,sha
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch
OUT=ROOT/'work/ver_rin_nana/ride_chaser/v1'
PARENT=ROOT/'out/ver_rin_nana/rin_ride_heads_20261029T003329979054Z'
ORIGINAL=ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z/original.arc'

def main():
    if OUT.exists():raise ValueError('Chaser guide already exists')
    pm=json.loads((PARENT/'manifest.json').read_text('utf-8'));arc=(PARENT/'modified.arc').read_bytes();old=ORIGINAL.read_bytes()
    if sha(arc)!=pm['modified_archive_sha256']:raise ValueError('Parent changed')
    OUT.mkdir(parents=True);g=entry(arc,2)[1];parts=entry(arc,3)[1];pal=struct.unpack_from('<16H',entry(arc,9)[1]);ow=struct.unpack_from('<16H',entry(old,9)[1])
    idle=Image.open(ROOT/'work/ver_rin_nana/style_revision/v4_special/master_preview_147.png').convert('RGBA');idle=idle.crop(idle.getbbox());idle.resize((idle.width*10,idle.height*10),Image.Resampling.NEAREST).save(OUT/'approved_reference.png')
    slots=[None,14,22,30,38,None];template=Image.new('RGBA',(288,192));poses=Image.new('RGBA',template.size);frames={}
    for n in range(14,50):
        f=graphics_bank(g,1)['frames'][n];c=composition_frame(parts,5,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        rec={'parts':c['parts'],'tile_count':f['tile_count'],'stream_offset':f['offset'],'raw_sha256':sha(raw)}
        if n<42:
            px,sz,b,_=compose_launch(raw,f['tile_count'],c);save_image(px,sz,ow,OUT/f'original_{n}.png');rec.update(bounds=b,size=sz)
        frames[str(n)]=rec
    for i,n in enumerate(slots):
        cx=i%3*96+48;cy=i//3*96+48
        template.alpha_composite(idle,(cx-idle.width//2,cy-24))
        if n is None:poses.alpha_composite(idle,(cx-idle.width//2,cy-24))
        else:
            im=Image.open(OUT/f'original_{n}.png').convert('RGBA');b=frames[str(n)]['bounds'];poses.alpha_composite(im,(cx+b[0],cy+b[1]))
    for name,im in [('template',template),('poses',poses)]:im.resize((im.width*6,im.height*6),Image.Resampling.NEAREST).save(OUT/f'{name}.png')
    m={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':pm['modified_bin']['sha256'],'parent_arc_sha256':sha(arc),'original_arc_sha256':sha(old),'palette_words':pal,'frames':frames,'slots':slots,'columns':3,'rows':2,'calibration_height':idle.height}
    (OUT/'guide.json').write_text(json.dumps(m,indent=2)+'\n','utf-8');print(json.dumps({'output':str(OUT),'slots':slots,'calibration_height':idle.height}))

if __name__=='__main__':main()
