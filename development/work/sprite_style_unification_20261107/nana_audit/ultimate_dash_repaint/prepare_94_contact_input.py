"""94의 접힌 앞다리만 원래 높이로 되돌리는 입력 구성."""
from pathlib import Path
import sys
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need
from prepare_inputs import SRC,EXPECTED,WINDOW
def main():
 need(digest(SRC)==EXPECTED,'Parent');p=D/'before_last_v1/generated.png';need(digest(p)=='4f328802e14c925d32c3835b43da4731da31040aacff49a6218f71140b49a8bd','Art');im=Image.open(p).convert('RGBA');side=im.width;s=side//2;a=Archive(SRC.read_bytes());out=D/'fold94_input_v1';out.mkdir(exist_ok=False);cv=Image.new('RGBA',im.size);cv.alpha_composite(im.crop((s,0,side,s)),(0,0))
 for i,n in enumerate((94,93,39),1):cv.alpha_composite(a.composite(n,15)[0].crop(WINDOW).resize((s,s),Image.Resampling.NEAREST),(i%2*s,i//2*s))
 cv.save(out/'target_and_pose.png');write(out/'manifest.json',{'parent_arc_sha256':EXPECTED,'source_art_sha256':digest(p),'target_ref':94,'source_cell':[s,0,side,s],'target_cell':[0,0,s,s],'image_sha256':digest(out/'target_and_pose.png'),'scope':'좌상단 새94의 앞 접힌 다리만 대상.우상단 원94,아래93/39참조. 긴뒤다리·상체·새얼굴 보호.'});print(out)
if __name__=='__main__':main()
