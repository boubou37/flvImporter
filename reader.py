import string
import struct


class BinaryReader:
    def __init__(self, stream, endianness):
        self.stream = stream;
        self.positions = [];
        self.endianness = endianness

    def unpack(self, fmt, length=1):
        """
        Unpack the stream contents according to the specified format in `fmt`.
        For more information about the `fmt` format see: https://docs.python.org/3/library/struct.html
        Args:
            fmt (str): format string.
            length (int): amount of bytes to read.
        Returns:
            variable: the result according to the specified format.
        """
        return struct.unpack(fmt, self.stream.read(length))[0]

    def endian(self) -> string:
        if self.endianness == 'big':
            return '>'
        elif self.endianness == 'little':
            return '<'
        raise Exception('incorrectness endiannes')

    def assert_read(self, count, fmt, expected_values) -> int:
        value = self.unpack(fmt, count)
        for expected_value in expected_values:
            if value == expected_value:
                return value

        raise Exception('Failed value assertion read. Expected {}, got {}'.format(expected_value, value))

    def assert_int32(self, *expected_values) -> int:
        return self.assert_read(4, "%si" % self.endian(), expected_values)

    def assert_int16(self, *expected_values) -> int:
        return self.assert_read(2, "%sh" % self.endian(), expected_values)

    def assert_bool(self, *expected_values):
        return self.assert_read(1, "?", expected_values)

    def assert_byte(self, *expected_values) -> int:
        return self.assert_read(1, "B", expected_values)

    def read_byte(self):
        return self.unpack("B", 1)

    def read_int32(self) -> int:
        return self.unpack("%si" % self.endian(), 4)

    def read_uint16(self) -> int:
        return self.unpack("%sH" % self.endian(), 4)

    def read_uint32(self) -> int:
        return self.unpack("%sI" % self.endian(), 4)

    def read_int16(self) -> int:
        return self.unpack('%sh' % self.endian(), 2)

    def read_bool(self) -> bool:
        return self.unpack('?')

    def read_float(self) -> float:
        return self.unpack("%sf" % self.endian(), 4)

    def skip(self, count):
        self.stream.seek(count, 1)

    def get_bytes(self, offset, count):
        self.step_in(offset)
        result = self.read_bytes(count)
        self.step_out()
        return result;

    def get_int32s(self, offset, count):
        return self.get_values(self.read_int32, offset, count)

    def get_uint32s(self, offset, count):
        return self.get_values(self.read_int32, offset, count)

    def get_uint16s(self, offset, count):
        return self.get_values(self.read_int16, offset, count)

    def get_values(self, function, offset, count):
        self.step_in(offset)
        result = []
        for i in range(0, count):
            result.append(function())
        self.step_out()
        return result;

    def read_bytes(self, count):
        bytes = bytearray(self.stream.read(count));
        return bytes;

    def read_utf16(self):
        bytes = b'';
        bytePair = self.stream.read(2)
        while bytePair[0] != 0 or bytePair[1] != 0:
            bytes = bytes + bytePair
            bytePair = self.stream.read(2)

        encoding = ''
        if self.endianness == 'big':
            encoding = 'utf-16be'
        elif self.endianness == 'little':
            encoding = 'utf-16le'

        result = bytes.decode(encoding)
        return result;

    def get_utf16(self, offset) -> string:
        startPos = self.stream.tell();
        self.stream.seek(offset);
        result = self.read_utf16();
        self.stream.seek(startPos)
        return result;

    def step_in(self, offset):
        self.positions.append(self.stream.tell())
        self.stream.seek(offset)

    def step_out(self):
        if (len(self.positions) <= 0):
            raise Exception('No positions found on position stack')
        position = self.positions.pop()
        self.stream.seek(position)

    def read_vector3(self):
        x = self.read_float()
        y = self.read_float()
        z = self.read_float()
        return [x, y, z]


