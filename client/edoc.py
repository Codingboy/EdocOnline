from random import randint
from copy import deepcopy
import argparse
import os
import logging
import shutil
import time
import math
import unittest
import sys
import threading

class ReadBuffer:
	"""
	ReadBuffer buffers reading of files.
		
	Attributes:
		fIn (file): filereference
		bufferSize (int): size of the buffer
		buffer (bytearray): buffer
		bufferPos (int): startposition of the buffer in the open file
		pos (int): position of the cursor in the open file
		filesize (int): size of the open file
		
	Parameters:
		inFile (string): path to file
		bufferSize (int): size of the buffer
		
	| **Pre:**
	|	os.path.isFile(inFile)
	|	self.bufferSize > 0
		
	| **Post:**
	|	self.fIn is open
	|	len(self.buffer) >= 0
	|	len(self.buffer) <= self.bufferSize
	|	isinstance(self.buffer[i], int)
	|	self.buffer[i] >= 0
	|	self.buffer[i] < 256
	|	self.bufferPos == 0
	|	self.pos == 0
	|	self.filesize == os.stat(inFile).st_size
	"""
	def __init__(self, inFile, bufferSize=1024):
		self.fIn = open(inFile, "rb")
		self.bufferSize = bufferSize
		self.buffer = self.fIn.read(self.bufferSize)
		self.bufferPos = 0
		self.pos = 0
		self.filesize = os.stat(inFile).st_size

	def seek(self, pos):
		"""
		Changes the cursorposition within a file.
			
		Parameters:
			pos (int): position
			
		| **Pre:**
		|	pos >= 0
		|	pos <= self.fileSize
		|	self.fIn is open
			
		| **Post:**
		|	self.bufferPos = pos
			
		| **Modifies:**
		|	self.bufferPos
		|	self.buffer[i]
		|	self.fIn
		"""
		self.bufferPos = pos
		self.fIn.seek(pos)
		self.buffer = self.fIn.read(self.bufferSize)

	def read(self, size):
		"""
		Reads data from file into buffer.
			
		Parameters:
			size (int): max number of bytes to be read
		
		Returns:
			bytearray: read bytes
			
		| **Pre:**
		|	size > 0
		|	size <= self.bufferSize
		|	self.fIn is open
			
		| **Post:**
		|	len(return) >= 0
		|	len(return) <= size
		|	isinstance(return[i], int)
		|	return[i] >= 0
		|	return[i] < 256
			
		| **Modifies:**
		|	self.bufferPos
		|	self.buffer[i]
		|	self.pos
		|	self.fIn
		"""
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
		"""
		Closes the file.
			
		| **Pre:**
		|	self.fIn is open
			
		| **Post:**
		|	self.fIn is closed
			
		| **Modifies:**
		|	self.fIn
		"""
		self.fIn.close()

class WriteBuffer:
	"""
	WriteBuffer buffers writing of files.
		
	Attributes:
		fOut (file): filereference
		bufferSize (int): size of the buffer
		buffer (bytearray): buffer
		size (int): actual size of the buffer
		
	Parameters:
		outFile (string): path to file
		bufferSize (int): size of the buffer
		
	| **Pre:**
	|	os.path.isFile(outFile)
	|	self.bufferSize > 0
		
	| **Post:**
	|	self.fOut is open
	|	len(self.buffer) >= 0
	|	len(self.buffer) <= self.bufferSize
	|	isinstance(self.buffer[i], int)
	|	self.buffer[i] >= 0
	|	self.buffer[i] < 256
	|	folders above outFile are created
	
	Note:
		self.size might be bigger sometimes than self.bufferSize
	"""
	def __init__(self, outFile, bufferSize=1024):
		self.bufferSize = bufferSize
		self.buffer = bytearray()
		self.size = 0
		index = outFile.rfind("/")
		if (index != -1):
			folder = outFile[:index]
			if (not os.path.exists(folder)):
				os.makedirs(folder)
		self.fOut = open(outFile, "wb")
	def write(self, data):
		"""
		Writes data into buffer and file.
			
		Parameters:
			data (bytearray): data to be written
			
		| **Pre:**
		|	self.fIn is open
		|	len(data) > 0
		|	isinstance(data[i], int)
		|	data[i] >= 0
		|	data[i] < 256
			
		| **Modifies:**
		|	self.size
		|	self.buffer[i]
		|	self.fOut
		"""
		for d in data:
			self.buffer.append(d)
		self.size += len(data)
		if (self.size > self.bufferSize):
			self.fOut.write(self.buffer)
			self.size = 0
			self.buffer = bytearray()
	def close(self):
		"""
		Closes the file and flushes the buffer.
			
		| **Pre:**
		|	self.fOut is open
			
		| **Post:**
		|	self.fOut is closed
			
		| **Modifies:**
		|	self.fOut
		"""
		self.fOut.write(self.buffer)
		self.fOut.close()
	def seek(self, pos):
		"""
		Changes the cursorposition within a file and flushes buffer.
			
		Parameters:
			pos (int): position
			
		| **Pre:**
		|	pos >= 0
		|	self.fIn is open
			
		| **Post:**
		|	self.buffer = bytearray()
			
		| **Modifies:**
		|	self.fOut
		|	self.buffer[i]
		"""
		self.fOut.write(self.buffer)
		self.buffer = bytearray()
		self.fOut.seek(pos)#TODO preconditions
