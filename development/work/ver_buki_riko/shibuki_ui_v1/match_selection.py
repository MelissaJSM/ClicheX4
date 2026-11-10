exec(open('work/ver_buki_riko/shibuki_ui_v1/inspect_more.py',encoding='utf8').read().split('records,o,cur=load();')[0])
records,o,cur=load();from src.psx_sprite_batch import canvas_from_parts
g=entry(o['PL00_U.ARC'],2);p=entry(o['PL00_U.ARC'],3);base=[]
for n in range(237):
 try:
  f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];dec=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;fr=compose_indices(dec,f['tile_count'],composition_frame(p,0,n))
  im=Image.frombytes('L',fr[1],fr[0]);im=im.crop(im.getbbox());base.append((n,np.array(im)>0))
 except ValueError:pass
raw=o['ST0E_U1.ARC'];gg=entry(raw,0x10102)[90112:];pp=entry(raw,10);found={}
for n in list(range(9))+list(range(18,25)):
 fr=compose_static(gg,local_composition(aliased_composition(pp,2,n)));im=Image.frombytes('L',fr[1],fr[0]);im=im.crop(im.getbbox());a=np.array(im)>0;matches=[]
 for k,b in base:
  for flip in (False,True):
   bb=b[:,::-1] if flip else b;h=max(a.shape[0],b.shape[0]);w=max(a.shape[1],b.shape[1]);aa=np.zeros((h,w),bool);cc=aa.copy();aa[:a.shape[0],:a.shape[1]]=a;cc[:bb.shape[0],:bb.shape[1]]=bb
   matches.append((float(np.count_nonzero(aa^cc))/max(1,np.count_nonzero(aa|cc)),k,flip,a.shape,b.shape))
 found[n]=sorted(matches)[:4]
print(json.dumps(found,indent=2));(D/'selection_mask_matches.json').write_text(json.dumps(found,indent=2))
