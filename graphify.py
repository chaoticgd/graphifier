#!/usr/bin/env python3

"""
	Copyright (c) 2019 chaoticgd

	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all
	copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
	SOFTWARE.
"""

import os
import sys
import pydot
import subprocess

def main(src, dest):
	files = parse_dir(src)
	graph = files_to_graph(files)
	graph.write_svg(dest)

def parse_dir(path):
	result = {}
	for root, subdirs, files in os.walk(path):
		for file in files:
			if file[-4:] != '.cpp':
				continue
			metadata = parse_file(root + os.sep + file)
			if metadata == {}:
				continue
			result[metadata['name'][:-4]] = metadata
		for file in files:
			if file[-2:] != '.h':
				continue
			metadata = parse_file(root + os.sep + file)
			if metadata == {}:
				continue
			key = metadata['name'][:-2]
			if key in result:
				metadata['includes'] += result[key]['includes']
			else:
				metadata['header_only'] = True
			result[metadata['name'][:-2]] = metadata
	return result

def parse_file(path):

	if not is_in_git_repository(path):
		return {}

	result = {
		'name': os.path.basename(path),
		'desc': '',
		'includes': [],
		'entry_point': False,
		'header_only': False
	}
	parsing_description = False
	with open(path, 'r') as source_file:
		source_text = source_file.read()
		if 'int main(' in source_text:
			result['entry_point'] = True
		for line in source_text.split('\n'):
			if len(line) < 3:
				continue
			if not parsing_description:
				if line[0] != '#':
					continue
				if len(line) > 9:
					if line[1:10] == 'include "':
						included_file = os.path.basename(line[10:-3])
						result['includes'].append(included_file)
				if line[1:4] == ' /*':
					parsing_description = True
			else:
				if line[1:4] == ' */':
					parsing_description = False
				else:
					result['desc'] += line[1:].strip() + '\n'

	return result

def files_to_graph(files):
	result = 'digraph {\n'
	for name, file in files.items():
		text = name
		if file['desc'] != '':
			text += ': ' + file['desc'].strip()
		result += '\t' + name + ' ['
		result += 'label="' + split_lines(text) + '"'
		if file['entry_point']:
			result += ' color=red'
		if file['header_only']:
			result += ' color=blue'
		result += '];\n'
		for include in file['includes']:
			result += '\t' + name + ' -- ' + include + ';\n'
	pass
	result += '}'
	return pydot.graph_from_dot_data(result)[0]

def split_lines(desc):
	out_line = ''
	out_word = ''
	count = 0
	for word in desc.replace('\n', ' ').split(' '):
		count += len(word)
		if count > 20:
			out_line += out_word + '\n'
			out_word = ''
			count = 0
		out_word += word + ' '
	return out_line + out_word

dev_null = open(os.devnull, 'w')

def is_in_git_repository(path):
	try:
		subprocess.check_call(['git', 'ls-files', '--error-unmatch', path], stdout=dev_null, stderr=dev_null)
	except subprocess.CalledProcessError:
		return False
	return True

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('Incorrect number of arguments.')
		exit(1)
	main(sys.argv[1], sys.argv[2])