class Archiver:
	def __init__(self, folder, deleteOnCompletion=False):
		self.readBuffer = None
		self.files = []
		if (os.path.isfile(file)):
			self.files = [folder]
		elif (os.path.isdir(file)):
			files = os.listdir(folder)
			for file in files:
				file = folder + "/" + file
				self.files.append(file)
		self.file = ""
		self.deleteOnCompletion = deleteOnCompletion
		self.readSize = 1024
	def read():
		ba = bytearray()
		if (self.readBuffer is None):
			while (True):
				if (len(self.files) == 0):
					break
				else:
					file = self.files.pop(0)
					if (os.path.isdir(file)):
						folder = file
						files = os.listdir(folder)
						for file in files:
							file = folder + "/" + file
							self.files.append(file)
					elif (os.path.isfile(file)):
						self.readBuffer = ReadBuffer(file)
						self.file = file
						length = len(file)
						ba.append(length>>8)
						ba.append(length&255)
						for c in file:
							ba.append(ord(c))
						fileSize = os.stat(file).st_size
						for i in range(8):
							ba.append((fileSize >> (8*(8-1-i))) & 255)
						break
		else:
			ba = self.readBuffer.read(self.readSize)
			if (len(ba) == 0):
				self.readBuffer.close()
				self.readBuffer = None
				if (self.deleteOnCompletion):
					os.remove(self.file)
				ba = self.read()
		return ba
class Dearchiver:
	def __init__(self, folder):
		self.writeBuffer = None
		self.filesize = 0
		self.buffer = None
		self.folder = folder
	def write(data):
		if (self.buffer is not None):
			data = self.buffer+data
			self.buffer = None
		dataLength = len(data)
		if (self.writeBuffer is None):
			if (dataLength >= 2):
				length = ((data[0])<<8) + data[1]
				if (dataLength >= 2+length):
					file = ""
					for i in range(length):
						file += chr(data[2+i])
					self.filesize = 0
					if (dataLength >= 2+length+8):
						for i in range(8):
							self.filesize += (data[2+length+i]) << (8*(8-1-i))
							self.writeBuffer = WriteBuffer(self.folder+"/"file)
							length = min(dataLength-(2+length+8), self.filesize)
							ba = bytearray()
							for i in range(length):
								ba.append(data[2+length+8+i])
							self.writeBuffer.write(ba)
							self.filesize -= length
					else:
						self.buffer = data
				else:
					self.buffer = data
			else:
				self.buffer = data
		else:
			length = min(dataLength, self.filesize)
			ba = bytearray()
			for i in range(length):
				ba.append(data[i])
			self.writeBuffer.write(ba)
			self.filesize -= length
			if (self.filesize == 0):
				self.writeBuffer.close()
				self.writeBuffer = None
				self.write(data[length:])
class Compressor:
	def __init__(self):
		self.dict = {}
		for i in range(256):
			self.dict[(i,)] = [-1, i]
		self.size = 256
		self.maxSize = 256*256
		self.buffer = None
	def compress(self, data):
		bytes = ()
		if (self.buffer is not None):
			bytes = self.buffer
			self.buffer = None
		dataLen = len(data)
		returnValue = bytearray()
		while (True):
			if (len(data) == 0):
				self.buffer = bytes
				break
			bytes += (data.pop(0),)
			if (bytes not in self.dict):
				if (self.size == self.maxSize):
					prev = self.dict[bytes[:-1]][1]
					ba = bytearray()
					ba.append(prev>>8)
					ba.append(prev&255)
					returnValue += ba
					bytes = bytes[-1:]
				else:
					prev = self.dict[bytes[:-1]][1]
					self.dict[bytes] = [prev, self.size]
					self.size += 1
					ba = bytearray()
					ba.append(prev>>8)
					ba.append(prev&255)
					ba.append(bytes[-1:][0])
					returnValue += ba
					bytes = ()
		return returnValue
	def close(self):
		bytes = ()
		if (self.buffer is not None):
			bytes = self.buffer
			self.buffer = None
		if (len(bytes) > 0):
			prev = self.dict[bytes][1]
			ba = bytearray()
			ba.append(prev>>8)
			ba.append(prev&255)
			return ba
