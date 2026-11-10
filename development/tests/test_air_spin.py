import copy
import unittest
import numpy as np
from src.psx_air_spin import BODY,ROTATING,head_views,validate_heads,validate_body_mass

class AirSpinTests(unittest.TestCase):
    def setUp(self):
        self.head=np.zeros((19,23),np.uint8);self.head[2:17,2:19]=4;self.head[3:8,4:7]=8;self.head[15,19:22]=12
        self.ref=(self.head.tobytes(),(23,19),(0,0,23,19))
        self.reg={'base_head_world':[-14,-18],'lead_head_world':{'132':[-10,-22],'160':[-9,-25]},'rotation_degrees':list(range(0,360,45)),'pivot_world':[0,0]}
        self.views=head_views(*self.ref,self.reg);self.frames={};self.bounds={n:(-64,-64,64,64) for n in BODY}
        for n,(data,(w,h),(x,y)) in self.views.items():
            a=np.zeros((128,128),np.uint8);a[y+64:y+64+h,x+64:x+64+w]=np.frombuffer(data,np.uint8).reshape(h,w)
            self.frames[n]=(a.tobytes(),(128,128))

    def test_quarter_turn_retains_native_pixel_count_and_orientation(self):
        data,size,pos=self.views[165];p=np.frombuffer(data,np.uint8).reshape(size[1],size[0])
        expected=np.rot90(self.head);ys,xs=np.nonzero(expected);expected=expected[ys.min():ys.max()+1,xs.min():xs.max()+1]
        self.assertTrue(np.array_equal(p,expected))
        self.assertEqual(np.count_nonzero(p),np.count_nonzero(self.head))
        self.assertEqual(set(validate_heads(self.frames,self.bounds,*self.ref,self.reg)['frames']),set(map(str,BODY)))

    def test_one_changed_head_pixel_is_rejected_in_each_pose(self):
        for n,(data,size) in self.frames.items():
            with self.subTest(frame=n):
                changed=bytearray(data);i=next(i for i,v in enumerate(data) if v);changed[i]=1
                with self.assertRaisesRegex(ValueError,'identity'):
                    validate_heads({**self.frames,n:(bytes(changed),size)},self.bounds,*self.ref,self.reg)

    def test_missing_pose_and_per_frame_rotation_changes_rejected(self):
        frames=dict(self.frames);frames.pop(163)
        with self.assertRaisesRegex(ValueError,'Incomplete'):validate_heads(frames,self.bounds,*self.ref,self.reg)
        for key,value in [('pivot_world',[1,0]),('rotation_degrees',[0]*8),('base_head_world',[0.5,0])]:
            reg=copy.deepcopy(self.reg);reg[key]=value
            with self.assertRaises(ValueError):head_views(*self.ref,reg)

    def test_wrong_head_scale_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'23x19'):head_views(bytes(22*19),(22,19),(0,0,22,19),self.reg)

    def test_half_pixel_rotation_origin_keeps_cardinal_pixel_area(self):
        reg=copy.deepcopy(self.reg);reg['pivot_world']=[0,.5];views=head_views(*self.ref,reg)
        for n in (161,165,169,173):self.assertEqual(sum(v!=0 for v in views[n][0]),np.count_nonzero(self.head))

    def test_body_can_shrink_while_head_stays_exact_and_must_be_rejected(self):
        with self.assertRaisesRegex(ValueError,'body mass'):validate_body_mass(self.frames,self.views,446)
        def body(area):
            return {n:(data[:-area]+bytes([7])*area,size) for n,(data,size) in self.frames.items()}
        frames=body(446)
        self.assertEqual(len(validate_body_mass(frames,self.views,446)['frames']),8)
        for extra in (258,900):
            changed=body(extra)
            with self.assertRaisesRegex(ValueError,'body mass'):validate_body_mass(changed,self.views,446)

    def test_jump_reference_rejects_old_crouch_sized_body(self):
        def body(area):
            return {n:(data[:-area]+bytes([7])*area,size) for n,(data,size) in self.frames.items()}
        with self.assertRaisesRegex(ValueError,'body mass'):
            validate_body_mass(body(437),self.views,586)
        self.assertEqual(len(validate_body_mass(body(541),self.views,586)['frames']),8)

if __name__=='__main__':unittest.main()
