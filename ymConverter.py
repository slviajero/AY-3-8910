# YM converter to SNG file format for the AY-3-8910 programmable sound generator and compatible chips

# SNG file format:
# 5 bytes: 'S', 'N', 'G', 1, 0
# Followed by sequence of 2 bytes: register, value

# when register < 16, it's AY-3-8910 register
# when register = 16, the following value hold how many frames to skip
# when register = 255, means end of file

# Used in the video https://youtu.be/srmNbi9yQNU
# Sérgio Vieira 2022

import sys
import struct

def readAllFrames(inputFile, frameCount):
    totalBytes = 16 * frameCount

    tempArray = inputFile.read(totalBytes)
    finalArray = [0] * totalBytes

    for currentRegister in range(16):
        offset = frameCount * currentRegister
        for i in range(frameCount):
            finalArray[16 * i + currentRegister] = tempArray[i + offset]
    
    return finalArray


def processYMFile(inputFilename, outputFilename):
    try:

        frameCount = 0
        frames = []

        with open(inputFilename, "rb") as inputFile:
            # Read Header
            header = inputFile.read(4)

            if not header in ["YM3!".encode("ascii"), "YM4!".encode("ascii"), "YM5!".encode("ascii"), "YM6!".encode("ascii")]:
                print("ERROR: Invalid header in input file")
                print("Make sure it's an uncompressed YM file, if you think this is a valid YM file, try to uncompress it and use the uncompressed file")
                sys.exit(1)
            
            print("Header:", header.decode("ascii"))

            checkString = inputFile.read(8)
            
            if checkString != "LeOnArD!".encode("ascii"):
                print("ERROR: Check string doesn't check out in input file")
                sys.exit(1)

            frameCount = struct.unpack(">i", inputFile.read(4))[0]
            print("Frame count:", frameCount)

            temp = struct.unpack(">i", inputFile.read(4))[0]
            print("Song attributes:", temp)

            if (temp & 1) != 1:
                print("Error: Only interlaced YM files are supported.")

            temp = struct.unpack(">h", inputFile.read(2))[0]
            print("Digidrums samples:", temp)

            temp = struct.unpack(">i", inputFile.read(4))[0]
            print("YM frequency:", temp, "Hz")

            frameRate = struct.unpack(">h", inputFile.read(2))[0]
            print("Frame rate:", frameRate, "Hz")

            loopFrame = struct.unpack(">i", inputFile.read(4))[0]
            print("Loop frame number:", loopFrame)

            # Read unused bytes
            inputFile.read(2)

            title = ''.join(iter(lambda: inputFile.read(1).decode('ascii'), '\x00'))
            print("Title:", title);
            artist = ''.join(iter(lambda: inputFile.read(1).decode('ascii'), '\x00'))
            print("Artist:", artist);
            comments = ''.join(iter(lambda: inputFile.read(1).decode('ascii'), '\x00'))
            print("Comments:", comments);

            frames = readAllFrames(inputFile, frameCount)

    except FileNotFoundError as fnfe:
        print("Can't open input file:", fnfe)
    except BaseException as be:
        print("Error reading input file:", be)
        sys.exit(1)

    try:
        with open(outputFilename, "wb") as outputFile:
            # Write header
            outputFile.write("SNG".encode("ascii"))
            outputFile.write(bytes([1, 0]))

            registerBytes = [0] * 16
            lastRegisterBytes = [0] * 16

            totalSize = 0
            lastChange = 0

            for i in range(frameCount):

                anyChange = False
                for j in range(14):
                    registerBytes[j] = frames[i * 16 + j]

                    # Always write values of register 13 because whenever it's written to
                    # it resets the envelope wave
                    if i == 0 or lastRegisterBytes[j] != registerBytes[j] or j == 13:
                        if not anyChange and i != 0:
                            # Write wait instruction
                            outputFile.write(bytes([16, lastChange]))
                            totalSize = totalSize + 2

                            lastChange = 0
                        
                        # The value 255 for register 13 in a YM file is to be ignored
                        if j != 13 or registerBytes[j] != 255:
                            # Write register value
                            outputFile.write(bytes([j, registerBytes[j]]))
                            lastRegisterBytes[j] = registerBytes[j]
                            totalSize = totalSize + 2

                        anyChange = True
                
                if not anyChange:
                    lastChange = lastChange + 1
            

            print("Total size:", totalSize)

            # Write end of file
            outputFile.write(bytes([255, 255]))


    except BaseException as be:
        print("Error writing to output file", be)
        sys.exit(1)


if __name__ == "__main__":    
    print("YM Converter to SNG file format for AY-3-8910 chips")

    inputFile = ""

    if len(sys.argv) < 2:
        print("No input file")
        print()
        print("Usage:")
        print("python3 ymConverter.py inputFile [outputFile]")
        print()
        print("Note: the input file must be an uncompressed YM file in interlaced mode")
        sys.exit(1)

    inputFilename = sys.argv[1]

    outputFilename = "output.sng"

    if len(sys.argv) > 2:
        outputFilename = sys.argv[2]
    
    processYMFile(inputFilename, outputFilename)