class Decompressor:
	def __init__(self):
		self.uncompressDict = {}
		for i in range(256):
			self.uncompressDict[i] = [-1, (i,)]
		self.size = 256
		self.maxSize = 256*256
		self.buffer = None
	def decompress(self, data):
		if (self.buffer is not None):
			data = self.buffer+data
			self.buffer = None
		returnValue = bytearray()
		while (True):
			reqiredLength = 3
			if (self.size == self.maxSize):
				reqiredLength = 2
			if (len(data) >= reqiredLength):
				ba = bytearray()
				ba.append(data.pop(0))
				ba.append(data.pop(0))
				if (self.size == self.maxSize):
					index = (ba[0])<<8
					index += ba[1]
					bytes = self.uncompressDict[index][1]
					for b in bytes:
						returnValue.append(b)
				else:
					ba.append(data.pop(0))
					prev = (ba[0])<<8
					prev += ba[1]
					bytes = self.uncompressDict[prev][1]
					bytes += (ba[2],)
					self.uncompressDict[self.size] = [prev, bytes]
					self.size += 1
					for b in bytes:
						returnValue.append(b)
			else:
				self.buffer = data
				return returnValue
	def close(self):
		self.decompress(bytearray())
class Encoder:
	def __init__(self):
		pass
class Decoder:
	def __init__(self):
		pass
class SBox:
	"""
	SBox is a substitution cipher.
		
	Attributes:
		encodeMap (list): lookuptable used to encode data
		decodeMap (list): lookuptable used to decode data
		
	Parameters:
		pw (list): password
		
	| **Pre:**
	|	len(pw) == 256
	|	isinstance(pw[i], int)
	|	pw[i] >= 0
	|	pw[i] < 256
		
	| **Post:**
	|	len(self.encodeMap) == 256
	|	isinstance(self.encodeMap[i], int)
	|	self.encodeMap[i] >= 0
	|	self.encodeMap[i] < 256
	|	len(self.decodeMap) == 256
	|	isinstance(self.decodeMap[i], int)
	|	self.decodeMap[i] >= 0
	|	self.decodeMap[i] < 256
	"""

	def __init__(self, pw):
		self.encodeMap = [-1]*256
		self.decodeMap = [-1]*256
		index = 0
		for i in range(256):
			emptyCounter = 0
			maxEmpty = 256-i
			targetEmpty = 1+(pw[i] % maxEmpty)
			while (emptyCounter < targetEmpty):
				if (self.encodeMap[index] == -1):
					emptyCounter += 1
				if (emptyCounter < targetEmpty):
					index = (index+1)%256
			self.encodeMap[index] = i
		for i in range(256):
			self.decodeMap[self.encodeMap[i]] = i

	def encode(self, plain):
		"""
		Encodes a single plain number.
		
		Parameters:
			plain (int): plain number
		
		Returns:
			int: encoded number
			
		| **Pre:**
		|	plain >= 0
		|	plain < 256
			
		| **Post:**
		|	return >= 0
		|	return < 256
		"""
		return self.encodeMap[plain]

	def decode(self, encoded):
		"""
		Decodes a single encoded number.
		
		Parameters:
			encoded (int): encoded number
		
		Returns:
			int: decoded number
			
		| **Pre:**
		|	encoded >= 0
		|	encoded < 256
			
		| **Post:**
		|	return >= 0
		|	return < 256
		"""
		return self.decodeMap[encoded]

class PBox:
	"""
	PBox is a transposition cipher.
		
	Attributes:
		encodeMap (list): lookuptable used to encode data
		decodeMap (list): lookuptable used to decode data
		
	Parameters:
		pw (list): password
		
	| **Pre:**
	|	len(pw) == 2048
	|	isinstance(pw[i], int)
	|	pw[i] >= 0
	|	pw[i] < 256
		
	| **Post:**
	|	len(self.encodeMap) == 2048
	|	isinstance(self.encodeMap[i], int)
	|	self.encodeMap[i] >= 0
	|	self.encodeMap[i] < 2048
	|	len(self.decodeMap) == 2048
	|	isinstance(self.decodeMap[i], int)
	|	self.decodeMap[i] >= 0
	|	self.decodeMap[i] < 2048
	"""
	def __init__(self, pw):
		self.encodeMap = [-1]*(256*8)
		self.decodeMap = [-1]*(256*8)
		index = 0
		for i in range(256*8):
			emptyCounter = 0
			maxEmpty = 256*8-i
			targetEmpty = 1+(pw[i] % maxEmpty)
			while (emptyCounter < targetEmpty):
				if (self.encodeMap[index] == -1):
					emptyCounter += 1
				if (emptyCounter < targetEmpty):
					index = (index+1)%(256*8)
			self.encodeMap[index] = i
		for i in range(256*8):
			self.decodeMap[self.encodeMap[i]] = i

	def encode(self, plain, seed):
		"""
		Encodes a block of plain numbers.
		
		Parameters:
			plain (list): block of plain numbers
			seed (list): seed
		
		Returns:
			list: block of encoded numbers
			
		| **Pre:**
		|	len(plain) == 256
		|	isinstance(plain[i], int)
		|	plain[i] >= 0
		|	plain[i] < 256
		|	len(seed) == 256
		|	isinstance(seed[i], int)
		|	seed[i] >= 0
		|	seed[i] < 256
			
		| **Post:**
		|	len(return) == 256
		|	isinstance(return[i], int)
		|	return[i] >= 0
		|	return[i] < 256
		"""
		encoded = [0]*256
		for i in range(256):
			indexVar = i*8+seed
			for b in range(8):
				if ((plain[i]) & (1<<b)):
					index = self.encodeMap[(b+indexVar)%2048]
					index8 = int(index/8)
					encoded[index8] = encoded[index8] + (1<<(index%8))
		return encoded

	def decode(self, encoded, seed):
		"""
		Decodes a block of encoded numbers.
		
		Parameters:
			encoded (list): block of encoded numbers
			seed (list): seed
		
		Returns:
			list: block of decoded numbers
			
		| **Pre:**
		|	len(encoded) == 256
		|	isinstance(encoded[i], int)
		|	encoded[i] >= 0
		|	encoded[i] < 256
		|	len(seed) == 256
		|	isinstance(seed[i], int)
		|	seed[i] >= 0
		|	seed[i] < 256
			
		| **Post:**
		|	len(return) == 256
		|	isinstance(return[i], int)
		|	return[i] >= 0
		|	return[i] < 256
		"""
		decoded = [0]*256
		for i in range(256):
			indexVar = i*8
			for b in range(8):
				if ((encoded[i]) & (1<<b)):
					index = self.decodeMap[indexVar+b] - seed
					if (index < 0):
						index += 2048
					index8 = int(index/8)
					decoded[index8] = decoded[index8] + (1<<(index%8))
		return decoded

