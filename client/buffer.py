import os
class ReadBuffer:
	def __init__(self, inFile, bufferSize):
		self.fIn = open(inFile, "rb")
		self.bufferSize = bufferSize
		self.buffer = self.fIn.read(self.bufferSize)
		self.bufferPos = 0
		self.pos = 0
		self.filesize = os.stat(inFile).st_size
	def seek(self, pos):
		self.bufferPos = pos
		self.fIn.seek(pos)
		self.buffer = self.fIn.read(self.bufferSize)
	def read(self, size):
		ba = bytearray()
		if (self.pos+size > self.filesize):
			size = self.filesize-self.pos
		if (size == 0):
			return ba
		if (self.pos+size > self.bufferPos+self.bufferSize):
			for i in range(self.bufferPos+self.bufferSize-self.pos):
				ba.append(self.buffer[i+self.pos-self.bufferPos])
			self.seek(self.bufferPos+self.bufferSize)#TODO ensure buffer contains all data (size<=bufferSize)
			for i in range(self.pos+size-self.bufferPos):
				ba.append(self.buffer[i])
		else:
			for i in range(size):
				ba.append(self.buffer[i+self.pos-self.bufferPos])
		self.pos = self.pos+size
		return ba
	def close(self):
		self.fIn.close()
class WriteBuffer:
	def __init__(self, outFile, bufferSize):
		self.bufferSize = bufferSize
		self.buffer = bytearray()
		self.size = 0
		self.fOut = open(outFile, "wb")
	def write(self, data):
		for d in data:
			self.buffer.append(d)
		self.size += len(data)
		if (self.size > self.bufferSize):
			self.fOut.write(self.buffer)
			self.size = 0
			self.buffer = bytearray()
	def close(self):
		self.fOut.write(self.buffer)
		self.fOut.close()
	def seek(self, pos):
		self.fOut.write(self.buffer)
		self.fOut.seek(pos)
class Compressor:
	def __init__(self):
		self.dict = {}
		self.uncompressDict = {}
		for i in range(256):
			self.dict[(i,)] = [-1, i]
			self.uncompressDict[i] = [-1, (i,)]
		self.size = 256
		self.maxSize = 256*128
	def compressFile(self, inFile, outFile=""):
		if (outFile == ""):
			outFile = inFile+".compressed"
		readBuffer = ReadBuffer(inFile, 1024)
		writeBuffer = WriteBuffer(outFile, 1024)
		bytes = ()
		while (True):
			readBytes = readBuffer.read(1)
			if (len(readBytes) == 0):
				prev = self.dict[bytes][1]
				ba = bytearray()
				ba.append(prev>>8)
				ba.append(prev&255)
				writeBuffer.write(ba)
				break
			bytes += (readBytes[0],)
			if (bytes not in self.dict):
				if (self.size == self.maxSize):
					prev = self.dict[bytes[:-1]][1]
					ba = bytearray()
					ba.append(prev>>8)
					ba.append(prev&255)
					writeBuffer.write(ba)
					bytes = bytes[-1:]
				else:
					prev = self.dict[bytes[:-1]][1]
					self.dict[bytes] = [prev, self.size]
					self.size += 1
					ba = bytearray()
					ba.append((prev>>8)|128)
					ba.append(prev&255)
					ba.append(bytes[-1:][0])
					writeBuffer.write(ba)
					bytes = ()
		readBuffer.close()
		writeBuffer.close()
	def uncompressFile(self, inFile, outFile=""):
		if (outFile == ""):
			outFile = inFile[:-11]
		readBuffer = ReadBuffer(inFile, 1024)
		writeBuffer = WriteBuffer(outFile, 1024)
		while (True):
			ba = bytearray()
			readBytes = readBuffer.read(1)
			if (len(readBytes) == 0):
				break
			ba.append(readBytes[0])
			ba.append(readBuffer.read(1)[0])
			if ((readBytes[0]) & 128):
				ba.append(readBuffer.read(1)[0])
				prev = ((ba[0]) & 127)<<8
				prev += ba[1]
				bytes = self.uncompressDict[prev][1]
				bytes += (ba[2],)
				self.uncompressDict[self.size] = [prev, bytes]
				self.size += 1
				ba = bytearray()
				for b in bytes:
					ba.append(b)
				writeBuffer.write(ba)
			else:
				index = (ba[0])<<8
				index += ba[1]
				bytes = self.uncompressDict[index][1]
				ba = bytearray()
				for b in bytes:
					ba.append(b)
				writeBuffer.write(ba)
		readBuffer.close()
		writeBuffer.close()
		for key in self.uncompressDict:
			print(self.uncompressDict[key][1])
compressor = Compressor()
compressor.compressFile("test.txt", "test.c")
compressor = Compressor()
compressor.uncompressFile("test.c", "test.un")