class FlvReader(BinaryReader):
    def read_dummy(self):
        Position = self.read_vector3();

        Unk0C = self.read_byte();
        Unk0D = self.read_byte();
        Unk0E = self.read_int16();

        Forward = self.read_vector3();

        ReferenceID = self.read_int16();
        DummyBoneIndex = self.read_int16();

        Upward = self.read_vector3();

        AttachBoneIndex = self.read_int16();
        Flag1 = self.read_boolean();
        Flag2 = self.read_boolean();

        Unk30 = self.read_int32();
        Unk34 = self.read_int32();
        self.assert_int32(0);
        self.assert_int32(0);

    def read_material(self):
        material = Material();
        material.nameOffset = self.read_int32();
        material.mtdOffset = self.read_int32();
        material.textureCount = self.read_int32();
        material.textureIndex = self.read_int32();
        material.flags = self.read_int32();
        material.gxOffset = self.read_int32();
        material.unk18 = self.read_int32();
        self.assert_int32(0);

        material.name = self.get_utf16(material.nameOffset);
        material.mtd = self.get_utf16(material.mtdOffset);

        if material.gxOffset > 0:
            self.step_in(material.gxOffset)
            while True:
                section = self.read_int32()
                self.read_int32()
                self.skip(self.read_int32() - 0xC)
                if section == 0x7FFFFFFF:
                    break;

            gxbytes = self.get_bytes(material.gxOffset, self.stream.tell() - material.gxOffset)
            material.gxbytes = gxbytes
            self.step_out()
        return material

    def read_bones(self):
        Translation = self.read_vector3();
        nameOffset = self.read_int32();
        Rotation = self.read_vector3();
        ParentIndex = self.read_int16();
        ChildIndex = self.read_int16();
        Scale = self.read_vector3();
        NextSiblingIndex = self.read_int16();
        PreviousSiblingIndex = self.read_int16();
        BoundingBoxMin = self.read_vector3();
        Unk3C = self.read_int32();
        BoundingBoxMax = self.read_vector3();

        self.assert_int32(0);
        self.assert_int32(0);
        self.assert_int32(0);
        self.assert_int32(0);
        self.assert_int32(0);
        self.assert_int32(0);
        self.assert_int32(0);
        self.assert_int32(0);
        self.assert_int32(0);
        self.assert_int32(0);
        self.assert_int32(0);
        self.assert_int32(0);
        self.assert_int32(0);
        Name = self.get_utf16(nameOffset)

    def read_meshes(self, version):
        mesh = Mesh()
        mesh.dynamic = self.read_bool();
        self.assert_byte(0);
        self.assert_byte(0);
        self.assert_byte(0);

        mesh.materialIndex = self.read_int32();
        self.assert_int32(0);
        if version <= 0x20010:
            self.assert_int32(0);
        mesh.defaultBoneIndex = self.read_int32();

        mesh.boneCount = self.read_int32();
        mesh.unk1 = self.assert_int32(0, 1, 10);
        if version >= 0x20013:
            mesh.boundingBoxOffset = self.read_int32();
            self.step_in(mesh.boundingBoxOffset);
            mesh.boundingBoxMin = self.read_vector3();
            mesh.boundingBoxMax = self.read_vector3();
            if version >= 0x2001A:
                mesh.boundingBoxUnk = self.read_vector3();
            self.step_out();
        mesh.boneOffset = self.read_int32();
        mesh.boneIndices = self.get_int32s(mesh.boneOffset, mesh.boneCount);

        mesh.faceSetCount = self.read_int32();
        mesh.faceSetOffset = self.read_int32();
        mesh.faceSetIndices = self.get_int32s(mesh.faceSetOffset, mesh.faceSetCount);

        mesh.vertexBufferCount = self.assert_int32(1, 2, 3);
        mesh.vertexBufferOffset = self.read_int32();
        mesh.vertexBufferIndices = self.get_int32s(mesh.vertexBufferOffset, mesh.vertexBufferCount)
        return mesh

    def read_face_set(self, dataOffset):
        faceSet = FaceSet()
        faceSet.flags = self.read_uint32();

        faceSet.triangleStrip = self.read_bool();
        faceSet.cullBackfaces = self.read_bool();
        faceSet.unk06 = self.read_byte();
        faceSet.unk07 = self.read_byte();

        faceSet.vertexCount = self.read_int32();
        faceSet.vertexOffset = self.read_int32();
        faceSet.vertexSize = self.read_int32();

        self.assert_int32(0);
        faceSet.indexSize = self.assert_int32(0, 16, 32);
        self.assert_int32(0);

        if faceSet.indexSize == 0 or faceSet.indexSize == 16:
            faceSet.vertices = self.get_uint16s(dataOffset + faceSet.vertexOffset, faceSet.vertexCount)
        elif faceSet.indexSize == 32:
            faceSet.vertices = self.get_uint32s(dataOffset + faceSet.vertexOffset, faceSet.vertexCount)

        return faceSet

    def read_vertex_buffer(self):
        vBuffer = VertexBuffer();
        vBuffer.bufferIndex = self.read_int32();
        vBuffer.layoutIndex = self.read_int32();
        vBuffer.vertexSize = self.read_int32();
        vBuffer.vertexCount = self.read_int32();
        self.assert_int32(0);
        self.assert_int32(0);
        self.assert_int32(vBuffer.vertexSize * vBuffer.vertexCount);
        vBuffer.bufferOffset = self.read_int32();
        return vBuffer

    def read_buffer_layout(self):
        bufferLayout = BufferLayout();
        bufferLayout.memberCount = self.read_int32();
        self.assert_int32(0);
        self.assert_int32(0);
        bufferLayout.memberOffset = self.read_int32();
        self.step_in(bufferLayout.memberOffset);
        for i in range(0, bufferLayout.memberCount):
            bufferLayout.members.append(self.read_buff_layout_member())
        self.step_out();
        return bufferLayout

    def read_buff_layout_member(self):
        buffLayoutMember = BufferLayoutMember();
        buffLayoutMember.structOffset = self.read_int32();
        buffLayoutMember.type = self.read_uint32()
        buffLayoutMember.semantic = self.read_uint32()
        buffLayoutMember.index = self.read_int32()
        return buffLayoutMember

    def read_texture(self):
        pathOffset = self.read_int32();
        typeOffset = self.read_int32();
        ScaleX = self.read_float();
        ScaleY = self.read_float();

        Unk10 = self.assert_byte(0, 1, 2);
        Unk11 = self.read_bool();
        self.assert_byte(0);
        self.assert_byte(0);

        Unk14 = self.read_int32();
        Unk18 = self.read_int32();
        Unk1C = self.read_int32();

        Type = self.get_utf16(typeOffset);
        Path = self.get_utf16(pathOffset)

    def read_vertices(self, mesh, bufferLayouts, dataOffset, version):
        vertexCount = len(mesh.vertexBuffers[0].vertexCount)
        for vertexBuffer in mesh.vertexBuffers:
            layout = bufferLayouts[vertexBuffer.layoutIndex]
            self.step_in(dataOffset + vertexBuffer.bufferOffset)
            for i in range(0, vertexCount):
                self.read_vertex(layout, vertexBuffer, version)
            self.step_out()

    #def readBuffer(self, vertexBuffer, bufferLayouts, dataOffset, version):
    #    print()

    def read_vertex(self, layout, vertexBuffer, version):
        pass