class SPBox:
	"""
	SPBox is a substitution-permutation network.
		
	Attributes:
		sBoxes (list): list of SBoxes used for substitution
		seed (list): seed
		pBox (PBox): PBox used for permutation
		
	Parameters:
		pw (list): password
		seed (list): seed
		
	| **Pre:**
	|	len(pw) == 4096
	|	isinstance(pw[i], int)
	|	pw[i] >= 0
	|	pw[i] < 256
	|	len(seed) == 256
	|	isinstance(seed[i], int)
	|	seed[i] >= 1
	|	seed[i] < 256
		
	| **Post:**
	|	len(self.sBoxes) == 8
	|	isinstance(self.sBoxes[i], SBox)
	|	len(self.seed) == 256
	|	isinstance(self.seed[i], int)
	|	self.seed[i] >= 1
	|	self.seed[i] < 256
	"""
	def __init__(self, pw, seed=None):
		self.sBoxes = [None]*8
		if (seed is None):
			seed = [0]*256
			for i in range(256):
				seed[i] = randint(1, 255)
		self.seed = deepcopy(seed)
		for s in range(8):
			spw = [0]*256
			for i in range(256):
				spw[i] = pw[s*256+i]
			self.sBoxes[s] = SBox(spw)
		ppw = [0]*2048
		for i in range(2048):
			ppw[i] = pw[8*256+i]
		self.pBox = PBox(ppw)

	def encodeRound(self, plain, round, pSeed):
		"""
		Encodes a block of plain numbers.
		
		Parameters:
			plain (list): block of plain numbers
			round (int): iteration of encode
			pSeed (int): seed for PBox
		
		Returns:
			list: block of encoded numbers
			
		| **Pre:**
		|	len(plain) == 256
		|	isinstance(plain[i], int)
		|	plain[i] >= 0
		|	plain[i] < 256
		|	round >= 0
		|	round < 8
		|	pSeed >= 0
		|	pSeed < 256
			
		| **Post:**
		|	len(return) == 256
		|	isinstance(return[i], int)
		|	return[i] >= 0
		|	return[i] < 256
		"""
		encoded = [0]*256
		for i in range(256):
			seedAtI = self.seed[i]
			encoded[i] = plain[i] ^ self.sBoxes[round].encodeMap[i] ^ seedAtI
			for j in range(8):
				if ((seedAtI & (1<<j)) != 0):
					encoded[i] = self.sBoxes[j].encodeMap[encoded[i]]##!replacement for SBox.encode() to improve performance
		encoded = self.pBox.encode(encoded, pSeed)
		return encoded

	def decodeRound(self, encoded, round, pSeed):
		"""
		Decodes a block of encoded numbers.
		
		Parameters:
			encoded (list): block of encoded numbers
			round (int): iteration of decode
			pSeed (int): seed for PBox
		
		Returns:
			list: block of decoded numbers
			
		| **Pre:**
		|	len(encoded) == 256
		|	isinstance(encoded[i], int)
		|	encoded[i] >= 0
		|	encoded[i] < 256
		|	round >= 0
		|	round < 8
		|	pSeed >= 0
		|	pSeed < 256
			
		| **Post:**
		|	len(return) == 256
		|	isinstance(return[i], int)
		|	return[i] >= 0
		|	return[i] < 256
		"""
		decoded = self.pBox.decode(encoded, pSeed)
		for i in range(256):
			seedAtI = self.seed[i]
			for invertedJ in range(8):
				j = 8-1-invertedJ
				if ((seedAtI & (1<<j)) != 0):
					decoded[i] = self.sBoxes[j].decodeMap[decoded[i]]#replacement for SBox.decode() to improve performance
			decoded[i] = decoded[i] ^ self.sBoxes[round].encodeMap[i] ^ seedAtI
		return decoded

	def encodeRounds(self, plain):
		"""
		Encodes a block of plain numbers.
		
		Parameters:
			plain (list): block of plain numbers
		
		Returns:
			list: block of encoded numbers
			
		| **Pre:**
		|	len(plain) == 256
		|	isinstance(plain[i], int)
		|	plain[i] >= 0
		|	plain[i] < 256
			
		| **Post:**
		|	len(return) == 256
		|	isinstance(return[i], int)
		|	return[i] >= 0
		|	return[i] < 256
			
		| **Modifies:**
		|	self.seed[i]
		"""
		pSeed = 0
		for i in range(256):
			pSeed = (pSeed+self.seed[i])%256
		encoded = self.encodeRound(plain, 0, pSeed)
		for i in range(7):
			encoded = self.encodeRound(encoded, i+1, pSeed)
		for i in range(256):
			self.seed[i] = plain[i] ^ self.seed[i]
			if (self.seed[i] == 0):
				self.seed[i] = 1
		return encoded

	def decodeRounds(self, encoded):
		"""
		Decodes a block of encoded numbers.
		
		Parameters:
			encoded (list): block of encoded numbers
		
		Returns:
			list: block of decoded numbers
			
		| **Pre:**
		|	len(encoded) == 256
		|	isinstance(encoded[i], int)
		|	encoded[i] >= 0
		|	encoded[i] < 256
			
		| **Post:**
		|	len(return) == 256
		|	isinstance(return[i], int)
		|	return[i] >= 0
		|	return[i] < 256
			
		| **Modifies:**
		|	self.seed[i]
		"""
		pSeed = 0
		for i in range(256):
			pSeed = (pSeed+self.seed[i])%256
		decoded = self.decodeRound(encoded, 7, pSeed)
		for invertedI in range(7):
			i = 6-invertedI
			decoded = self.decodeRound(decoded, i, pSeed)
		for i in range(256):
			self.seed[i] = decoded[i] ^ self.seed[i]
			if (self.seed[i] == 0):
				self.seed[i] = 1
		return decoded

	def encode(self, plain):
		"""
		Encodes a block of plain numbers.
		
		Parameters:
			plain (list): block of plain numbers
		
		Returns:
			{"length":length, "message":encodedNumbers}: container with encoded numbers
			
		| **Pre:**
		|	len(plain) > 0
		|	isinstance(plain[i], int)
		|	plain[i] >= 0
		|	plain[i] < 256
			
		| **Post:**
		|	isinstance(return["message"], list)
		|	len(return["message"]) >= return["length"]
		|	len(return["message"]) % 256 == 0
		|	isinstance(return["message"][i], int)
		|	return["message"][i] >= 0
		|	return["message"][i] < 256
			
		| **Modifies:**
		|	self.seed[i]
		"""
		length = len(plain)
		while (len(plain)%256 != 0):
			plain.append(randint(0, 255))
		encodedBytes = 0
		encoded = []
		while (encodedBytes < len(plain)):
			plainPart = [0]*256
			for i in range(256):
				plainPart[i] = plain[encodedBytes]
				encodedBytes += 1
			encodedPart = self.encodeRounds(plainPart)
			for i in range(256):
				encoded.append(encodedPart[i])
		return {"length":length, "message":encoded}

	def decode(self, encodedJSON):
		"""
		Decodes a container with encoded numbers.
		
		Parameters:
			encodedJSON ({"length":length, "message":encodedNumbers}): container with encoded numbers
		
		Returns:
			list: block of decoded numbers
			
		| **Pre:**
		|	isinstance(encodedJSON["message"], list)
		|	len(encodedJSON["message"]) >= encodedJSON["length"]
		|	len(encodedJSON["message"]) % 256 == 0
		|	isinstance(encodedJSON["message"][i], int)
		|	encodedJSON["message"][i] >= 0
		|	encodedJSON["message"][i] < 256
			
		| **Post:**
		|	len(return) == encodedJSON["length"]
		|	isinstance(return[i], int)
		|	return[i] >= 0
		|	return[i] < 256
			
		| **Modifies:**
		|	self.seed[i]
		"""
		length = encodedJSON["length"]
		encoded = encodedJSON["message"]
		decodedBytes = 0
		decoded = []
		while (decodedBytes < len(encoded)):
			encodedPart = [0]*256
			for i in range(256):
				encodedPart[i] = encoded[decodedBytes]
				decodedBytes += 1
			decodedPart = self.decodeRounds(encodedPart)
			for i in range(256):
				if (len(decoded) < length):
					decoded.append(decodedPart[i])
				else:
					break
		return decoded

	def getSeed(self):
		"""
		Gets the seed.
		
		Returns:
			list: block of seed numbers
			
		| **Post:**
		|	len(return) == 256
		|	isinstance(return[i], int)
		|	return[i] >= 1
		|	return[i] < 256
		"""
		seed = [0]*256
		for i in range(256):
			seed[i] = self.seed[i]
		return seed

	def setSeed(self, seed):
		"""
		Sets the seed.
		
		Parameters:
			seed (list): block of seed numbers
			
		| **Pre:**
		|	len(seed) == 256
		|	isinstance(seed[i], int)
		|	seed[i] >= 1
		|	seed[i] < 256
			
		| **Modifies:**
		|	self.seed[i]
		"""
		for i in range(256):
			self.seed[i] = seed[i]

