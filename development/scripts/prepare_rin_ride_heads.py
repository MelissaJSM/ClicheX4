"""원작 탑승 머리의 공유 관계를 추출하고 승인 린 머리와 비교 시트를 만든다."""
import json,struct,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_rin_idle import entry,sha
from scripts.extract_zero import save_image
from scripts.project import digest
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch
OUT=ROOT/'work/ver_rin_nana/ride_armor_head/v2'
PARENT=ROOT/'out/ver_rin_nana/rin_personal_effects_20261029T002211975515Z'

def main():
    if OUT.exists():raise ValueError('Head work already exists')
    pm=json.loads((PARENT/'manifest.json').read_text('utf-8'));a=(PARENT/'modified.arc').read_bytes();original=(ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z/original.arc').read_bytes()
    if sha(a)!=pm['modified_archive_sha256']:raise ValueError('Changed accepted parent')
    OUT.mkdir(parents=True);g=entry(a,2)[1];p=entry(a,3)[1];words=struct.unpack_from('<16H',entry(a,9)[1]);ow=struct.unpack_from('<16H',entry(original,9)[1]);seen={};frames={};unique=[];pictures={}
    for n in range(66,86):
        f=graphics_bank(g,1)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;c=composition_frame(p,5,n);px,sz,b,_=compose_launch(raw,f['tile_count'],c);key=(px,sz)
        if sz!=(16,16) or len(c['parts'])!=1:raise ValueError('Unexpected head geometry')
        if not any(px):seen[key]=None
        elif key not in seen:seen[key]=n;unique.append(n);pictures[n]=save_image(px,sz,ow,OUT/f'original_{n}.png').convert('RGBA')
        frames[str(n)]={'source':seen[key],'parts':c['parts'],'bounds':b,'stream_offset':f['offset'],'tile_count':f['tile_count'],'original_decoded_sha256':sha(raw)}
    slots=[None,*unique];cols=3;rows=(len(slots)+2)//3;slots += [None]*(cols*rows-len(slots));idle=Image.open(ROOT/'work/ver_rin_nana/style_revision/v4_special/master_preview_147.png').convert('RGBA');head=idle.crop((13,0,29,16));head.save(OUT/'approved_head_reference.png')
    template=Image.new('RGBA',(cols*48,rows*48));poses=Image.new('RGBA',template.size);labels=Image.new('RGB',template.size,(34,37,47));d=ImageDraw.Draw(labels)
    for i,n in enumerate(slots):
        x=i%cols*48+16;y=i//cols*48+16;template.alpha_composite(head,(x,y));poses.alpha_composite(head if n is None else pictures[n],(x,y));d.text((i%cols*48+2,i//cols*48+2),str(n),fill='white')
    for name,im in [('template',template),('poses',poses)]:im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST).save(OUT/f'{name}.png')
    labels.paste(poses,(0,0),poses);labels.resize((labels.width*8,labels.height*8),Image.Resampling.NEAREST).save(OUT/'guide.png')
    m={'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':pm['modified_bin']['sha256'],'parent_arc_sha256':sha(a),'original_arc_sha256':sha(original),'palette_words':words,'frames':frames,'unique':unique,'slots':slots,'columns':cols,'rows':rows,'reference':'work/ver_rin_nana/style_revision/v4_special/master_preview_147.png','reference_sha256':digest(ROOT/'work/ver_rin_nana/style_revision/v4_special/master_preview_147.png')}
    (OUT/'guide.json').write_text(json.dumps(m,indent=2)+'\n','utf-8');print(json.dumps({'unique':unique,'slots':slots,'references':len(frames)}))

if __name__=='__main__':main()
