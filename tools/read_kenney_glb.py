"""Minimal dependency-free glTF 2.0 GLB triangle reader for selected Kenney CC0 props.

Only static, uncompressed triangles, embedded BIN buffer 0, ordinary POSITION
accessors and ushort/uint/ubyte indices are supported. Node transforms are
honored. The pack is authored Y-up: output is Blender Z-up (x,-z,y).
This is *not* a generic target Saturn loader or a fallback for unknown assets.
"""
import json
import math
import struct
from pathlib import Path

COMPONENT = {5121:("B",1),5123:("H",2),5125:("I",4),5126:("f",4)}
ELEMENTS = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4}
SUPPORTED_EXTENSIONS={"KHR_materials_unlit","KHR_texture_transform"}

def mat_identity():
    return ((1.0,0.0,0.0,0.0),
            (0.0,1.0,0.0,0.0),
            (0.0,0.0,1.0,0.0),
            (0.0,0.0,0.0,1.0))

def mat_mul(a,b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(4))
                       for j in range(4)) for i in range(4))

def node_matrix(node):
    if "matrix" in node:
        x=node["matrix"]
        if len(x)!=16:raise ValueError("invalid node transform")
        return tuple(tuple(x[col*4+row] for col in range(4)) for row in range(4))
    x,y,z,w=node.get("rotation",[0,0,0,1])
    sx,sy,sz=node.get("scale",[1,1,1])
    tx,ty,tz=node.get("translation",[0,0,0])
    return (
        ((1-2*y*y-2*z*z)*sx,(2*x*y-2*z*w)*sy,(2*x*z+2*y*w)*sz,tx),
        ((2*x*y+2*z*w)*sx,(1-2*x*x-2*z*z)*sy,(2*y*z-2*x*w)*sz,ty),
        ((2*x*z-2*y*w)*sx,(2*y*z+2*x*w)*sy,(1-2*x*x-2*y*y)*sz,tz),
        (0.0,0.0,0.0,1.0)
    )

def open_glb(path):
    data=Path(path).read_bytes()
    if len(data)<20:raise ValueError("truncated GLB")
    magic,version,size=struct.unpack_from("<4sII",data,0)
    if magic!=b"glTF" or version!=2 or size!=len(data):
        raise ValueError("unsupported GLB v2 header")
    chunks={}
    at=12
    while at<len(data):
        if at+8>len(data):raise ValueError("truncated chunk header")
        size,kind=struct.unpack_from("<I4s",data,at)
        at+=8
        if at+size>len(data):raise ValueError("truncated chunk")
        chunks[kind]=data[at:at+size]
        at+=size
    if b"JSON" not in chunks or b"BIN\x00" not in chunks:
        raise ValueError("GLB must contain JSON and one embedded binary buffer")
    obj=json.loads(chunks[b"JSON"].decode("utf-8").rstrip(" \x00"))
    required=set(obj.get("extensionsRequired",[]))
    if not required.issubset(SUPPORTED_EXTENSIONS):
        raise ValueError("unsupported required GLB extensions")
    if len(obj.get("buffers",[]))!=1 or "uri" in obj["buffers"][0]:
        raise ValueError("only embedded buffer zero supported")
    binary=chunks[b"BIN\x00"]
    if len(binary)<obj["buffers"][0]["byteLength"]:
        raise ValueError("embedded GLB binary too short")
    return obj,binary

def read_accessor(obj,binary,index):
    acc=obj["accessors"][index]
    if "sparse" in acc or "bufferView" not in acc:
        raise ValueError("sparse/implicit GLB accessor unsupported")
    comp=acc["componentType"]
    if comp not in COMPONENT or acc["type"] not in ELEMENTS:
        raise ValueError("unsupported accessor type")
    kind,size=COMPONENT[comp]
    count=ELEMENTS[acc["type"]]
    fmt="<"+kind*count
    item_size=size*count
    view=obj["bufferViews"][acc["bufferView"]]
    if view.get("buffer",0)!=0:raise ValueError("external GLB buffer")
    stride=view.get("byteStride",item_size)
    if stride<item_size:raise ValueError("invalid accessor stride")
    off=view.get("byteOffset",0)+acc.get("byteOffset",0)
    limit=view.get("byteOffset",0)+view["byteLength"]
    if off<0 or acc["count"]<0 or (acc["count"] and off+(acc["count"]-1)*stride+item_size>limit):
        raise ValueError("accessor outside buffer view")
    return [struct.unpack_from(fmt,binary,off+i*stride) for i in range(acc["count"])]

def read_glb_triangles(path,with_materials=False):
    obj,binary=open_glb(path)
    nodes=obj.get("nodes",[])
    scenes=obj.get("scenes",[])
    if not scenes:raise ValueError("GLB missing scene")
    active=obj.get("scene",0)
    if active>=len(scenes):raise ValueError("invalid scene index")
    vertices=[]
    triangles=[]
    face_materials=[]
    seen=set()
    def walk(index,parent):
        if index<0 or index>=len(nodes):raise ValueError("invalid node index")
        if index in seen:raise ValueError("shared/cyclic node unsupported")
        seen.add(index)
        node=nodes[index]
        transform=mat_mul(parent,node_matrix(node))
        if "mesh" in node:
            mesh=obj["meshes"][node["mesh"]]
            for p in mesh["primitives"]:
                if p.get("mode",4)!=4 or "POSITION" not in p.get("attributes",{}):
                    raise ValueError("only triangle POSITION primitives supported")
                coords=read_accessor(obj,binary,p["attributes"]["POSITION"])
                if any(len(v)!=3 for v in coords):raise ValueError("bad positions")
                off=len(vertices)
                for x,y,z in coords:
                    world=(
                      transform[0][0]*x+transform[0][1]*y+transform[0][2]*z+transform[0][3],
                      transform[1][0]*x+transform[1][1]*y+transform[1][2]*z+transform[1][3],
                      transform[2][0]*x+transform[2][1]*y+transform[2][2]*z+transform[2][3],
                    )
                    # glTF is Y-up, Blender is Z-up.
                    vertices.append((world[0],-world[2],world[1]))
                idx=read_accessor(obj,binary,p["indices"]) if "indices" in p else [(i,) for i in range(len(coords))]
                flat=[t[0] for t in idx]
                if len(flat)%3:raise ValueError("non-triangle index count")
                for j in range(0,len(flat),3):
                    a,b,c=flat[j:j+3]
                    if min(a,b,c)<0 or max(a,b,c)>=len(coords):
                        raise ValueError("out of range GLB index")
                    triangles.append((off+a,off+b,off+c))
                    face_materials.append(p.get('material',-1))
        for child in node.get("children",[]):
            walk(child,transform)
    for root in scenes[active].get("nodes",[]):
        walk(root,mat_identity())
    if not vertices or not triangles:raise ValueError("GLB contains no triangles")
    if not all(math.isfinite(v) for xyz in vertices for v in xyz):
        raise ValueError("nonfinite GLB coordinates")
    if with_materials:
        names=[m.get('name','') for m in obj.get('materials',[])]
        return vertices,triangles,face_materials,names
    return vertices,triangles
