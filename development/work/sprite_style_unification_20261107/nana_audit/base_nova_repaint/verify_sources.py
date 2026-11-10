"""생성 고정6셀과 새 의미층/효과 규칙을 실제최종 ARC에 결속한다."""
from pack_candidate import *
from scipy.ndimage import binary_dilation,binary_fill_holes
from save_and_register import reg
from lock_candidate import validate_inputs
def main():
 p=D/'packed_nova_candidate_v1';lock=validate_inputs(PARENT.read_bytes());a=Archive(PARENT.read_bytes());b=Archive((p/'PL00_U.ARC').read_bytes());registrations=[]
 for page in('a','b'):
  m=json.loads((D/f'{page}_registered_v1/manifest.json').read_text('utf8'));im=Image.open(ROOT/m['source_art']).convert('RGBA');need(digest(ROOT/m['source_art'])==m['source_art_sha256'],'원화해시')
  for q in m['frames']:
   start=16 if q['form']=='fourth'else 0;pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(im.crop(q['source_crop']),(96,96),pal,'area_vote')
   want=np.array(Image.open(D/f'{page}_registered_v1/{q["form"]}_{q["ref"]:03}_indices.png'));need(np.array_equal(z,want)and sha(z.tobytes())==q['target_sha256'],'고정셀 재양자화');registrations.append({'ref':q['ref'],'form':q['form'],'indices_sha256':sha(z.tobytes())})
 t,_=targets();fx=np.array(Image.open(D/'preparation_effect_probe_v2/effect214_indices.png'));fm=fx>0;need(int(fm.sum())==124,'124원효과');fxchecks=0
 for pb in PBS:
  z=t[213,pb].copy();z[fm]=fx[fm]if pb==0 else 0;need(np.array_equal(z,t[214,pb]),'214파생');need(np.array_equal(t[215,pb],t[216,pb]),'216별칭')
 for mask in range(16):
  for arm in(1,2):need(np.array_equal(np.array(b.composite(214,mask,arm)[0])[fm],np.array(a.rgba(fx))[fm]),'원효과 모든조건');fxchecks+=1
 db=np.array(Image.open(D/'dash_layers_probe_v1/base_body_217.png'));df=np.array(Image.open(D/'dash_layers_probe_v1/fourth_union_217.png'))
 for z,mask in((db,0),(df,15)):
  ring=binary_dilation(z>0)&(z==0);body=z.copy();body[ring]=9;need(a.rgba(body,16 if mask else 0).tobytes()==b.composite(217,mask,1)[0].tobytes(),'새ring 원규칙')
  if not mask:need(np.array_equal(body,t[217,0]),'새217기본')
 oldbody=np.roll(a.layer(217)[0],1,axis=0);old220=a.layer(220)[0];om=oldbody>0;bg=old220.copy();bg[om]=0;bg[om&binary_fill_holes(old220>0)]=9
 nb=np.roll(t[217,0],1,axis=0);bg[nb>0]=nb[nb>0];need(np.array_equal(bg,t[220,0]),'220새몸+1 및효과구멍')
 for pb in PBS[1:]:need(np.array_equal(t[220,pb],np.roll(t[217,pb],1,axis=0)),'220아머+1')
 for n in(218,219):
  need(raw(a,0,n)==raw(b,0,n),'독립에너지raw')
  for pb in PBS:need(np.array_equal(a.layer(n,pb)[0],b.layer(n,pb)[0]),'독립에너지층')
 for(n,pb),z in t.items():need(np.array_equal(b.layer(n,pb)[0],z),'최종30층')
 write(p/'source_verification.json',{'passed':True,'candidate_sha256':digest(p/'PL00_U.ARC'),'input_lock_sha256':digest(p/'INPUT_FROZEN.json'),'input_files_verified':len(lock['files']),'generated_fixed_cells_requantized':registrations,'effect214_texels':124,'effect214_RGBA_conditions':fxchecks,'new217_manhattan1_both_forms_exact':True,'new220_body_y1_and_envelope_rule_exact':True,'effects218219_all_raw_layers_exact':True,'target_layers_exact':30,'scope':'원화6고정셀 재양자화와최종효과/층결속.공통손/하체같은행표본의의미선택은마스크manifest·정적검토를따르며독립검사/실기는별도.'});print(json.dumps({'passed':True,'cells':len(registrations),'layers':30}))
if __name__=='__main__':main()