class Edoc:
	"""
	"""
	def __init__(self, pw):
		"""
		"""
		asInt = []
		for i in range(len(pw)):
			asInt.append(ord(pw[i]))
		pwIndex = 0
		while (len(asInt) < 4096):
			asInt.append(ord(pw[pwIndex%len(pw)]))
			pwIndex += 1
		self.spBox = SPBox(asInt)
	def encodeString(self, plain):
		"""
		"""
		plainMessage = []
		for i in range(len(plain)):
			if (ord(plain[i]) > 255):
				plainMessage[i] = ord("?"[0])
				logger.info(ord(plain[i])+" is no valid char")
			else:
				plainMessage[i] = ord(plain[i])
		return self.spBox.encode(plainMessage)
	def decodeString(self, encoded):
		"""
		"""
		decoded = self.spBox.decode(encoded)
		decodedStr = ""
		for i in range(len(decoded)):
			decodedStr += chr(decoded[i])
		return decodedStr
	def encode(self, plain):
		"""
		"""
		seed = [0]*256
		for i in range(256):
			seed[i] = randint(1, 255)
		self.spBox.setSeed(seed)
		return {"seed":seed,"message":self.encodeString(plain)}
	def decode(self, container):
		"""
		"""
		seed = container["seed"]
		encoded = container["message"]
		self.spBox.setSeed(seed)
		return self.decodeString(encoded)
	def encodeFile(self, inFile, outFile):
		"""
		"""
		compressor = Compressor()
		compressor.compressFile(inFile, inFile+".compressed")
		inFile = inFile+".compressed"
		fOut = open(outFile, "wb")
		fOut.write(chr(0).encode("utf-8"))
		size = getSize(inFile)
		self.encodeFileStream(inFile, fOut, size)
		now = time.time()
		logger.info(str(round(size/(now-start)))+" B/s")
		fOut.close()
		os.remove(inFile)
	def encodeFileStream(self, inFile, fOut, targetProgress):#TODO use buffers
		"""
		"""
		global progress
		seed = [1]*256
		for i in range(256):
			seed[i] = randint(1, 255)
		self.spBox.setSeed(seed)
		fIn = open(inFile, "rb")
		ba = bytearray()
		fileSize = os.stat(inFile).st_size
		for i in range(8):
			ba.append((fileSize >> (8*(8-1-i))) & 0xff)
		fOut.write(ba)
		ba = bytearray()
		for i in range(256):
			ba.append(self.spBox.seed[i])
		fOut.write(ba)
		readSize = 0
		while readSize < fileSize:
			now = time.time()
			end = 0
			if (progress != 0):
				end = targetProgress*(float(now-start)/progress)
				end -= (now-start)
			h = math.floor(end/3600)
			m = math.floor((end-h*3600)/60)
			s = math.floor(end-h*3600-m*60)
			h = str(h)
			m = str(m)
			s = str(s)
			if (len(h) == 1):
				h = "0"+h
			if (len(m) == 1):
				m = "0"+m
			if (len(s) == 1):
				s = "0"+s
			end = round(end*10)/10
			print(str(round(progress*1000/targetProgress)/10)+"% "+h+":"+m+":"+s, end="\r")
			n = min(fileSize-readSize, 256)
			progress += n
			data = fIn.read(n)
			asInt = []
			for c in data:
				asInt.append(c)
			output = bytearray()
			encoded = self.spBox.encode(asInt)
			for i in range(256):
				output.append(encoded["message"][i])
			fOut.write(output)
			readSize += n
		fIn.close()
	def decodeFile(self, inFile, outFile):
		"""
		"""
		outFile = outFile+".compressed"
		fIn = open(inFile, "rb")
		ord(fIn.read(1).decode("utf-8")[0])#0
		size = getSize(inFile)
		self.decodeFileStream(fIn, outFile, size)
		now = time.time()
		logger.info(str(round(size/(now-start)))+" B/s")
		fIn.close()
		os.remove(inFile)
		compressor = Compressor()
		compressor.decompressFile(outFile, outFile[:-11])
	def decodeFileStream(self, fIn, outFile, targetProgress):#TODO use buffers
		"""
		"""
		global progress
		fOut = open(outFile, "wb")
		fileSize = 0
		for i in range(8):
			fileSize += (fIn.read(1)[0]) << (8*(8-1-i))
		seed = []
		b = fIn.read(256)
		for c in b:
			seed.append(c)
		self.spBox.setSeed(seed)
		readSize = 0
		while readSize < fileSize:
			now = time.time()
			end = 0
			if (progress != 0):
				end = targetProgress*(float(now-start)/progress)
				end -= (now-start)
			h = math.floor(end/3600)
			m = math.floor((end-h*3600)/60)
			s = math.floor(end-h*3600-m*60)
			h = str(h)
			m = str(m)
			s = str(s)
			if (len(h) == 1):
				h = "0"+h
			if (len(m) == 1):
				m = "0"+m
			if (len(s) == 1):
				s = "0"+s
			end = round(end*10)/10
			print(str(round(progress*1000/targetProgress)/10)+"% "+h+":"+m+":"+s, end="\r")
			length = min(fileSize-readSize, 256)
			n = 256
			progress += n
			data = fIn.read(n)
			message = []
			for c in data:
				message.append(c)
			encoded = {"length":length,"message":message}
			decoded = self.spBox.decode(encoded)
			output = bytearray()
			for c in decoded:
				output.append(c)
			fOut.write(output)
			readSize += n
		fOut.close()
	def encodeFolder(self, folder, outFile):
		"""
		"""
		fOut = open(outFile, "wb")
		fOut.write(chr(1).encode("utf-8"))
		size = getSize(folder)
		self.encodeFolderStream(folder, fOut, folder+"/", size)
		now = time.time()
		logger.info(str(round(size/(now-start)))+" B/s")
		fOut.close()
		shutil.rmtree(folder)
	def encodeFolderStream(self, folder, fOut, root, targetProgress):
		"""
		"""
		files = os.listdir(folder)
		for file in files:
			file = folder + "/" + file
			if (os.path.isfile(file)):
				compressor = Compressor()
				compressor.compressFile(file, file+".compressed")
				file = file+".compressed"
				fileName = file[len(root):]
				ba = bytearray()
				ba.append(len(fileName))
				for c in fileName:
					ba.append(ord(c))
				fOut.write(ba)
				self.encodeFileStream(file, fOut, targetProgress)
			elif (os.path.isdir(file)):
				self.encodeFolderStream(file, fOut, root, targetProgress)
	def decodeFolder(self, inFile):
		"""
		"""
		fIn = open(inFile, "rb")
		folder = inFile[0:inFile.rfind(".")] + "/"
		fIn.read(1)[0]#1
		size = getSize(inFile)
		self.decodeFolderStream(fIn, folder, size)
		now = time.time()
		logger.info(str(round(size/(now-start)))+" B/s")
		fIn.close()
		os.remove(inFile)
	def decodeFolderStream(self, fIn, root, targetProgress):
		"""
		"""
		while True:
			lengthStr = fIn.read(1)
			if (len(lengthStr) == 0):
				break
			length = lengthStr[0]
			data = fIn.read(length)
			outFile = root
			for c in data:
				outFile += chr(c)
			folder = outFile[0:outFile.rfind("/")]
			if (not os.path.exists(folder)):
				os.makedirs(folder)
			self.decodeFileStream(fIn, outFile, targetProgress)
			compressor = Compressor()
			compressor.decompressFile(outFile, outFile[:-11])
