"""누적 후보에서 남은 특수 본체의 묘사 차이를 대기와 직접 비교한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
def main():
    o=H/'special_after_air01';need(not o.exists(),'Fresh output required');o.mkdir()
    src={'PL00_U.ARC':('prepared_air01','c580b371564252fd73cb97aa31d3282dcebabf5855cbec6d5b00acc7f7b7c6be'),'PL02_U.ARC':('prepared_ultimate_wall01','c851fb17b2369281667970c414be63eb31fb1f02fe5641ad667bfb4b5c8507cf')}
    arcs={}
    for name,(folder,expected) in src.items():
        data=(H/folder/name).read_bytes();need(sha(data)==expected,'Changed candidate');arcs[name]=Archive(data)
    refs=[88,89,90,91,92,93,94,95,96,98,99,100,101,102,103,104,231,232];rows=[]
    for form,name,mask in [('base','PL00_U.ARC',0),('fourth','PL00_U.ARC',15),('ultimate_before','PL02_U.ARC',15),('ultimate_after','PL02_U.ARC',0)]:
        a=arcs[name]
        for i in range(3):
            ns=refs[i*6:(i+1)*6];p=o/f'{form}_{i:02}.png';page([(str(n),a.composite(n,mask)[0])for n in ns],a.composite(0,mask)[0],p,cols=3,scale=5)
            rows.append({'form':form,'refs':ns,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())})
    write(o/'manifest.json',{'sources':src,'sheets':rows,'scope':'特수 본체 미술 재검토용 추출. 게임 실행 또는 재작화가 아님.'.replace('特','특'),'actual_view_pending':True})
    print(str(o))
if __name__=='__main__':main()
