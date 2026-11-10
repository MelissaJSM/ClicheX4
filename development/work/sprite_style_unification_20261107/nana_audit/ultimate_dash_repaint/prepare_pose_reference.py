"""채택된 기본형 같은4자세를 의상 아닌 관절/발 접점 참조로 수집한다."""
from pathlib import Path
import sys
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need
def main():
 src=N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC';need(digest(src)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa','Base source');a=Archive(src.read_bytes());out=D/'base_pose_reference_v1';out.mkdir(exist_ok=False);im=Image.new('RGBA',(1536,1536))
 for i,n in enumerate((67,71,79,93)):im.alpha_composite(a.composite(n,0)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
 im.save(out/'accepted_base_poses.png');write(out/'manifest.json',{'source':src.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'refs':[67,71,79,93],'role':'관절과 앞뒤 두 발의 분리 참고만.검정 의상/부츠를 얼티밋에 복사하지 않음.','image_sha256':digest(out/'accepted_base_poses.png')})
if __name__=='__main__':main()
