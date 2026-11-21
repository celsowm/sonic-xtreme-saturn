import json
import unittest
from tools.bake_greybox import convert_xyz, emit, parse_obj, parse_entities

OBJ = b"o mesh_0000_main_route\nv 0 0 0\nv 2 0 0\nv 2 3 1\nv 0 3 1\nf 1 2 3 4\n"
SCENE = {"version":0,"units":"m","axes":"RH_Z_UP","entities":[
    {"id":"start","kind":"player_spawn","position":[1,2,3]},
    {"id":"end","kind":"goal","position":[-2,5,3]}
]}

class BakeTests(unittest.TestCase):
    def test_axes(self):
        self.assertEqual(convert_xyz((1,2,3)), (65536,196608,-131072))
    def test_winding_and_triangles(self):
        v, f = parse_obj(OBJ.decode())
        self.assertEqual(v[2], (131072,65536,-196608))
        self.assertEqual(f, [(0,2,1,1,0),(0,3,2,2,0)])
    def test_decor_material_palette_and_collision_isolation(self):
        # All render props are separate from the ground collision OBJ.
        # Group suffixes map to small, fixed renderer color indices.
        header = b"v 0 0 0\nv 2 0 0\nv 0 2 0\n"
        for suffix, expected in (("canopy",3),("trunk",2),("wood",4),("rock",2),("water",5)):
            source = header + f"o mesh_0000_palm_{suffix}\nf 1 2 3\n".encode()
            vertices, faces = parse_obj(source.decode())
            self.assertEqual(len(vertices),3)
            self.assertEqual([face[4] for face in faces],[expected])
        # Existing playable strips preserve their calibrated alternating palette.
        strip = (b"v 0 0 0\nv 2 0 0\nv 2 3 1\nv 0 3 1\n"
                 b"o mesh_0000_main_route\nf 1 2 3 4\nf 1 3 4\n")
        self.assertEqual([f[4] for f in parse_obj(strip.decode())[1]],[0,0,3])

    def test_invalid_obj(self):
        for bad in (b"f 1 2 99", b"f 1 1 2", b"f -1 2 3", b"v NaN 0 0", b"v 257 0 0"):
            with self.assertRaises(ValueError):
                parse_obj((OBJ + bad).decode())
    def test_required_entities(self):
        with self.assertRaises(ValueError):
            parse_entities(json.dumps(dict(SCENE, entities=[])))
    def test_determinism(self):
        raw = json.dumps(SCENE).encode()
        output = emit(OBJ, raw)
        self.assertEqual(output, emit(OBJ, raw))
        self.assertIn(b"#define STAGE_FACE_COUNT 2u", output)
        self.assertIn(b"#define STAGE_ENTITY_COUNT 2u", output)
