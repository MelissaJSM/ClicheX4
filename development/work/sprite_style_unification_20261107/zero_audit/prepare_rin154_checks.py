"""Create isolated current native test plan and independent reader from prior audit."""
from pathlib import Path
import json
D=Path(__file__).parent;R=D/'rin_extension'
j=json.loads((R/'rin141_components.json').read_text('utf8'));j['resources']['PL01_U.ARC'].update(path=str(R/'prepared_ground_remaining_v1/PL01_U.ARC'),after='a8a268fa92912678e70b01b776ffa477dd46c16e791f16f3346c76cd55016319')
(R/'rin154_components.json').write_text(json.dumps(j,indent=2)+'\n','utf8')
s=(D/'verify_rin141_readback.py').read_text('utf8').replace('prepared_ground_wall_v1','prepared_ground_remaining_v1').replace('after122_registered_v1','after141_registered_v2').replace('prepared_ground_first_v1','prepared_ground_wall_v1').replace('cf01c08e17c742983abcd566e08f165c2c48205b453d051ce64ea58ca1a8c0c1','247b47bcbf91eea64697305ba5a705de02207682c46fbbab0b527f9df00d6bb6')
s=s.replace("assert sha(new)=='247b47bcbf91eea64697305ba5a705de02207682c46fbbab0b527f9df00d6bb6'","assert sha(new)=='a8a268fa92912678e70b01b776ffa477dd46c16e791f16f3346c76cd55016319'")
start=s.index('mapping=');end=s.index('targets={}',start)
s=s[:start]+"mapping={(0,n):(0,n)for n in[83,85,87,89,91,105,107,130,133,134,3,4]};mapping[0,93]=(0,91)\n"+s[end:]
s=s.replace("support={(0,n)for n in(72,74,76,78,80)}|{(1,n)for n in(52,55,58,60,62,64)}","support={(0,n)for n in(84,86,88,90,92,94,106,108)}")
s=s.replace("counts['authored_exact']==19 and counts['other_display_exact']==417","counts['authored_exact']==13 and counts['other_display_exact']==423").replace('rin141_components_native_checks','rin154_components_native_checks').replace('final141_readback_audit','final154_readback_audit').replace("'cumulative_authored_refs':141,'incremental_refs':19,'previous122_preserved':True","'cumulative_authored_refs':154,'incremental_refs':13,'previous141_preserved':True")
# The independent 130 local image decoder is supplied below. It never imports the producer.
marker="  elif 'whole_translation'in op:"
s=s.replace(marker,"  elif 'arm_repaint_source'in op:\n   pp=ROOT/op['arm_repaint_source'];assert sha(pp.read_bytes())==op['source_sha256'];arm=decode_one(pp,130);assert np.array_equal(arm,np.array(Image.open(pp)));mask=Image.new('1',(384,384));ImageDraw.Draw(mask).polygon(op['polygon'],fill=1);mask=np.array(mask,bool);a[mask]=arm[mask]\n"+marker)
loc=s.index('masters={};provenance=[]')
fun='''def decode_one(source,n):
 folder=source.parent.parent;info=json.loads((folder/'inputs.json').read_text('utf8'));native=json.loads((folder/'native/registration.json').read_text('utf8'));f=next(f for f in info['frames']if f['ref']==n);nr=next(f for f in native['records']if f['ref']==n)
 im=Image.open(folder/'generated.png').convert('RGBA');assert sha((folder/'generated.png').read_bytes())==native['source_art_sha256'];cw,ch=im.width/info['columns'],im.height/info['rows'];cx,cy=f['cell'];crop=im.crop((round(cx*cw),round(cy*ch),round((cx+1)*cw),round((cy+1)*ch)));v=np.array(crop);near=np.zeros(v.shape[:2],np.uint8)
 for y in range(v.shape[0]):near[y]=1+np.sum((v[y,:,:3,None].transpose(0,2,1).astype(np.int32)-colors[None,:,:])**2,axis=2).argmin(1)
 nw,nh=info['native_cell'];votes=np.stack([np.array(Image.fromarray(np.where(near==i,v[:,:,3],0).astype(np.uint8)).resize((nw,nh),Image.Resampling.BOX))for i in range(1,16)]);alpha=np.array(crop.getchannel('A').resize((nw,nh),Image.Resampling.BOX));cell=np.where(alpha>=128,votes.argmax(0)+1,0).astype(np.uint8);a=np.zeros((384,384),np.uint8);x0,y0,x1,y1=info['crop'];a[y0:y1,x0:x1]=cell;dx,dy=nr['translate'];return np.roll(a,(dy,dx),(0,1))
'''
s=s[:loc]+fun+s[loc:]
(D/'verify_rin154_readback.py').write_text(s,'utf8')
g=(D/'check_rin141_guards.py').read_text('utf8').replace('pack_rin_after122','pack_rin_after141').replace('rin141_guard_checks','rin154_guard_checks')
g=g.replace("('parent_hash','missing71','extra147','bad_palette','altered_wall50','changed_saber72','wrong_alias75','changed_prior62')","('parent_hash','missing83','extra147','bad_palette','altered130','changed_saber84','wrong_alias93','changed_prior62')")
g=g.replace('missing71','missing83').replace('t[0,71]','t[0,83]').replace('t[0,73]','t[0,85]').replace('altered_wall50','altered130').replace('t[1,50]','t[0,130]').replace('changed_saber72','changed_saber84').replace('t[0,72]','t[0,84]').replace('wrong_alias75','wrong_alias93').replace('t[0,75]','t[0,93]')
(D/'check_rin154_guards.py').write_text(g,'utf8')
