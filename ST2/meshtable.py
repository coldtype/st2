# AUTOMATED FILE COPY
# Light riff on the sbix table from fontTools

from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval, num2binary, binary2num
from fontTools.ttLib.tables import DefaultTable
import struct

from fontTools.misc import sstruct
from fontTools.misc.textTools import readHex, safeEval
import struct


meshGlyphHeaderFormat = """
    >
    originOffsetX: h	# The x-value of the point in the glyph relative to its
                        # lower-left corner which corresponds to the origin of
                        # the glyph on the screen, that is the point on the
                        # baseline at the left edge of the glyph.
    originOffsetY: h	# The y-value of the point in the glyph relative to its
                        # lower-left corner which corresponds to the origin of
                        # the glyph on the screen, that is the point on the
                        # baseline at the left edge of the glyph.
    graphicType:  4s	# e.g. "png "
"""

meshGlyphHeaderFormatSize = sstruct.calcsize(meshGlyphHeaderFormat)


class Glyph(object):
    def __init__(self, glyphName=None, referenceGlyphName=None, originOffsetX=0, originOffsetY=0, graphicType=None, meshData=None, rawdata=None, gid=0):
        self.gid = gid
        self.glyphName = glyphName
        self.referenceGlyphName = referenceGlyphName
        self.originOffsetX = originOffsetX
        self.originOffsetY = originOffsetY
        self.rawdata = rawdata
        self.graphicType = graphicType
        self.meshData = meshData

        # fix self.graphicType if it is null terminated or too short
        if self.graphicType is not None:
            if self.graphicType[-1] == "\0":
                self.graphicType = self.graphicType[:-1]
            if len(self.graphicType) > 4:
                from fontTools import ttLib
                raise ttLib.TTLibError("Glyph.graphicType must not be longer than 4 characters.")
            elif len(self.graphicType) < 4:
                # pad with spaces
                self.graphicType += "    "[:(4 - len(self.graphicType))]

    def decompile(self, ttFont):
        #print("DECOMPILING", self.rawdata)
        self.glyphName = ttFont.getGlyphName(self.gid)
        if self.rawdata is None:
            from fontTools import ttLib
            raise ttLib.TTLibError("No table data to decompile")
        if len(self.rawdata) > 0:
            if len(self.rawdata) < meshGlyphHeaderFormatSize:
                from fontTools import ttLib
                #print "Glyph %i header too short: Expected %x, got %x." % (self.gid, meshGlyphHeaderFormatSize, len(self.rawdata))
                raise ttLib.TTLibError("Glyph header too short.")

            sstruct.unpack(meshGlyphHeaderFormat, self.rawdata[:meshGlyphHeaderFormatSize], self)

            if self.graphicType == "dupe":
                # this glyph is a reference to another glyph's image data
                gid, = struct.unpack(">H", self.rawdata[meshGlyphHeaderFormatSize:])
                self.referenceGlyphName = ttFont.getGlyphName(gid)
            else:
                self.meshData = self.rawdata[meshGlyphHeaderFormatSize:]
                self.referenceGlyphName = None
        # clean up
        del self.rawdata
        del self.gid

    def compile(self, ttFont):
        if self.glyphName is None:
            from fontTools import ttLib
            raise ttLib.TTLibError("Can't compile Glyph without glyph name")
            # TODO: if ttFont has no maxp, cmap etc., ignore glyph names and compile by index?
            # (needed if you just want to compile the mesh table on its own)
        self.gid = struct.pack(">H", ttFont.getGlyphID(self.glyphName))
        if self.graphicType is None:
            self.rawdata = b""
        else:
            self.rawdata = sstruct.pack(meshGlyphHeaderFormat, self) + self.meshData

    def toXML(self, xmlWriter, ttFont):
        if self.graphicType == None:
            # TODO: ignore empty glyphs?
            # a glyph data entry is required for each glyph,
            # but empty ones can be calculated at compile time
            xmlWriter.simpletag("glyph", name=self.glyphName)
            xmlWriter.newline()
            return
        xmlWriter.begintag("glyph",
            graphicType=self.graphicType,
            name=self.glyphName,
            originOffsetX=self.originOffsetX,
            originOffsetY=self.originOffsetY,
        )
        xmlWriter.newline()
        if self.graphicType == "dupe":
            # graphicType == "dupe" is a reference to another glyph id.
            xmlWriter.simpletag("ref", glyphname=self.referenceGlyphName)
        else:
            xmlWriter.begintag("hexdata")
            xmlWriter.newline()
            xmlWriter.dumphex(self.meshData)
            xmlWriter.endtag("hexdata")
        xmlWriter.newline()
        xmlWriter.endtag("glyph")
        xmlWriter.newline()

    def fromXML(self, name, attrs, content, ttFont):
        if name == "ref":
            # glyph is a "dupe", i.e. a reference to another glyph's image data.
            # in this case meshData contains the glyph id of the reference glyph
            # get glyph id from glyphname
            self.meshData = struct.pack(">H", ttFont.getGlyphID(safeEval("'''" + attrs["glyphname"] + "'''")))
        elif name == "hexdata":
            self.meshData = readHex(content)
        else:
            from fontTools import ttLib
            raise ttLib.TTLibError("can't handle '%s' element" % name)


