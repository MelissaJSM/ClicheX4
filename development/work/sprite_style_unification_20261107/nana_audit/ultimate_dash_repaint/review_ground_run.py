"""같은 최신 PL02에서 얼티밋 이동32 전후 의상을 대기와 재검토할 시트."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from prepare_inputs import SRC,EXPECTED
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'ground_run_review_v1';out.mkdir(exist_ok=False);records=[]
 for form,mask in(('before',15),('after',0)):
  rows=[]
  for n in range(1,33,2):
   ims=[a.composite(i,mask)[0]for i in(0,n,n+1,39)]
   rows.append((f'{form} run {n}/{n+1}',list(zip(('accepted idle','current run','current firing','new air detail'),ims))))
   records.append({'form':form,'refs':[n,n+1],'rgba_sha256':[sha(im.tobytes())for im in ims]})
  for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'{form}_{i//3+1}.png',5)
 write(out/'manifest.json',{'parent_arc_sha256':EXPECTED,'records':records,'source_only':True,'new_art_or_native_change':False,'actual_viewed_sheets':[],'art_findings_pending':True});print(out)
if __name__=='__main__':main()
