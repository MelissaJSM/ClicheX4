from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,helper,need
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
reg=load('special_quantizer',N/'base_run_repaint/register_page.py');metric=load('special_metric',N/'ultimate_victory_repaint/register_page.py')
def main():
 m=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());p=D/'hand98_v1/generated.png';need(digest(p)=='4576b0c9235db167a647732687c74d9642e76bb3a5ac0ae8edfb54c121968e64','新source');im=Image.open(p).convert('RGBA');need(im.size==(1536,1024),'전체격자');out=D/'hand98_registered_v1';out.mkdir(exist_ok=False);rows=[];records=[]
 for i,(form,start,mask)in enumerate((('before',16,15),('after',0,0))):
  cell=im.crop((i*768,0,(i+1)*768,1024));ar=np.array(cell);lab,count=label(ar[:,:,3]>=128,np.ones((3,3)));sz=np.bincount(lab.flat);sz[0]=0;need(sum(sz>1000)==1,'큰몸체');pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32);z=np.zeros((384,384),np.uint8);z[96:224,112:208]=reg.register(cell,(96,128),pal,'area_vote');Image.fromarray(z).save(out/f'{form}_098_indices.png')
  bg=ar[40:240,180:600,3];old=metric.full(a,98,mask);records.append({'form':form,'source_crop':[i*768,0,(i+1)*768,1024],'world_crop':[-48,-64,48,64],'source_size':list(im.size),'body_translation':[0,0],'new_bbox':metric.bbox(z),'old_bbox':metric.bbox(old),'eye':metric.eye(z),'old_eye':metric.eye(old),'components8':int(label(z>0,np.ones((3,3)))[1]),'sample_background_alpha_range':[int(bg.min()),int(bg.max())],'target_sha256':sha(z.tobytes())});rows.append((form,[('idle',a.composite(0,mask)[0]),('previous',a.composite(98,mask)[0]),('new source fixed',a.rgba(z,start)),('prior local',a.rgba(np.array(Image.open(D/f'geometry_position_probe_v1/{form}_098_indices.png')),start))]))
 helper.grid(rows,out/'comparison.png',7);write(out/'manifest.json',{'source_sha256':digest(p),'frames':records,'native_packed':False,'runtime_verified':False});print(json.dumps(records))
if __name__=='__main__':main()
