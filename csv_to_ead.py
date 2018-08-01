import csv
import argparse
import sys
from xml.etree.ElementTree import Element, SubElement, Comment, tostring, ElementTree
from xml.dom import minidom
import tkinter
from tkinter import messagebox

class EadTag():
	def __init__(self, tagname, value, attributes=None):
		self.tagname = tagname
		self.value = value
		self.attributes = attributes

	def title_element_in_value(self):
		if '<title' in self.value:
			return True
		else:
			return False

	def process_titles(self):
		'''Chops value into parts, plain text sections and Title elements and adds them to a list'''
		value = self.value
		value_elements = []
		while len(value) > 0:
			if '<title' in value:
				if value.startswith('<title'):
					#isolate title snippet to create title object
					try:
						title_slice = value[0:value.index("</title>")]
					except ValueError:
						print('Closing title tag not found in ' + self.value)
						messagebox.showerror("Error", 'Closing title tag not found in ' + self.value)
						raise SystemExit
					value = value[value.index("</title>") + 8:] #remove closing tag from remainder of title
					render = ''
					try:
						if 'render' in title_slice:
							if 'render=”' in title_slice:
								r_index = title_slice.index('render=”') + 8
								end_r_index = title_slice.index('”', r_index)
								render = title_slice[r_index:end_r_index]
							elif 'render=\"' in title_slice:
								r_index = title_slice.index('render=\"') + 8
								end_r_index = title_slice.index('\"', r_index)
								render = title_slice[r_index:end_r_index]
					except ValueError:
						print('render=” or render=\" not found in ' + self.value)
						messagebox.showerror("Error", 'render=” or render=\" not found in ' + self.value)
						raise SystemExit
					title_slice = title_slice[title_slice.index('>')+1:]
					value_elements.append(Title(title_slice, render))
				else:
					#create text snippet and append to element list
					try:
						value_elements.append(value[:value.index("<title")])
						value = value[value.index("<title"):]
					except ValueError:
						print(self.value)
						raise SystemExit
			else:
				value_elements.append(value)
				value = ''
		return value_elements

	def build_complex_value(self, element_tag):
		value_elements = self.process_titles()
		e = Element(element_tag)
		current_element = e
		for vp in value_elements:
			if current_element == e and vp.__class__.__name__.lower() != "title":
				e.text = vp
			else:
				if vp.__class__.__name__.lower() == "title":
					current_element = vp.output_ead()
					e.append(current_element)
				else:
					current_element.tail = vp
		return e


	def output_ead(self):
		if self.title_element_in_value:
			return build_complex_value(self.tagname)
		else:
			e = Element(self.tagname)
			e.text = self.value
			return e

class Container(EadTag):
	def __init__(self, value, container_type, label="mixed materials"):
		self.tagname = self.__class__.__name__.lower()
		self.value = value
		self.container_type = container_type
		self.label = label.lower()

	def output_ead(self):
		e = Element(self.tagname, {'type':self.container_type})
		e.text = self.value
		#only add container label for top level container types
		if self.container_type == "Box" or self.container_type == "Oversize" or self.container_type == "Digital_file":
			e.set("label", self.label)
		return e

class UnitDate(EadTag):
	def __init__(self, value, datetype=None, normal=None, label=None):
		self.tagname = self.__class__.__name__.lower()
		self.value = value
		self.datetype = datetype
		self.normal = normal
		self.label = label

	def output_ead(self):
		e = Element(self.tagname)
		e.text = self.value
		if self.datetype is not None:
			e.set("type", self.datetype)
		if self.normal is not None:
			e.set("normal", self.normal)
		if self.label is not None:
			e.set("label", self.label)
		return e

class UnitTitle(EadTag):
	def __init__(self, value):
		self.tagname = self.__class__.__name__.lower()
		self.value = value

	def output_ead(self):
		if self.title_element_in_value():
			return self.build_complex_value(self.tagname)
		else:
			e = Element(self.tagname)
			e.text = self.value
			return e

class Title(EadTag):
	def __init__(self, value, render):
		self.tagname = self.__class__.__name__.lower()
		self.value = value
		self.render = render

	def __str__(self):
		return self.value

	def output_ead(self):
		e = Element('title')
		e.set("render", self.render)
		e.text = self.value
		return e

class Note(EadTag):
	def __init__(self, value, note_header):
		self.tagname = 'odd'
		self.value = value
		self.note_header = note_header

	def output_ead(self):
		e = Element(self.tagname)
		header = SubElement(e, 'head')
		header.text = self.note_header
		if self.title_element_in_value():
			e.append(self.build_complex_value('p'))
		else:
			note = SubElement(e, 'p')
			note.text = self.value
		return e

