"""81의 넓어진 보폭만 교정하기 위한 새원화/원접점 비교 입력."""
from pathlib import Path
import sys
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need
from prepare_inputs import SRC,EXPECTED,WINDOW
def main():
 need(digest(SRC)==EXPECTED,'Parent');p=D/'before_second_v1/generated.png';need(digest(p)=='b27c2ac0b60fe4073a223bddc8809c11db1fb94ecd6c21d3e2751c05370f80ca','Art');im=Image.open(p).convert('RGBA');side=im.width;need(im.height==side and side%2==0,'Square');s=side//2;a=Archive(SRC.read_bytes());out=D/'stance81_input_v1';out.mkdir(exist_ok=False);cv=Image.new('RGBA',im.size);cv.alpha_composite(im.crop((s,s,side,side)),(0,0))
 for i,n in enumerate((81,0,67),1):cv.alpha_composite(a.composite(n,15)[0].crop(WINDOW).resize((s,s),Image.Resampling.NEAREST),(i%2*s,i//2*s))
 cv.save(out/'target_and_pose.png');write(out/'manifest.json',{'parent_arc_sha256':EXPECTED,'source_art_sha256':digest(p),'target_ref':81,'source_cell':[s,s,side,side],'target_cell':[0,0,s,s],'image_sha256':digest(out/'target_and_pose.png'),'actual_source_dimensions':list(im.size),'scope':'좌상단 새81만 교정,우상단 원81 발간격·접점,아래는 대기/67 의상참고. 원화 픽셀 수정 없음.'});print(out)
if __name__=='__main__':main()
