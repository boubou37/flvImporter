from reader import BinaryReader, FlvReader

f = open('customMade.flver', 'rb');
br = None;
identifier = f.read(6)
endianness = f.read(2)

if endianness == b'B\x00':
    endianness = 'big'
elif endianness == b'L\x00':
    endianness = 'little'
else:
    raise Exception('Endianness unrecognized: expected either B or L, got {}'.format(endianness))

br = FlvReader(f, endianness);
version = br.assert_int32(0x2001A)

dataOffset = br.read_int32();
dataSize = br.read_int32();
dummyCount = br.read_int32();
materialCount = br.read_int32();
boneCount = br.read_int32();
meshCount = br.read_int32();
vertexBufferCount = br.read_int32();

boundingBoxMin = br.read_vector3()
boundingBoxMax = br.read_vector3()

Unk40 = br.read_int32();
totalFaceCount = br.read_int32();

Unk48 = br.assert_byte(0x00, 0x10);
br.assert_bool(True);
Unk4A = br.read_bool();
br.assert_byte(0);

br.assert_int16(0);
Unk4E = br.assert_int16(0, -1);

faceSetCount = br.read_int32();
bufferLayoutCount = br.read_int32();
textureCount = br.read_int32();

Unk5C = br.read_int32();
br.assert_int32(0);
br.assert_int32(0);
Unk68 = br.assert_int32(0, 1, 2, 3, 4);
br.assert_int32(0);
br.assert_int32(0);
br.assert_int32(0);
br.assert_int32(0);
br.assert_int32(0);

meshes = []
faceSets = []
faceSetsDict = {}
vertexBuffers = []
vertexBuffersDict = {}
bufferLayouts = []
textures = []
for i in range(0, dummyCount):
    br.read_dummy()

for i in range(0, materialCount):
    br.read_material()

for i in range(0, boneCount):
    br.read_bones()

for i in range(0, meshCount):
    meshes.append(br.read_meshes(version))

for i in range(0, faceSetCount):
    faceset = br.read_face_set(dataOffset)
    faceSets.append(faceset)
    faceSetsDict[i] = faceset

for i in range(0, vertexBufferCount):
    vertexBuffer = br.read_vertex_buffer()
    vertexBuffers.append(vertexBuffer);
    vertexBuffersDict[i] = vertexBuffer

for i in range(0, bufferLayoutCount):
    bufferLayouts.append(br.read_buffer_layout());

for i in range(0, textureCount):
    textures.append(br.read_texture())

for mesh in meshes:
    mesh.take_face_sets(faceSetsDict)
    mesh.take_vertex_buffers(vertexBuffersDict)
    br.read_vertices(mesh, bufferLayouts, dataOffset, version)

print('end')
