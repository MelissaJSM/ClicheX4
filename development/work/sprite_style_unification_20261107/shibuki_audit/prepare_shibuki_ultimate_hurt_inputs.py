"""새 기본 피격 포즈를 유지하는 Ultimate 의상 편집 입력. 원자료 쓰기 없음."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',type=int,choices=(1,2),default=1);args=ap.parse_args();pageid=args.page;refs=(106,110)if pageid==1 else(233,234)
    d=H/f'ultimate_hurt_inputs01/page{pageid:02}';need(not d.exists(),'Fresh inputs');d.mkdir(parents=True)
    p=H/'prepared_ultimate_ladder01/PL02_U.ARC';need(sha(p.read_bytes())=='03a675626035b93ad2e2feef8dd643365ed8a3e1a61a1eb02a476063e2c55e8a','Parent changed');a=Archive(p.read_bytes())
    source=H/f'hurt_inputs01/page{pageid:02}/generated.png';expected='cd9f9509e583b3cc2690251a963ba8f55f9d07946957345bc57043c1eb9d903f'if pageid==1 else'be3172a16a3ab46f34f8facc3be92f8ca85e07b3b06e18684df08d5f41244772';need(sha(source.read_bytes())==expected,'New pose art changed');original=Image.open(source).convert('RGBA');need(original.size==(1536,1024),'Exact source size');target=Image.new('RGBA',original.size)
    target.alpha_composite(original.crop((0,0,1536,512)),(0,0));target.alpha_composite(original.crop((0,0,1536,512)),(0,512));target.save(d/'edit_target.png')
    style=Image.new('RGBA',(1536,1024));current=Image.new('RGBA',(1536,1024));rows=[]
    for row,(form,mask)in enumerate((('before',15),('after',0))):
        for col,n in enumerate((0,120,55)):
            im=a.composite(n,mask)[0];style.alpha_composite(im.crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
        for col,n in enumerate(refs):
            im=a.composite(n,mask)[0];cut=im.crop((112,128,208,192));need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]),'Current source clips');current.alpha_composite(cut.resize((768,512),Image.Resampling.NEAREST),(col*768,row*512));rows.append({'form':form,'ref':n,'old_metrics':metrics(im),'source_rgba_sha256':sha(im.tobytes())})
    style.save(d/'accepted_ultimate_style.png');current.save(d/'old_coordinate_reference.png')
    write(d/'input.json',{'intent':'새 기본 피격 관절을 유지한 Ultimate 의상 편집, 옛 몸/머리 덮기 아님','refs':list(refs),'parent_path':p.relative_to(ROOT).as_posix(),'parent_sha256':sha(p.read_bytes()),'pose_art_path':source.relative_to(ROOT).as_posix(),'pose_art_sha256':sha(source.read_bytes()),'edit_target_sha256':sha((d/'edit_target.png').read_bytes()),'source_layout':{'size':[1536,1024],'cell':[768,512],'native_cell':[96,64],'native_origin':[48,32],'scale':0.125,'crop':[112,128,208,192]},'styles':[0,120,55],'rows':rows,'arc_changed':False})
    print(d.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