class Material:
    def __init__(self):
        self.nameOffset = 0;
        self.mtdOffset = 0;
        self.textureCount = 0;
        self.textureIndex = 0;
        self.flags = 0;
        self.gxOffset = 0;
        self.unk18 = 0;
        self.name = '';
        self.mtd = '';
        self.gxbytes = []


class VertexBuffer:
    def __init__(self):
        self.bufferIndex = 0;
        self.layoutIndex = 0;
        self.vertexSize = 0;
        self.vertexCount = 0;
        self.bufferOffset = 0;


class BufferLayout:
    def __init__(self):
        self.memberCount = 0;
        self.memberOffset = 0
        self.members = []


class BufferLayoutMember:
    def __init__(self):
        self.structOffset = 0;
        self.type = 0;
        self.semantic = 0;
        self.index = 0;


class Mesh:
    def __init__(self):
        self.dynamic = False
        self.materialIndex = 0
        self.defaultBoneIndex = 0
        self.boneCount = 0
        self.unk1 = 0
        self.boundingBoxOffset = 0
        self.boundingBoxMin = []
        self.boundingBoxMax = []
        self.boundingBoxUnk = []
        self.faceSets = []
        self.vertexBuffers = []
        self.vertices = []
        self.boneOffset = 0
        self.boneIndices = []
        self.faceSetCount = 0
        self.faceSetOffset = 0
        self.faceSetIndices = []
        self.vertexBufferCount = 0
        self.vertexBufferOffset = 0
        self.vertexBufferIndices = []

    def take_face_sets(self, faceSetsDict):
        for i in self.faceSetIndices:
            self.faceSets.append(faceSetsDict[i])

    def take_vertex_buffers(self, vertexBufferDict):
        for i in self.vertexBufferIndices:
            self.vertexBuffers.append(vertexBufferDict[i])


class FaceSet:
    def __init__(self):
        self.flags = 0;
        self.triangleStrip = False;
        self.cullBackfaces = False;
        self.unk06 = 0;
        self.unk07 = 0;
        self.vertexCount = 0;
        self.vertexOffset = 0;
        self.vertexSize = 0;
        self.indexSize = 0
        self.vertices = 0