meshStrikeHeaderFormat = """
    >
    ppem:          H	# The PPEM for which this strike was designed (e.g., 9,
                        # 12, 24)
    resolution:    H	# The screen resolution (in dpi) for which this strike
                        # was designed (e.g., 72)
"""

meshGlyphDataOffsetFormat = """
    >
    glyphDataOffset:   L	# Offset from the beginning of the strike data record
                            # to data for the individual glyph
"""

meshStrikeHeaderFormatSize = sstruct.calcsize(meshStrikeHeaderFormat)
meshGlyphDataOffsetFormatSize = sstruct.calcsize(meshGlyphDataOffsetFormat)


class Strike(object):
    def __init__(self, rawdata=None, ppem=0, resolution=72):
        self.data = rawdata
        self.ppem = ppem
        self.resolution = resolution
        self.glyphs = {}

    def decompile(self, ttFont):
        if self.data is None:
            from fontTools import ttLib
            raise ttLib.TTLibError
        if len(self.data) < meshStrikeHeaderFormatSize:
            from fontTools import ttLib
            raise(ttLib.TTLibError, "Strike header too short: Expected %x, got %x.") \
                % (meshStrikeHeaderFormatSize, len(self.data))

        # read Strike header from raw data
        sstruct.unpack(meshStrikeHeaderFormat, self.data[:meshStrikeHeaderFormatSize], self)

        # calculate number of glyphs
        firstGlyphDataOffset, = struct.unpack(">L", \
            self.data[meshStrikeHeaderFormatSize:meshStrikeHeaderFormatSize + meshGlyphDataOffsetFormatSize])
        self.numGlyphs = (firstGlyphDataOffset - meshStrikeHeaderFormatSize) // meshGlyphDataOffsetFormatSize - 1
        # ^ -1 because there's one more offset than glyphs

        # build offset list for single glyph data offsets
        self.glyphDataOffsets = []
        for i in range(self.numGlyphs + 1): # + 1 because there's one more offset than glyphs
            start = i * meshGlyphDataOffsetFormatSize + meshStrikeHeaderFormatSize
            current_offset, = struct.unpack(">L", self.data[start:start + meshGlyphDataOffsetFormatSize])
            self.glyphDataOffsets.append(current_offset)

        # iterate through offset list and slice raw data into glyph data records
        for i in range(self.numGlyphs):
            current_glyph = Glyph(rawdata=self.data[self.glyphDataOffsets[i]:self.glyphDataOffsets[i+1]], gid=i)
            current_glyph.decompile(ttFont)
            self.glyphs[current_glyph.glyphName] = current_glyph
        del self.glyphDataOffsets
        del self.numGlyphs
        del self.data

    def compile(self, ttFont):
        self.glyphDataOffsets = b""
        self.bitmapData = b""

        glyphOrder = ttFont.getGlyphOrder()

        # first glyph starts right after the header
        currentGlyphDataOffset = meshStrikeHeaderFormatSize + meshGlyphDataOffsetFormatSize * (len(glyphOrder) + 1)
        for glyphName in glyphOrder:
            if glyphName in self.glyphs:
                # we have glyph data for this glyph
                current_glyph = self.glyphs[glyphName]
            else:
                # must add empty glyph data record for this glyph
                current_glyph = Glyph(glyphName=glyphName)
            current_glyph.compile(ttFont)
            current_glyph.glyphDataOffset = currentGlyphDataOffset
            self.bitmapData += current_glyph.rawdata
            currentGlyphDataOffset += len(current_glyph.rawdata)
            self.glyphDataOffsets += sstruct.pack(meshGlyphDataOffsetFormat, current_glyph)

        # add last "offset", really the end address of the last glyph data record
        dummy = Glyph()
        dummy.glyphDataOffset = currentGlyphDataOffset
        self.glyphDataOffsets += sstruct.pack(meshGlyphDataOffsetFormat, dummy)

        # pack header
        self.data = sstruct.pack(meshStrikeHeaderFormat, self)
        # add offsets and image data after header
        self.data += self.glyphDataOffsets + self.bitmapData

    def toXML(self, xmlWriter, ttFont):
        xmlWriter.begintag("strike")
        xmlWriter.newline()
        xmlWriter.simpletag("ppem", value=self.ppem)
        xmlWriter.newline()
        xmlWriter.simpletag("resolution", value=self.resolution)
        xmlWriter.newline()
        glyphOrder = ttFont.getGlyphOrder()
        for i in range(len(glyphOrder)):
            if glyphOrder[i] in self.glyphs:
                self.glyphs[glyphOrder[i]].toXML(xmlWriter, ttFont)
                # TODO: what if there are more glyph data records than (glyf table) glyphs?
        xmlWriter.endtag("strike")
        xmlWriter.newline()

    def fromXML(self, name, attrs, content, ttFont):
        if name in ["ppem", "resolution"]:
            setattr(self, name, safeEval(attrs["value"]))
        elif name == "glyph":
            if "graphicType" in attrs:
                myFormat = safeEval("'''" + attrs["graphicType"] + "'''")
            else:
                myFormat = None
            if "glyphname" in attrs:
                myGlyphName = safeEval("'''" + attrs["glyphname"] + "'''")
            elif "name" in attrs:
                myGlyphName = safeEval("'''" + attrs["name"] + "'''")
            else:
                from fontTools import ttLib
                raise ttLib.TTLibError("Glyph must have a glyph name.")
            if "originOffsetX" in attrs:
                myOffsetX = safeEval(attrs["originOffsetX"])
            else:
                myOffsetX = 0
            if "originOffsetY" in attrs:
                myOffsetY = safeEval(attrs["originOffsetY"])
            else:
                myOffsetY = 0
            current_glyph = Glyph(
                glyphName=myGlyphName,
                graphicType=myFormat,
                originOffsetX=myOffsetX,
                originOffsetY=myOffsetY,
            )
            for element in content:
                if isinstance(element, tuple):
                    name, attrs, content = element
                    current_glyph.fromXML(name, attrs, content, ttFont)
                    current_glyph.compile(ttFont)
            self.glyphs[current_glyph.glyphName] = current_glyph
        else:
            from fontTools import ttLib
            raise ttLib.TTLibError("can't handle '%s' element" % name)



