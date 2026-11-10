"""US animation103 body references; separate parts6 projectiles stay untouched."""
SCOPE='wall_spin_ice_rise_burst_bank1_v1'
BODY=frozenset(range(177,190))
CHARGE=frozenset(range(177,182))
GROUND=frozenset(range(182,188))
CHARGE_BOXES={177:(13,-5,22,9),178:(3,-35,20,-21),179:(-1,-39,21,-20),180:(4,-35,25,-14),181:(5,-30,23,5)}
CHARGE_REMAP={1:10,2:2,3:6,8:15,9:12,10:7,11:1}

def validate_charge(frames,originals,bounds):
    """Keep the original embedded aura shape at its original world coordinates."""
    result={}
    for n,box in CHARGE_BOXES.items():
        pixels,size=frames[n];source,source_size=originals[n]
        if size!=source_size:raise ValueError('Charging frame size changed')
        x0,y0,_,_=bounds[n];count=0
        for y in range(box[1],box[3]):
            for x in range(box[0],box[2]):
                i=(y-y0)*size[0]+x-x0;wanted=CHARGE_REMAP.get(source[i])
                if wanted is not None:
                    if pixels[i]!=wanted:raise ValueError(f'Charging aura changed at frame{n} ({x},{y})')
                    count+=1
        result[str(n)]=count
    return result
