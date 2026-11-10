"""71/75 낮은 두 발만 다시 그릴 원화2셀과 원위치 가이드2셀."""
from pathlib import Path
import sys
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need
from prepare_inputs import SRC,EXPECTED,WINDOW
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'low_boots_inputs_v2';out.mkdir(exist_ok=False);side=1254;cell=side//2;canvas=Image.new('RGBA',(side,side));sources=[]
 for i,(n,folder,expected)in enumerate(((71,'dash71_legs_v1','eaab95456fe7d274ef98c104aca5bec123ba6e198cc7fcee748e9b15dc6195eb'),(75,'before_second_v1','b27c2ac0b60fe4073a223bddc8809c11db1fb94ecd6c21d3e2751c05370f80ca'))):
  p=D/folder/'generated.png';need(digest(p)==expected,'Art');im=Image.open(p).convert('RGBA');need(im.size==(side,side),'Fixed actual source dimensions');canvas.alpha_composite(im.crop((cell,0,side,cell)),(cell*i,0));canvas.alpha_composite(a.composite(n,15)[0].crop(WINDOW).resize((cell,cell),Image.Resampling.NEAREST),(cell*i,cell));sources.append({'ref':n,'path':str(p.relative_to(ROOT)),'sha256':digest(p),'source_cell':[cell,0,side,cell],'target_cell':[cell*i,0,cell*(i+1),cell]})
 canvas.save(out/'two_targets_two_pose_guides.png');write(out/'manifest.json',{'parent_arc_sha256':EXPECTED,'source_cells':sources,'image_sha256':digest(out/'two_targets_two_pose_guides.png'),'art_not_edited':'원화 셀 복사와 원게임 그림 가이드 구성만 수행. 두 원화의 실제 그림 내용/알파 불변.'});print(out)
if __name__=='__main__':main()
