"""Read-only full-cycle Nana reference/constraint package before new artwork."""
from pathlib import Path
import sys,json,hashlib,struct
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT),str(Path(__file__).parent/'native_restore')]
from preview_restore import data,Archive,sha,digest,write,need,EXPECTED,SOURCE
from src.psx_player import composition_frame,decode_stream,bank_offsets
from scripts.export_x_consistency import animation_map
from PIL import Image,ImageDraw,ImageFont
import numpy as np
D=Path(__file__).parent/'base_run_repaint'
RUN_PAGES=[[1,7,15,25],[3,5,9,11],[13,17,19,21],[23,27,29,31]]
SHOT_PAGES=[[2,12,26,32],[4,6,8,10],[14,16,18,20],[22,24,28,30]]

def page(a,refs,path,title):
 font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',24);board=Image.new('RGB',(1536,1648),(181,193,201));draw=ImageDraw.Draw(board)
 for i,n in enumerate(refs):
  im=a.composite(n,0)[0];v=np.array(im.getchannel('A'));v[112:208,112:208]=0;need(not v.any(),'Reference clipped');p=im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST);x=i%2*768;y=i//2*824;board.paste(p,(x,y+56),p);draw.text((x+10,y+10),title+' / '+str(n),font=font,fill='#172430')
 board.save(path)

def main():
 assets,records=data();D.mkdir(exist_ok=True);(D/'inputs').mkdir(exist_ok=True);a=Archive(assets['PL00_U.ARC']);(D/'baseline_PL00_U.ARC').write_bytes(a.data);(D/'baseline_palette.bin').write_bytes(a.p)
 old=ROOT/'work/ver_rin_nana/nana_art/run_v1';art=json.loads((old/'normalized05/art.json').read_text('utf8'));pairs=json.loads((old/'paired06/pairs.json').read_text('utf8'));frames=[]
 for n in range(1,33):
  pix=a.layer(n)[0];previous=old/'paired06'/f'{"run"if n%2 else"shoot"}_{n if n%2 else n-1:03}.png';need(np.array_equal(np.array(Image.open(previous)),pix[120:200,112:208]),'Historical registration drift');d=a.banks[0]['frames'][n];ar=next(q for q in art['frames']if q['frame']==(n if n%2 else n-1));pr=next(q for q in pairs['frames']if q['run']==(n if n%2 else n-1));ey,ex=np.nonzero((pix==14)&(np.indices(pix.shape)[0]<160));y,x=np.nonzero(pix);foot_y=int(y.max()-160)
  frames.append({'ref':n,'run_partner':n if n%2 else n-1,'bbox_world':[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)],'eye_world_original_registration':[ar['eye'][0]-48,ar['eye'][1]-40],'eye_world_visible':[float(np.median(ex)-160),float(np.median(ey)-160)]if len(ex)else None,'foot_max_y':foot_y,'original_muzzle':pr['original_muzzle'],'registered_arm_bounds_96x80':pr['registered_arm_bounds'],'tile_count':d['tile_count'],'stream_aliases':[q['index']for q in a.banks[0]['frames']if q['offset']==d['offset']],'base_tile_ids':sorted({p['tile']for p in composition_frame(a.c,0,n)['parts']}),'armor_tile_ids':sorted({p['tile']for pb in(5,6,7,8)for p in composition_frame(a.c,pb,n)['parts']}),'base_part_count':len(composition_frame(a.c,0,n)['parts']),'current_indexed_sha256':sha(pix.tobytes()),'historical_registered_sha256':digest(previous)})
  Image.fromarray(pix).save(D/'inputs'/f'current_indexed_{n:03}.png');a.composite(n,0)[0].save(D/'inputs'/f'current_rgba_{n:03}.png')
 pages=[]
 for kind,sets in [('run',RUN_PAGES),('shot',SHOT_PAGES)]:
  for i,refs in enumerate(sets):
   path=D/'inputs'/f'{kind}_page{i+1}.png';page(a,refs,path,'보행'if kind=='run'else'이동사격');pages.append({'kind':kind,'refs':refs,'path':path.relative_to(ROOT).as_posix(),'sha256':digest(path)})
 plan={'project':'ver_rin_nana','source_bin':SOURCE.relative_to(ROOT).as_posix(),'source_sha256':EXPECTED,'source_arc_sha256':sha(a.data),'source_palette_sha256':sha(a.p),'frames':frames,'pages':pages,'native_canvas':[384,384],'native_origin':[160,160],'image_page_cell':[96,96],'image_page_scale':8,'scope':'기본 나나 보행/이동사격1..32 재작화. 포스 레이어는 후속 차례에 다루되 현재모든부분조합을 회귀 검토한다.','fixed':['사용자 수용 대기0/115..119와정지85는기준으로보존','CLUT색16개/타일최대32','원래보행타이밍/판정/총구/발접점','의상정체성:분홍머리/검정베레/초록눈/비대칭스타킹/사랑이'],'forbidden':['옛단순머리를새원화위에재덮기','팔/소매스트립가로늘리기','대표4포즈만수정하고전체완료로보고','새그림의중간명암을슬롯절약만을위해일괄제거'],'new_art_generated':False}
 write(D/'plan.json',plan);print(json.dumps({'directory':str(D),'references':len(frames),'pages':len(pages),'current_equals_retained_registration':32}))

if __name__=='__main__':main()