def getSize(folder):
	"""
	"""
	if (os.path.isfile(folder)):
		return os.stat(folder).st_size
	size = 0
	files = os.listdir(folder)
	for file in files:
		file = folder + "/" + file
		if (os.path.isfile(file)):
			size += getSize(file)
		elif (os.path.isdir(file)):
			size += getSize(file)
	return size
class SBoxUnitTest(unittest.TestCase):
	def setUp(self):
		self.pw = []
		for i in range(256):
			self.pw.append(randint(0, 255))
		self.sBox = SBox(self.pw)
	def tearDown(self):
		self.pw = None
		self.sBox = None
	def test_simple(self):
		decodedMatches = 0
		encodedMatches = 0
		for i in range(256):
			plain = i
			encoded = self.sBox.encode(plain)
			decoded = self.sBox.decode(encoded)
			if (plain == encoded):
				encodedMatches += 1
			if (plain == decoded):
				decodedMatches += 1
		self.assertTrue(encodedMatches < 256/10)
		self.assertTrue(decodedMatches == 256)
class PBoxUnitTest(unittest.TestCase):
	def setUp(self):
		self.pw = []
		for i in range(2048):
			self.pw.append(randint(0, 255))
		self.pBox = PBox(self.pw)
	def tearDown(self):
		self.pw = None
		self.pBox = None
	def test_simple(self):
		plain = []
		for i in range(256):
			plain.append(randint(0, 255))
		for seed in range(256):
			encoded = self.pBox.encode(plain, seed)
			decoded = self.pBox.decode(encoded, seed)
			decodedMatches = 0
			encodedMatches = 0
			for i in range(256):
				if (plain[i] == encoded[i]):
					encodedMatches += 1
				if (plain[i] == decoded[i]):
					decodedMatches += 1
			self.assertTrue(encodedMatches < 256/10)
			self.assertTrue(decodedMatches == 256)
