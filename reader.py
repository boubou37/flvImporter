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
            result.append(function)
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
    def readDummy(self):
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

    def readMaterial(self):
        nameOffset = self.read_int32();
        mtdOffset = self.read_int32();
        textureCount = self.read_int32();
        textureIndex = self.read_int32();
        Flags = self.read_int32();
        gxOffset = self.read_int32();
        Unk18 = self.read_int32();
        self.assert_int32(0);

        Name = self.get_utf16(nameOffset);
        MTD = self.get_utf16(mtdOffset);

        if gxOffset > 0:
            self.step_in(gxOffset)
            while True:
                section = self.read_int32()
                self.read_int32()
                self.skip(self.read_int32() - 0xC)
                if section == 0x7FFFFFFF:
                    break;

            gxbytes = self.get_bytes(gxOffset, self.stream.tell() - gxOffset)
            self.step_out()

    def readBones(self):
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

    def readMeshes(self, version):
        Dynamic = self.read_bool();
        self.assert_byte(0);
        self.assert_byte(0);
        self.assert_byte(0);

        MaterialIndex = self.read_int32();
        self.assert_int32(0);
        if version <= 0x20010:
            self.assert_int32(0);
        DefaultBoneIndex = self.read_int32();

        boneCount = self.read_int32();
        Unk1 = self.assert_int32(0, 1, 10);
        if version >= 0x20013:
            boundingBoxOffset = self.read_int32();
            self.step_in(boundingBoxOffset);
            BoundingBoxMin = self.read_vector3();
            BoundingBoxMax = self.read_vector3();
            if version >= 0x2001A:
                BoundingBoxUnk = self.read_vector3();
            self.step_out();
        boneOffset = self.read_int32();
        BoneIndices = self.get_int32s(boneOffset, boneCount);

        faceSetCount = self.read_int32();
        faceSetOffset = self.read_int32();
        faceSetIndices = self.get_int32s(faceSetOffset, faceSetCount);

        vertexBufferCount = self.assert_int32(1, 2, 3);
        vertexBufferOffset = self.read_int32();
        vertexBufferIndices = self.get_int32s(vertexBufferOffset, vertexBufferCount)

    def readFaceSets(self, dataOffset):
        Flags = self.read_uint32();

        TriangleStrip = self.read_bool();
        CullBackfaces = self.read_bool();
        Unk06 = self.read_byte();
        Unk07 = self.read_byte();

        vertexCount = self.read_int32();
        vertexOffset = self.read_int32();
        vertexSize = self.read_int32();

        self.assert_int32(0);
        IndexSize = self.assert_int32(0, 16, 32);
        self.assert_int32(0);

        if IndexSize == 0 or IndexSize == 16:
            Vertices = self.get_uint16s(dataOffset + vertexOffset, vertexCount)
        elif IndexSize == 32:
            Vertices = self.get_uint32s(dataOffset + vertexOffset, vertexCount)

    def readVertexBuffers(self):
        BufferIndex = self.read_int32();
        LayoutIndex = self.read_int32();
        VertexSize = self.read_int32();
        VertexCount = self.read_int32();
        self.assert_int32(0);
        self.assert_int32(0);
        self.assert_int32(VertexSize * VertexCount);
        BufferOffset = self.read_int32();

    def readBufferLayouts(self):
        memberCount = self.read_int32();
        self.assert_int32(0);
        self.assert_int32(0);
        memberOffset = self.read_int32();
        self.step_in(memberOffset);
        for i in range(0, memberCount):
            self.readBuffLayoutMember()
        self.step_out();

    def readTextures(self):
        print()

    def readBuffLayoutMember(self):
        StructOffset = self.read_int32();
        Type = self.read_uint32()
        Semantic = self.read_uint32()
        Index = self.read_int32()

    def readTextures(self):
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
