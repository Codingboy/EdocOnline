/**
\brief Gets a random number.
\param[in] min the minimum value to be returned
\param[in] max the maximum value to be returned
\pre max >= min
\return number between min (including) and max (including)
*/
function getRandomInt(min, max)
{
	return Math.floor(Math.random() * (max - min + 1)) + min;
}
/**
\brief SBox is a substitution cipher.
*/
class SBox
{
	/**
	\param[in] pw password
	\pre Array.isArray(pw)
	\pre pw.length == 256
	*/
	constructor(pw)
	{
		this.encodeMap = new Array(256);
		this.decodeMap = new Array(256);
		for (let i=0; i<256; i++)
		{
			this.encodeMap[i] = -1;
		}
		let index = 0;
		for (let i=0; i<256; i++)
		{
			let emptyCounter = 0;
			let maxEmpty = 256-i;
			let targetEmpty = 1+(pw[i] % maxEmpty);
			while (emptyCounter < targetEmpty)
			{
				if (this.encodeMap[index] == -1)
				{
					emptyCounter++;
				}
				if (emptyCounter < targetEmpty)
				{
					index = (index+1)%256;
				}
			}
			this.encodeMap[index] = i;
		}
		for (let i=0; i<256; i++)
		{
			this.decodeMap[this.encodeMap[i]] = i;
		}
	}
	/**
	\brief Encodes a single plain number.
	\param[in] plain plain number
	\pre typeof(plain) == "number"
	\return encoded number
	*/
	encode(plain)
	{
		return this.encodeMap[plain];
	}
	/**
	\brief Decodes a single encoded number.
	\param[in] encoded encoded number
	\pre typeof(encoded) == "number"
	\return decoded number
	*/
	decode(encoded)
	{
		return this.decodeMap[encoded];
	}
}
/**
\brief PBox is a transposition cipher.
*/
class PBox
{
	/**
	\param[in] pw password
	\pre Array.isArray(pw)
	\pre pw.length == 2048
	*/
	constructor(pw)
	{
		this.encodeMap = new Array(256*8);
		this.decodeMap = new Array(256*8);
		for (let i=0; i<256*8; i++)
		{
			this.encodeMap[i] = -1;
		}
		let index = 0;
		for (let i=0; i<256*8; i++)
		{
			let emptyCounter = 0;
			let maxEmpty = 256*8-i;
			let targetEmpty = 1+(pw[i] % maxEmpty);
			while (emptyCounter < targetEmpty)
			{
				if (this.encodeMap[index] == -1)
				{
					emptyCounter++;
				}
				if (emptyCounter < targetEmpty)
				{
					index = (index+1)%(256*8);
				}
			}
			this.encodeMap[index] = i;
		}
		for (let i=0; i<256*8; i++)
		{
			this.decodeMap[this.encodeMap[i]] = i;
		}
	}
	/**
	\brief Encodes a block of plain numbers.
	\param[in] plain block of plain numbers
	\param[in] seed seed
	\pre Array.isArray(plain)
	\pre plain.length == 256
	\return block of encoded numbers
	*/
	encode(plain, seed)
	{
		let encoded = new Array(256);
		for (let i=0; i<256; i++)
		{
			encoded[i] = 0;
		}
		for (let i=0; i<256; i++)
		{
			for (let b=0; b<8; b++)
			{
				let index = this.encodeMap[(i*8+b+seed)%2048];
				if ((plain[i]) & (1<<b))
				{
					encoded[parseInt(index/8)] = encoded[parseInt(index/8)] + (1<<(index%8));
				}
			}
		}
		return encoded;
	}
	/**
	\brief Decodes a block of encoded numbers.
	\param[in] encoded block of encoded numbers
	\param[in] seed seed
	\pre Array.isArray(encoded)
	\pre encoded.length == 256
	\return block of decoded numbers
	*/
	decode(encoded, seed)
	{
		let decoded = new Array(256);
		for (let i=0; i<256; i++)
		{
			decoded[i] = 0;
		}
		for (let i=0; i<256; i++)
		{
			for (let b=0; b<8; b++)
			{
				let index = this.decodeMap[i*8+b] - seed;
				if (index < 0)
				{
					index += 2048;
				}
				if ((encoded[i]) & (1<<b))
				{
					decoded[parseInt(index/8)] = decoded[parseInt(index/8)] + (1<<(index%8));
				}
			}
		}
		return decoded;
	}
}
/**
\brief SPBox is a substitution–permutation network.
*/
class SPBox
{
	/**
	\param[in] pw password
	\param[in] seed seed
	\pre Array.isArray(pw)
	\pre pw.length == 4096
	\pre Array.isArray(seed)
	\pre seed.length == 256
	\pre seed[i] != 0
	*/
	constructor(pw, seed)
	{
		this.sBoxes = new Array(8);
		if (typeof seed == "undefined")
		{
			seed = new Array(256);
			for (let i=0; i<256; i++)
			{
				seed[i] = getRandomInt(1, 255);
			}
		}
for (let i=0; i<256; i++)
{
	seed[i] = 0;
}
		this.seed = seed.slice();
		for (let s=0; s<8; s++)
		{
			let spw = new Array(256);
			for (let i=0; i<256; i++)
			{
				spw[i] = pw[s*256+i];
			}
			this.sBoxes[s] = new SBox(spw);
		}
		let ppw = new Array(2048);
		for (let i=0; i<2048; i++)
		{
			ppw[i] = pw[8*256+i];
		}
		this.pBox = new PBox(ppw);
	}
	/**
	\brief Encodes a block of plain numbers.
	\param[in] plain block of plain numbers
	\param[in] pSeed seed for PBox
	\pre Array.isArray(plain)
	\pre plain.length == 256
	\return block of encoded numbers
	*/
	encodeRound(plain, round, pSeed)
	{
		let encoded = new Array(256);
		for (let i=0; i<256; i++)
		{
			encoded[i] = plain[i];
			encoded[i] = encoded[i] ^ this.sBoxes[round].encodeMap[i];
//			encoded[i] = encoded[i] ^ this.seed[i];
			for (let j=0; j<8; j++)
			{
//				if ((this.seed[i] & (1<<j)) != 0)
//				{
					let sBox = this.sBoxes[j];
					encoded[i] = sBox.encode(encoded[i]);
//				}
			}
		}
		encoded = this.pBox.encode(encoded, pSeed);
		return encoded;
	}
	/**
	\brief Decodes a block of encoded numbers.
	\param[in] encoded block of encoded numbers
	\param[in] pSeed seed for PBox
	\pre Array.isArray(encoded)
	\pre encoded.length == 256
	\return block of decoded numbers
	*/
	decodeRound(encoded, round, pSeed)
	{
		let decoded = this.pBox.decode(encoded, pSeed);
		for (let i=0; i<256; i++)
		{
			for (let j=8-1; j>=0; j--)
			{
//				if ((this.seed[i] & (1<<j)) != 0)
//				{
					let sBox = this.sBoxes[j];
					decoded[i] = sBox.decode(decoded[i]);
//				}
			}
			decoded[i] = decoded[i] ^ this.sBoxes[round].encodeMap[i];
//			decoded[i] = decoded[i] ^ this.seed[i];
		}
		return decoded;
	}
	/**
	\brief Encodes a block of plain numbers.
	\param[in] plain block of plain numbers
	\pre Array.isArray(plain)
	\pre plain.length == 256
	\post this.seed changed
	\return block of encoded numbers
	*/
	encodeRounds(plain)
	{
		let pSeed = 0;
		for (let i=0; i<256; i++)
		{
			pSeed = (pSeed+this.seed[i])%256;
		}
pSeed = 0;
		let encoded = this.encodeRound(plain, 0, pSeed);
		for (let i=1; i<8; i++)
		{
			encoded = this.encodeRound(encoded, i, pSeed);
		}
		for (let i=0; i<256; i++)
		{
//			this.seed[i] = plain[i] ^ this.seed[i];
			if (this.seed[i] == 0)
			{
//				this.seed[i] = 1;
			}
		}
		return encoded;
	}
	/**
	\brief Decodes a block of encoded numbers.
	\param[in] encoded block of encoded numbers
	\pre Array.isArray(encoded)
	\pre encoded.length == 256
	\post this.seed changed
	\return block of decoded numbers
	*/
	decodeRounds(encoded)
	{
		let pSeed = 0;
		for (let i=0; i<256; i++)
		{
			pSeed = (pSeed+this.seed[i])%256;
		}
		let decoded = this.decodeRound(encoded, 7, pSeed);
		for (let i=6; i>=0; i--)
		{
			decoded = this.decodeRound(decoded, i, pSeed);
		}
		for (let i=0; i<256; i++)
		{
//			this.seed[i] = decoded[i] ^ this.seed[i];
			if (this.seed[i] == 0)
			{
//				this.seed[i] = 1;
			}
		}
		return decoded;
	}
	/**
	\brief Encodes a block of plain numbers.
	\param[in] plain block of plain numbers
	\pre Array.isArray(plain)
	\pre plain.length > 0
	\post this.seed changed
	\return container: {"length":length, "message":encodedNumbers}
	*/
	encode(plain)
	{
		let length = plain.length;
		while (plain.length%256 != 0)
		{
			plain.push(getRandomInt(0, 255));
		}
		let encodedBytes = 0;
		let encoded = [];
		while (encodedBytes < plain.length)
		{
			let plainPart = new Array(256);
			for (let i=0; i<256; i++)
			{
				plainPart[i] = plain[encodedBytes];
				encodedBytes++;
			}
			let encodedPart = this.encodeRounds(plainPart);
			for (let i=0; i<256; i++)
			{
				encoded.push(encodedPart[i]);
			}
		}
		return {"length":length, "message":encoded};
	}
	/**
	\brief Decodes a container.
	\param[in] encodedJSON encoded container {"length":length, "message":encodedNumbers}
	\pre Array.isArray(encodedJSON["message"])
	\pre encodedJSON["message"].length >= encodedJSON["length"]
	\pre encodedJSON["message"].length % 256 == 0
	\post this.seed changed
	\return block of decoded numbers
	*/
	decode(encodedJSON)
	{
		let length = encodedJSON["length"];
		let encoded = encodedJSON["message"];
		let decodedBytes = 0;
		let decoded = [];
		while (decodedBytes < encoded.length)
		{
			let encodedPart = [];
			for (let i=0; i<256; i++)
			{
				encodedPart.push(encoded[decodedBytes]);
				decodedBytes++;
			}
			let decodedPart = this.decodeRounds(encodedPart);
			for (let i=0; i<256; i++)
			{
				if (decoded.length < length)
				{
					decoded.push(decodedPart[i]);
				}
				else
				{
					break;
				}
			}
		}
		return decoded;
	}
	/**
	\brief Gets the seed.
	\return block of seed numbers
	*/
	getSeed()
	{
		let seed = [];
		for (let i=0; i<256; i++)
		{
			seed[i] = this.seed[i];
		}
		return seed;
	}
	/**
	\brief Sets the seed.
	\param[in] seed block of seed numbers
	*/
	setSeed(seed)
	{
		for (let i=0; i<256; i++)
		{
			this.seed[i] = seed[i];
		}
for (let i=0; i<256; i++)
{
	seed[i] = 0;
}
	}
}
/**
\brief Userfriendly interface for everyday uses.
*/
class Edoc
{
	/**
	\param[in] pw password
	\pre typeof(pw) == "string"
	\pre pw.length is recommended to be 4096
	*/
	constructor(pw)
	{
		let asInt = [];
		for (let i=0; i<pw.length; i++)
		{
			asInt.push(pw.charCodeAt(i));
		}
		let pwIndex = 0;
		while (asInt.length < 4096)
		{
			asInt.push(pw.charCodeAt(pwIndex%pw.length));
			pwIndex++;
		}
		this.spBox = new SPBox(asInt);
	}
	/**
	\brief Encodes a plain string.
	\param[in] plain plain string
	\pre typeof(plain) == "string"
	\pre plain.length > 0
	\post this.seed changed
	\return block of encoded numbers
	*/
	encodeString(plain)
	{
		let plainMessage = new Array(plain.length);
		for (let i=0; i<plain.length; i++)
		{
			plainMessage[i] = plain.charCodeAt(i);
		}
		return this.spBox.encode(plainMessage);
	}
	/**
	\brief Decodes a block of encoded numbers.
	\param[in] encoded block of encoded numbers
	\pre Array.isArray(encoded)
	\pre encoded.length >= 256
	\pre encoded.length % 256 == 0
	\post this.seed changed
	\return decoded string
	*/
	decodeString(encoded)
	{
		let decoded = this.spBox.decode(encoded);
		let decodedStr = "";
		for (let i=0; i<decoded.length; i++)
		{
			decodedStr += String.fromCharCode(decoded[i]);
		}
		return decodedStr;
	}
	/**
	\brief Encodes a plain string.
	\param[in] plain plain string
	\pre typeof(plain) == "string"
	\pre plain.length > 0
	\return container: {"seed":seed,"message":encodedMessage}
	*/
	encode(plain)
	{
		let seed = new Array(256);
		for (let i=0; i<256; i++)
		{
			seed[i] = getRandomInt(1, 255);
		}
		this.spBox.setSeed(seed);
		return {"seed":seed,"message":this.encodeString(plain)};
	}
	/**
	\brief Decodes an encoded container.
	\param[in] encoded encoded container {"seed":seed,"message":encodedMessage}
	\return decoded string
	*/
	decode(container)
	{
		let seed = container["seed"];
		let encoded = container["message"];
		this.spBox.setSeed(seed);
		return this.decodeString(encoded);
	}
}
/**
\brief Tests the SBox.
*/
function testSBox()
{
	let pw = new Array(256);
	for (let i=0; i<pw.length; i++)
	{
		pw[i] = getRandomInt(0, 255);
	}
	let plain = new Array(256);
	for (let i=0; i<plain.length; i++)
	{
		plain[i] = getRandomInt(0, 255);
	}
	let sBox = new SBox(pw);
	let encoded = new Array(plain.length);
	for (let i=0; i<plain.length; i++)
	{
		encoded[i] = sBox.encode(plain[i]);
	}
	let decoded = new Array(encoded.length);
	for (let i=encoded.length-1; i>=0; i--)
	{
		decoded[i] = sBox.decode(encoded[i]);
	}
	let matches = 0;
	for (let i=0; i<plain.length; i++)
	{
		if (plain[i] == decoded[i])
		{
			matches++;
		}
	}
	console.log("s "+(matches==plain.length));
}
/**
\brief Tests the PBox.
*/
function testPBox()
{
	let pw = new Array(2048);
	for (let i=0; i<pw.length; i++)
	{
		pw[i] = getRandomInt(0, 255);
	}
	let plain = new Array(256);
	for (let i=0; i<plain.length; i++)
	{
		plain[i] = getRandomInt(0, 255);
	}
	let pBox = new PBox(pw);
	let seed = getRandomInt(0, 255);
	let encoded = pBox.encode(plain, seed);
	let decoded = pBox.decode(encoded, seed);
	let matches = 0;
	for (let i=0; i<plain.length; i++)
	{
		if (plain[i] == decoded[i])
		{
			matches++;
		}
	}
	console.log("p "+(matches==plain.length));
}
/**
\brief Tests the SPBox.
*/
function testSPBox()
{
	let pw = new Array(4096);
	for (let i=0; i<pw.length; i++)
	{
		pw[i] = getRandomInt(0, 255);
	}
	let seed = new Array(256);
	for (let i=0; i<seed.length; i++)
	{
		seed[i] = getRandomInt(1, 255);
	}
	let plain = new Array(512);
	for (let i=0; i<plain.length; i++)
	{
		plain[i] = getRandomInt(0, 255);
	}
	let spBox = new SPBox(pw, seed);
	let encoded = spBox.encode(plain);
	spBox.setSeed(seed);
	let decoded = spBox.decode(encoded);
	let matches = 0;
	for (let i=0; i<plain.length; i++)
	{
		if (plain[i] == decoded[i])
		{
			matches++;
		}
	}
	console.log("sp "+(matches == plain.length));
}
/**
\brief Tests the Edoc.
*/
function testEdoc()
{
	let pw = "BlaBlub42";
	let plain = "Hello World! This is me!";
	let edoc = new Edoc(pw);
	let encoded = edoc.encode(plain);
	let decoded = edoc.decode(encoded);
	console.log("edoc "+(plain == decoded));
}