class SPBoxUnitTest(unittest.TestCase):
	def setUp(self):
		self.pw = []
		for i in range(4096):
			self.pw.append(randint(0, 255))
		self.spBox = SPBox(self.pw)
	def tearDown(self):
		self.pw = None
		self.spBox = None
	def test_simple(self):
		plain = []
		for i in range(randint(1, 256)):
			plain.append(randint(0, 255))
		length = len(plain)
		seed = self.spBox.getSeed()
		for i in range(256):
			self.assertTrue(self.spBox.seed[i] != 0)
		encoded = self.spBox.encode(plain)
		for i in range(256):
			self.assertTrue(self.spBox.seed[i] != 0)
		seed2 = self.spBox.getSeed()
		self.spBox.setSeed(seed)
		decoded = self.spBox.decode(encoded)
		decodedMatches = 0
		seedMatches = 0
		for i in range(256):
			if (seed[i] == seed2[i]):
				seedMatches += 1
		for i in range(length):
			if (plain[i] == decoded[i]):
				decodedMatches += 1
		self.assertTrue(decodedMatches == length)#TODO encodeMatches
		self.assertTrue(seedMatches < 256/10)
		#TODO encode 2nd batch#plain is edited
class EdocUnitTest(unittest.TestCase):
	def setUp(self):
		self.pw = ""
		for i in range(randint(1, 4096)):
			self.pw += chr(randint(0, 255))
		self.edoc = Edoc(self.pw)
	def tearDown(self):
		self.pw = None
		self.edoc = None
	def test_simple(self):
		plain = ""
		for i in range(randint(1, 256*4*16)):
			plain += chr(randint(0, 255))
		encoded1 = self.edoc.encode(plain)
		encoded2 = self.edoc.encode(plain)
		decoded1 = self.edoc.decode(encoded1)
		decoded2 = self.edoc.decode(encoded2)
		decodedMatches = 0
		for i in range(len(plain)):
			if (plain[i] == decoded1[i]):
				decodedMatches += 1
			if (plain[i] == decoded2[i]):
				decodedMatches += 1
		self.assertTrue(decodedMatches == 2*len(plain))#TODO encodeMatches
		self.assertTrue(len(decoded1) == len(plain))
		self.assertTrue(len(decoded2) == len(plain))
