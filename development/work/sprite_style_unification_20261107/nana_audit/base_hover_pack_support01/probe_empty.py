"""실제 빈 head층의 기존 count0 표현 재사용으로 20B 확보 여부."""
from probe_order import *
def main():
 audit=json.loads((R/'input_audit.json').read_text('utf8'));p=ROOT/audit['input']['path'];a=Archive(p.read_bytes());starts=bank_offsets(a.c);count=composition_frame(a.c,5,0)['bank_frame_count'];capacity=(starts[6]-starts[5]-count*4)//4;rr=[tuple(records(a.c,5,n)[i:i+4]for i in range(0,len(records(a.c,5,n)),4))for n in range(count)];targets={}
 for n in REFS:targets[n]=np.array(Image.open(R/('body_layers_probe01'if n%2 else'shoot_layers_probe02')/f'layer5_{n}.png'))
 for n in REFS[::2]:
  _,partlists,_=HeadPacker.head_data([targets[q][80:240,80:240]for q in(n,n+1)],GEOM)
  for q,parts in zip((n,n+1),partlists):rr[q]=tuple(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts)
 baseline,_=packed_sequences(rr);blank_refs=[128,129,132,140,159];proof=[]
 for n in blank_refs:
  z,_=a.layer(n,5);need(not z.any(),'실제 빈 head');need(len(rr[n])==1,'빈층 한기록');proof.append({'ref':n,'before_hex':b''.join(rr[n]).hex(),'before_count':1,'after_count':0,'whole_layer_pixels':int((z>0).sum()),'layer_indices_sha256':sha(z.tobytes())});rr[n]=()
 packed,merges=packed_sequences(rr);report={'parent_sha256':digest(p),'capacity_records':capacity,'baseline_records':len(baseline),'after_records':len(packed),'slack_bytes':(capacity-len(packed))*4,'existing_zero_count_refs':[n for n in range(count)if not records(a.c,5,n)],'changes':proof,'target_geometry':GEOM,'no_nonempty_record_order_change':True,'raw_changed':False,'new_art_changed':False,'native_cpu_verified':False};out=D/'empty_probe01';out.mkdir(exist_ok=False);write(out/'report.json',report);write(out/'sequences.json',{'sequences':[[t.hex()for t in seq]for seq in rr],'packed':[t.hex()for t in packed]});print(json.dumps(report))
if __name__=='__main__':main()