class ComponentEntry(EadTag):
	def __init__(self, component_elements=None):
		#print(component_elements)
		try:
			self.level = component_elements['level']
			self.level_type = component_elements['level_type'].lower()
		except KeyError as e:
			print("Level or Level Type not found in data, required for EAD creation")
			raise SystemExit
		self.unittitle = component_elements.pop('unittitle', None)
		self.scopecontent = component_elements.pop('scopecontent', None)
		self.accessrestrict = component_elements.pop('accessrestrict', None)
		self.userestrict = component_elements.pop('userestrict', None)
		self.containers = {}
		self.containers['box'] = component_elements.pop('box', None)
		self.containers['folder'] = component_elements.pop('folder', None)
		self.containers['oversize'] = component_elements.pop('oversize', None)
		self.containers['digital'] = component_elements.pop('digital_file', None)
		self.date = component_elements.pop('date', None)
		self.note = component_elements.pop('general_note', None)

	def output_ead(self):
		c_level = Element('c', {'level':self.level_type})
		did_elem = SubElement(c_level, 'did')
		if self.unittitle is not None:
			title_elem = UnitTitle(self.unittitle).output_ead()
			did_elem.append(title_elem)
		if self.date is not None and self.date != '':
			date_elem = UnitDate(self.date).output_ead()
			did_elem.append(date_elem)
		if self.containers['box'] is not None and self.containers['box'] != '':
			did_elem.append(Container(self.containers['box'], 'Box').output_ead())
		if self.containers['oversize'] is not None and self.containers['oversize'] != '':
			cont_elem = Container(self.containers['oversize'], 'Oversize').output_ead()
			did_elem.append(cont_elem)
		if self.containers['folder'] is not None and self.containers['folder'] != '':
			did_elem.append(Container(self.containers['folder'], 'Folder').output_ead())
		if self.containers['digital'] is not None and self.containers['digital'] != '':
			did_elem.append(Container(self.containers['digital'], 'Digital_file').output_ead())
		if self.note is not None and self.note != '':
			c_level.append(Note(self.note, 'General note').output_ead())
		return c_level

class ContainerListData():
	def __init__(self, inputfile):
		self.rows = []
		self.valid_header_vals = ['level', 'level_type', 'unittitle', 'unitid', 'date', 'begin_date', 'end_date', 'box', 'folder', 'oversize', 'digital_file', 'instance_type', 'general_note', 'accessrestrict', 'userestrict', 'scopecontent']
		self.header_index = {}
		self.header = None

		with open(inputfile, 'rt', encoding="utf8") as f:
			try:
				reader = csv.reader(f, dialect='excel')
				for i, r in enumerate(reader):
					# if header row, set that to header variable
					if i == 0:
						self.header = r
						self.translate_legacy_headers()
						self.validate_header_values()
					# otherwise set to row data, ignore blank rows
					# it is assumed the first column will either be level or level_name which should always have a value
					else:
						if r[0].strip() != "":
							clean_row = []
							for e in r:
								clean_e = e.strip()
								clean_row.append(clean_e)
							self.rows.append(clean_row)
			except UnicodeDecodeError as err:
				#Let the user know there are some pesky non-utf-8 chars in their csv
				messagebox.showerror("Error", "Non UTF-8 character encountered\n" + str(err))
				raise SystemExit
		self.set_header_value_positions()
		self.clean_entry_values()

	# validate header values and set their positions
	def set_header_value_positions(self):
		invalid = self.validate_header_values()
		#if not self.validate_header_values():
		if len(invalid) == 0:
			for index, val in enumerate(self.header):
				val = val.lower().strip()			#normalize header values by lowering case and strip extraneous white space
				self.header_index[val] = index
		else:
			print('No header values or invalid headers found, make sure first row has valid header values')
			err_msg = "Invalid headers found: "
			for invalid in self.validate_header_values():
				print(invalid)
				err_msg = err_msg + ', ' + invalid
			messagebox.showerror("Error", err_msg)
			sys.exit()

	def validate_header_values(self):
		invalid_headers = []
		if self.header is not None:
			for val in self.header:
				invalid = True
				val = val.lower().strip()
				for valid_header_val in self.valid_header_vals:
					if val == valid_header_val or val == '':  #blank header allowed for cases where there was space in the csv source (eg: Excel) but no data in column, if data in column of blank header it will be ignored
						invalid = False
				if invalid:
					invalid_headers.append(val)
		#print(len(invalid_headers))
		return invalid_headers

	def translate_legacy_headers(self):
		print('translating legacy headers')
		if self.header is not None:
			for i, val in enumerate(self.header):
				val = val.lower().strip()
				if val == 'level type':
					val = 'level_type'
				if val == 'title':
					val = 'unittitle'
				if val == 'df':
					val = 'digital_file'
				if val == 'instance type':
					val = 'instance_type'
				if val == 'general note':
					val = 'general_note'
				if val == 'restrictions':
					val = 'accessrestrict'
				self.header[i] = val
		print(self.header)


	# Remove extraneous white space at the beginning and end of elements
	# this white space can cause problems in programs like ArchiveSpace when ingesting the EAD
	def clean_entry_values(self):
		for row in self.rows:
			for entry in row:
				entry = entry.strip()

	def output_ead(self, outputfile):
		root = Element('dsc')
		current_parents = [root]
		parent_index = 0
		for current_row, row in enumerate(self.rows):
			entry_values = {}
			level_val = int(row[self.header_index['level']])
			parent_index = level_val - 1

			for e, index in self.header_index.items():
				entry_values[e] = row[index]
			ce = ComponentEntry(entry_values)

			c_element = ce.output_ead()
			current_parents[parent_index].append(c_element)
			if len(current_parents) <= level_val:
				current_parents.append(c_element)
			else:
				current_parents[level_val] = c_element

		indent(root)
		tree = ElementTree(root)
		tree.write(outputfile, encoding='utf8')

def indent(elem, level=0):
	i = "\n" + level*"  "
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + "  "
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			indent(elem, level+1)
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i

def main():
	inputfile = ''
	outputfile = ''
	argsparser = argparse.ArgumentParser()
	argsparser.add_argument('csv', help='csv filename', nargs='*')
	args = argsparser.parse_args()

	root = tkinter.Tk()
	root.withdraw()

	# import container data from csv file,
	# csv should be encoded UTF-8 to make sure there are no issues when writing XML
	for csvfile in args.csv:
		try:
			inputfile = csvfile
			outputfile = csvfile.replace(".csv", ".xml")
			csvdata = ContainerListData(inputfile)
			csvdata.output_ead(outputfile)
		except SystemExit:
			print("Program terminated")
			return

if __name__ == "__main__":
	main()