if __name__ == "__main__":
	PROJECTNAME = "edoc"
	LOGNAME = PROJECTNAME+".log"
	fileLogging = False
	useCurses = True
	profiling = False
	
	if (useCurses):
		import curses
	if (profiling):
		import cProfile, pstats, io
		
	logger = logging.getLogger(PROJECTNAME)
	logger.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	if (fileLogging):
		fh = logging.FileHandler(LOGNAME)
		fh.setLevel(logging.DEBUG)
		fh.setFormatter(formatter)
		logger.addHandler(fh)

	parser = argparse.ArgumentParser(description="Encodes or decodes a file or folder.")
	parser.add_argument("-e", "--encode", action="store_true", help="Specify mode: encode")
	parser.add_argument("-d", "--decode", action="store_true", help="Specify mode: decode")
	parser.add_argument("-p", "--password", action="store", metavar="password", help="Specify password.")
	parser.add_argument("-f", "--file", help="Specify file/folder.")
	parser.add_argument("-t", "--test", action="store_true", help="Runs unittests.")
	args = vars(parser.parse_args())
	file = args["file"]
	password = args["password"]
	encodeMode = args["encode"]
	testMode = args["test"]
	root = None
	progress = 0
	start = 0
	pr = None
	if (testMode):
		unittest.main(argv=[sys.argv[0]])
		input("Press Enter to leave")
		exit()
	else:
		if (password is None):
			password = input("Enter password: ")
			if (useCurses):
				window = curses.initscr()
				window.clear()
				window.refresh()
		if (password is not None):
			if (profiling):
				pr = cProfile.Profile()
				pr.enable()
			edoc = Edoc(password)
			start = time.time()
			if (os.path.isfile(file)):
				if (encodeMode):
					edoc.encodeFile(file, file+".edoc")
				else:
					fIn = open(file, "rb")
					startingByte = fIn.read(1)
					fIn.close()
					if (ord(startingByte) == 0):
						edoc.decodeFile(file, file[0:-5])
					else:
						edoc.decodeFolder(file)
			elif (os.path.isdir(file)):
				if (encodeMode):
					edoc.encodeFolder(file, file+".edoc")
			if (profiling):
				pr.disable()
				s = io.StringIO()
				sortby = "cumulative"
				ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
				ps.print_stats()
				logger.info(s.getvalue())