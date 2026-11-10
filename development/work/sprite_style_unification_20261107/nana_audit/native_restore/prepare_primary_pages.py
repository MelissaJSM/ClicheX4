"""Four large, origin-preserving native references for the next Nana artwork."""
from preview_restore import *
from PIL import ImageDraw,ImageFont

def main():
 assets,_=data();a=Archive(assets['PL00_U.ARC']);directory=OUT/'primary_art_inputs';directory.mkdir(exist_ok=True);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',26);manifest={'parent_sha256':EXPECTED,'arc_sha256':sha(a.data),'scale':8,'cell_native':[96,96],'origin_in_cell':[48,48],'world_window':[-48,-48,48,48],'images':[],'new_art_generated':False}
 groups=[('01_run_four_poses.png',[1,7,15,25],'나나 기본 보행'),('02_firing_four_poses.png',[2,12,26,32],'나나 기본 이동사격'),('03_idle_master.png',[0],'나나 현재 대기 기준'),('04_standing_fire_master.png',[85],'나나 현재 정지사격')]
 for filename,refs,title in groups:
  cols=2 if len(refs)>1 else 1;rows=(len(refs)+cols-1)//cols;board=Image.new('RGB',(cols*768,rows*824),(181,193,201));draw=ImageDraw.Draw(board);records=[]
  for i,n in enumerate(refs):
   im=a.composite(n,0)[0];crop=im.crop((112,112,208,208));outside=np.array(im.getchannel('A'));outside[112:208,112:208]=0;need(not outside.any(),'Reference crop clips art');pic=crop.resize((768,768),Image.Resampling.NEAREST);x,y=i%cols*768,i//cols*824;board.paste(pic,(x,y+56),pic);draw.text((x+12,y+10),f'{title} / ref {n}',font=font,fill='#142432');draw.line((x,y,x+767,y),fill='#617886');draw.line((x,y,x,y+823),fill='#617886');records.append({'ref':n,'rgba_sha256':sha(im.tobytes()),'native_crop_sha256':sha(crop.tobytes()),'all_opaque_pixels_present':True})
  p=directory/filename;board.save(p);manifest['images'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'references':records})
 write(directory/'manifest.json',manifest);print(json.dumps({'path':directory.relative_to(ROOT).as_posix(),'images':4}))

if __name__=='__main__':main()
