import unittest
from tools.adventure_tiling import midpoint,refine_first_segments,split_quad_across


class AdventureTilingTests(unittest.TestCase):
    def test_render_only_route_prefix_keeps_every_authored_station(self):
        src=[(0,0,10,4),(0,12,9,4),(3,25,5,4),(8,38,1,4),
             (13,51,1,4),(12,65,3,5)]
        fine=refine_first_segments(src,5)
        self.assertEqual(len(fine),len(src)+5)
        self.assertEqual(fine[0],src[0])
        self.assertEqual(fine[-1],src[-1])
        self.assertEqual(fine[2],src[1])
        self.assertEqual(fine[4],src[2])
        self.assertEqual(fine[1],(0,6,9.5,4))
        self.assertEqual(src[1],(0,12,9,4))

    def test_cross_valley_quads_keep_shared_boundary(self):
        a,b=(0,0,0),(20,0,-2)
        c,d=(22,12,-3),(2,12,1)
        left,right=split_quad_across(a,b,c,d)
        self.assertEqual(left[1],right[0])
        self.assertEqual(left[2],right[3])
        self.assertEqual(left[0],a)
        self.assertEqual(right[1],b)
        self.assertEqual(right[2],c)
        self.assertEqual(left[3],d)
        self.assertEqual(midpoint(a,b),left[1])

    def test_reject_unbounded_tessellation(self):
        with self.assertRaises(ValueError):
            refine_first_segments([(0,),(1,)],2)
        with self.assertRaises(ValueError):
            refine_first_segments([(0,),(1,)],-1)
        with self.assertRaises(ValueError):
            midpoint((1,2),(1,))


if __name__=="__main__":
    unittest.main()