meshHeaderFormat = """
    >
    version:       H	# Version number (set to 1)
    flags:         H	# The only two bits used in the flags field are bits 0
                        # and 1. For historical reasons, bit 0 must always be 1.
                        # Bit 1 is a meshDrawOutlines flag and is interpreted as
                        # follows:
                        #     0: Draw only 'mesh' bitmaps
                        #     1: Draw both 'mesh' bitmaps and outlines, in that
                        #        order
    numStrikes:    L	# Number of bitmap strikes to follow
"""
meshHeaderFormatSize = sstruct.calcsize(meshHeaderFormat)


meshStrikeOffsetFormat = """
    >
    strikeOffset:  L	# Offset from begining of table to data for the
                        # individual strike
"""
meshStrikeOffsetFormatSize = sstruct.calcsize(meshStrikeOffsetFormat)


class table__M_E_S_H(DefaultTable.DefaultTable):

    def __init__(self, tag=None):
        DefaultTable.DefaultTable.__init__(self, tag)
        self.version = 1
        self.flags = 1
        self.numStrikes = 0
        self.strikes = {}
        self.strikeOffsets = []

    def decompile(self, data, ttFont):
        # read table header
        sstruct.unpack(meshHeaderFormat, data[ : meshHeaderFormatSize], self)
        # collect offsets to individual strikes in self.strikeOffsets
        for i in range(self.numStrikes):
            current_offset = meshHeaderFormatSize + i * meshStrikeOffsetFormatSize
            offset_entry = meshStrikeOffset()
            sstruct.unpack(meshStrikeOffsetFormat, \
                data[current_offset:current_offset+meshStrikeOffsetFormatSize], \
                offset_entry)
            self.strikeOffsets.append(offset_entry.strikeOffset)

        # decompile Strikes
        for i in range(self.numStrikes-1, -1, -1):
            current_strike = Strike(rawdata=data[self.strikeOffsets[i]:])
            data = data[:self.strikeOffsets[i]]
            current_strike.decompile(ttFont)
            #print "  Strike length: %xh" % len(bitmapSetData)
            #print "Number of Glyph entries:", len(current_strike.glyphs)
            if current_strike.ppem in self.strikes:
                from fontTools import ttLib
                raise ttLib.TTLibError("Pixel 'ppem' must be unique for each Strike")
            self.strikes[current_strike.ppem] = current_strike

        # after the glyph data records have been extracted, we don't need the offsets anymore
        del self.strikeOffsets
        del self.numStrikes

    def compile(self, ttFont):
        meshData = b""
        self.numStrikes = len(self.strikes)
        meshHeader = sstruct.pack(meshHeaderFormat, self)

        # calculate offset to start of first strike
        setOffset = meshHeaderFormatSize + meshStrikeOffsetFormatSize * self.numStrikes

        for si in sorted(self.strikes.keys()):
            current_strike = self.strikes[si]
            current_strike.compile(ttFont)
            # append offset to this strike to table header
            current_strike.strikeOffset = setOffset
            meshHeader += sstruct.pack(meshStrikeOffsetFormat, current_strike)
            setOffset += len(current_strike.data)
            meshData += current_strike.data

        return meshHeader + meshData

    def toXML(self, xmlWriter, ttFont):
        xmlWriter.simpletag("version", value=self.version)
        xmlWriter.newline()
        xmlWriter.simpletag("flags", value=num2binary(self.flags, 16))
        xmlWriter.newline()
        for i in sorted(self.strikes.keys()):
            self.strikes[i].toXML(xmlWriter, ttFont)

    def fromXML(self, name, attrs, content, ttFont):
        if name =="version":
            setattr(self, name, safeEval(attrs["value"]))
        elif name == "flags":
            setattr(self, name, binary2num(attrs["value"]))
        elif name == "strike":
            current_strike = Strike()
            for element in content:
                if isinstance(element, tuple):
                    name, attrs, content = element
                    current_strike.fromXML(name, attrs, content, ttFont)
            self.strikes[current_strike.ppem] = current_strike
        else:
            from fontTools import ttLib
            raise ttLib.TTLibError("can't handle '%s' element" % name)


# Helper classes

class meshStrikeOffset(object):
    pass