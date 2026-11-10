from pathlib import Path
P=Path(__file__).parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
D=P/'walk_design_basis';worlds=np.load(D/'worlds_probe.npz')
items=[(22,'cape',[10,-15,29,1]),(22,'boot',[5,7,23,25]),(24,'cape',[10,-15,28,1]),(24,'boot',[6,7,22,20]),(25,'cape',[11,-18,27,-3]),(27,'cape',[8,-32,29,-9]),(33,'right_boot',[5,7,20,24]),(33,'left_boot',[-18,7,-5,24]),(33,'cape',[7,-3,21,15])]
sheet=Image.new('RGBA',(96,120));records=[]
for i,(n,kind,rect) in enumerate(items):
    x0,y0,x1,y1=rect;a=worlds[str(n)][64+y0:64+y1,64+x0:64+x1].copy();a[np.isin(a,[4,5,8,9,11,13,14])]=0
    m=a!=0;r=np.zeros((*a.shape,4),dtype=np.uint8);r[m,:3]=colors[a[m]-1];r[m,3]=255;anchor=[(32-a.shape[1])//2,(40-a.shape[0])//2]
    sheet.alpha_composite(Image.fromarray(r),(i%3*32+anchor[0],i//3*40+anchor[1]));records.append({'frame':n,'kind':kind,'rect':rect,'cell':i,'anchor':anchor})
sheet.resize((768,960),Image.Resampling.NEAREST).save(D/'cloth_edit_target.png')
(D/'cloth_layout.json').write_text(json.dumps(records,indent=2))
(D/'blocked_fit_call.json').write_text(json.dumps({'prompt':'prompt_fit.txt','input':'fit_edit_target.png','outcome':'imagegen output moderation blocked: sexual','request_id':'e4c6f3cb-8d98-4d32-aebb-4d9cfe3b6642','output_saved':False},indent=2))
