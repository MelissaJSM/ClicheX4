"""새 정면 원화의 금색 홍채2셀이 다수결 축소로 피부색이 되는 현상 대조."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash
from restore_remaining_sources import clean

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);d=H/'front156_generation02';p=d/'native01/base_156_indices.png';base=np.array(Image.open(p));new=base.copy();reg=json.loads((d/'native01/registration.json').read_text('utf8'))['records'][0]
 source=clean(Image.open(d/'generated.png').convert('RGBA').crop((0,0,768,1024)));z=np.array(source);colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[1:16]],np.int32);nearest=np.zeros(z.shape[:2],np.uint8)
 for y in range(len(z)):nearest[y]=np.argmin(((z[y,:,:3].astype(np.int32)[:,None]-colors[None])**2).sum(2),axis=1)+1
 size=(round(source.width*reg['uniform_scale']),round(source.height*reg['uniform_scale']));gold=np.array(Image.fromarray(np.where(nearest==7,z[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX));dx,dy=reg['translation'];records=[]
 for wx,wy in((-2,-9),(3,-9)):
  x,y=wx+160,wy+160;vote=int(gold[y-dy,x-dx]);need(base[y,x]==12 and vote>=20,'Source eye registration changed');new[y,x]=7;records.append({'world':[wx,wy],'before_index':12,'after_index':7,'source_gold_alpha_vote_of255':vote,'source_gold_palette_word':int(a.words[7]),'native_cell_source_rect_approx':[(x-dx)/size[0]*source.width,(y-dy)/size[1]*source.height,(x-dx+1)/size[0]*source.width,(y-dy+1)/size[1]*source.height]})
 out=d/'iris_probe';out.mkdir(exist_ok=False);Image.fromarray(new).save(out/'base_156_indices.png');a.rgba(new).save(out/'base_156.png');page([('before BOX majority',a.rgba(base)),('new source iris material',a.rgba(new))],a.composite(0,0)[0],out/'comparison.png',cols=2,scale=8)
 write(out/'provenance.json',{'source_art_sha256':sha((d/'generated.png').read_bytes()),'registered_base_sha256':sha(p.read_bytes()),'changes':records,'changed_texels':int(np.count_nonzero(base!=new)),'geometry_alpha_palette_bytes_unchanged':True,'old_head_or_face_used':False,'no_game_packing':True,'scope':'새 원화 홍채 재질의 팔레트 분류 비교. 부분 의상 정합은 아직 별도 미완료.'})
if __name__=='__main__':main()
