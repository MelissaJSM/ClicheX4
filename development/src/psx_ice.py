"""US Zero ice body IDs, including complete neutral recovery stream sharing."""
SCOPE='wall_spin_ice_bank1_v1'
ANIMATION_BODY=frozenset((86,87,95,98,*range(132,144)))
BODY=ANIMATION_BODY|frozenset((88,96,99))
SHARED_OTHER_BODY=BODY-ANIMATION_BODY
PRESERVED_EFFECTS=frozenset((89,90,97,100))
PRESERVED_BODY=frozenset()
FLASH_BODY=frozenset((88,))

def flash_from_recovery(data,size):
    """Keep recovery87's silhouette exactly; pale fill with inward white contour."""
    w,h=size
    if len(data)!=w*h:raise ValueError('Invalid ice recovery dimensions')
    result=bytearray(len(data))
    for i,v in enumerate(data):
        if not v:continue
        x,y=i%w,i//w
        edge=x==0 or x==w-1 or y==0 or y==h-1 or any(not data[(y+dy)*w+x+dx] for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)))
        result[i]=15 if edge else 12
    return bytes(result),size

def validate_flash(frames,bounds):
    if bounds[87]!=bounds[88] or frames[88]!=flash_from_recovery(*frames[87]):
        raise ValueError('Ice shared flash differs from Riko recovery silhouette')
    return {'source':87,'derived':88,'silhouette_equal':True,'palette_indices':[12,15]}
