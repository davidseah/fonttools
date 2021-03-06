from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
from fontTools.misc.fixedTools import (
	ensureVersionIsLong as fi2ve, versionToFixed as ve2fi)
from . import DefaultTable
import math


hheaFormat = """
		>  # big endian
		tableVersion:           L
		ascent:                 h
		descent:                h
		lineGap:                h
		advanceWidthMax:        H
		minLeftSideBearing:     h
		minRightSideBearing:    h
		xMaxExtent:             h
		caretSlopeRise:         h
		caretSlopeRun:          h
		caretOffset:            h
		reserved0:              h
		reserved1:              h
		reserved2:              h
		reserved3:              h
		metricDataFormat:       h
		numberOfHMetrics:       H
"""


class table__h_h_e_a(DefaultTable.DefaultTable):

	# Note: Keep in sync with table__v_h_e_a

	dependencies = ['hmtx', 'glyf', 'CFF ']

	def decompile(self, data, ttFont):
		sstruct.unpack(hheaFormat, data, self)

	def compile(self, ttFont):
		if ttFont.recalcBBoxes and (ttFont.isLoaded('glyf') or ttFont.isLoaded('CFF ')):
			self.recalc(ttFont)
		self.tableVersion = fi2ve(self.tableVersion)
		return sstruct.pack(hheaFormat, self)

	def recalc(self, ttFont):
		if 'hmtx' in ttFont:
			hmtxTable = ttFont['hmtx']
			self.advanceWidthMax = max(adv for adv, _ in hmtxTable.metrics.values())

		boundsWidthDict = {}
		if 'glyf' in ttFont:
			glyfTable = ttFont['glyf']
			for name in ttFont.getGlyphOrder():
				g = glyfTable[name]
				if g.numberOfContours == 0:
					continue
				if g.numberOfContours < 0 and not hasattr(g, "xMax"):
					# Composite glyph without extents set.
					# Calculate those.
					g.recalcBounds(glyfTable)
				boundsWidthDict[name] = g.xMax - g.xMin
		elif 'CFF ' in ttFont:
			topDict = ttFont['CFF '].cff.topDictIndex[0]
			for name in ttFont.getGlyphOrder():
				cs = topDict.CharStrings[name]
				bounds = cs.calcBounds()
				if bounds is not None:
					boundsWidthDict[name] = int(
						math.ceil(bounds[2]) - math.floor(bounds[0]))

		if boundsWidthDict:
			minLeftSideBearing = float('inf')
			minRightSideBearing = float('inf')
			xMaxExtent = -float('inf')
			for name, boundsWidth in boundsWidthDict.items():
				advanceWidth, lsb = hmtxTable[name]
				rsb = advanceWidth - lsb - boundsWidth
				extent = lsb + boundsWidth
				minLeftSideBearing = min(minLeftSideBearing, lsb)
				minRightSideBearing = min(minRightSideBearing, rsb)
				xMaxExtent = max(xMaxExtent, extent)
			self.minLeftSideBearing = minLeftSideBearing
			self.minRightSideBearing = minRightSideBearing
			self.xMaxExtent = xMaxExtent

		else:  # No glyph has outlines.
			self.minLeftSideBearing = 0
			self.minRightSideBearing = 0
			self.xMaxExtent = 0

	def toXML(self, writer, ttFont):
		formatstring, names, fixes = sstruct.getformat(hheaFormat)
		for name in names:
			value = getattr(self, name)
			if name == "tableVersion":
				value = fi2ve(value)
				value = "0x%08x" % value
			writer.simpletag(name, value=value)
			writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		if name == "tableVersion":
			setattr(self, name, ve2fi(attrs["value"]))
			return
		setattr(self, name, safeEval(attrs["value"]))
