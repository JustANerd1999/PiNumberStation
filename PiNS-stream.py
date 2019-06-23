#!/usr/bin/python
#
# PiNumberStation over icecast 
#
# Requires:
# 	- icecast 		 (https://icecast.org/download | brew install icecast)
#	- liquidsoap 	 (https://www.liquidsoap.info/doc-dev/install.html)
#	- liquidsoap-cry (liquidsoup plugin for stream to icecast)
#
# Configure:
# 	- 1. (required) Setup icecast: edit ```/etc/icecast.xml```, ```/usr/local/etc/icecast.xml```
#	- 2. (required) Run icecast: run ```icecast -c /usr/local/etc/icecast.xml -b```
#	- 3. (optional) Setup message: edit ```default.ini``` section streaming
#   - 4. (required) Setup liquidsoap config: edit ```streaming/config.liq``` with your host, and port (the same of icecast.xml)
#   - 5. (optional) Setup trasmission: edit ```streaming/stream.liq```
#
# Usage:
#
# ./PiNS-stream.py --text "my message"
# ./PiNS-stream.py --text "my message" --key "key for encrypt text with Vernam's Cipher"
#
import sys
import subprocess # for calling console
import wave
import os.path
import ConfigParser
from random import choice
import argparse

parser = argparse.ArgumentParser(prog="enc", add_help=True, description='Encrypt text with VernamCipher')
parser.add_argument('--conf', '--config', '-c', metavar='config', default="default.ini", type=str, help='Config file')
parser.add_argument('--text', '--string', '-t', metavar='text', default="hello", type=str, help='text to crypt')
parser.add_argument('--key',  '--pass',   '-k', metavar='key', default="", type=str, help='Encrypt text with VernamCipher')
args = parser.parse_args()


config = ConfigParser.ConfigParser()
# Sounds for digits/numbers.
sounds = ["zero.wav", "one.wav", "two.wav", "three.wav", "four.wav", "five.wav", "six.wav", "seven.wav", "eight.wav", "nine.wav"]

# Sounds for alphanumeric. Use NATO Phonetic
alpha = [
	"alpha", "bravo", "charlie", "delta",  "echo", "foxtrot", "golf",
	"hotel", "india", "juliet", "kilo", "lima", "mike", "november", "oscar",
	"papa", "quebec", "romeo", "sierra", "tango", "uniform", "victor",
	"whiskey", "x-ray", "yankee", "zulu"
]

def getVO( character ):
	if character.isdigit() == True:
		return sounds[int(character)]
	else:
		if character == ',' or character == ' ':
			return "_comma.wav"
		if character == '.':
			return "_period.wav"
		if character == '\n':
			return "nova.wav"

		if character.isalpha() == True:
			return "/alpha/" + str(alpha[ord(character) - ord('a')] + ".wav")


def constructWav( strMessage ):
	print("Synthesizing Message..")

	infiles = []
	strMessageOut = strMessage


	# determine infiles for message.

	for file in config.get('streaming', 'prepend').split(","):
		if not file[0] == "/" or not file[0] == ".":
			file = sys.path[0] + "/" + file

		if os.path.exists(file):
			infiles.append(file)
		else:
			print  "File %s not exists ... skipped!" % file

	for character in strMessageOut:
		char_sound = sys.path[0] + "/vo/" + getVO(character)
		infiles.append(char_sound)
		print "\t %s => %s" % (character, getVO(character))

	for file in config.get('streaming', 'append').split(","):
		if not file[0] == "/" or not file[0] == ".":
			file = sys.path[0] + "/" + file

		if os.path.exists(file):
			infiles.append(file)
		else:
			print  "File %s not exists ... skipped!" % file

		infiles.append(file)

	infiles.append(sys.path[0] + "/vo/off3.wav")

	outfile = sys.path[0] + "/message.wav"
	data    = []

	for infile in infiles:
	    w = wave.open(infile, 'rb')
	    data.append( [w.getparams(), w.readframes(w.getnframes())] )
	    w.close()

	output = wave.open(outfile, 'wb')
	output.setparams(data[0][0])

	for x in range(0, len(infiles)):
		output.writeframes(data[x][1])

	output.close()
	print("Synthesis Complete..")

	return


if __name__ == "__main__":
	config.read(args.conf)

	if len(args.key) > 0:
		process=subprocess.Popen([sys.path[0] + "/encoder.py", "--enc-text", args.text, "--enc-key", args.key], stdout=subprocess.PIPE)
		result=process.stdout.readlines()[-1]
		print(result)
		message=result.rstrip()
	else:
		message=args.text


	if not message:
		raise Exception("Empty PiNumberStation message")

	constructWav(message)
	subprocess.call([sys.path[0] + "/streaming/stream.liq"]);