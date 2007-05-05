import sys
from cStringIO import StringIO
from xml.parsers.expat import error as xml_error
from elementtree import ElementTree
from types import *
from lang import *

def input_items (input):
	def buf2elt (buf):
		buf.seek (0, 0)
		elt = None
		try:
			et = ElementTree.parse (buf)
			elt = et.getroot ()
		except xml_error, e:
			elt = None
			warn ("ignoring XML error: %s" % e)
		buf.close ()
		return elt

	buf = None
	pos = None
	try:
		for line in input:
			if line.startswith('<?xml '):
				if buf: yield (buf2elt (buf), pos)
				pos = input.tell ()
				buf = StringIO ()
			else:
				buf.write (line)
		if buf: yield (buf2elt (buf), pos)
	except:
		warn ("breaking at input position %d on data:\n%s" % (pos, buf.getvalue ()))
		raise

def setval (x, v, k):
	x[k] = v

def addval (x, v, k):
	vv = x.get (k)
	if vv:
		vv.append (v)
	else:
		x[k] = [v]
	x.setdefault (k, []).append (v)

def concval (x, v, k, sep=" "):
	vv = x.get (k)
	if vv:
		x[k] = vv + sep + v
	else:
		x[k] = v

element_dispatch = {
	'title': (setval, 'title'),
	'creator': (addval, 'author'),
	'subject': (addval, 'subject'),
	'description': (concval, 'description', "; "),
	'publisher': (setval, 'publisher'),
	'date': (setval, 'publish_date'),
	# if can be a language_code, enter that and also provide language, else store as language
	'language': (setval, 'language'),
	'sponsor': (setval, 'scan_sponsor'),
	'contributor': (setval, 'scan_contributor'),
	'identifier': (setval, 'oca_identifier')
	}

ignored = {}

def parse_item (r, pos):
	global ignored
	# ElementTree.dump (e)
	e = {}
	for field in r:
		if not ElementTree.iselement (r):
			die ("what is it: %s" % repr (r))
		text = field.text
		if text is None: continue
		tag = field.tag
		action = element_dispatch.get (tag)
		if action:
			f = action[0]
			args = action[1:]
			v = encode_val (text)
			f (e, v, *args)
		else:
			count = ignored.get (tag) or 0
			ignored[tag] = count + 1
	return e

limit = 1000

def parse_input (input):
	n = 0
	global ignored
	ignored = {}
	for (r,pos) in input_items (input):
		# if limit and n == limit: break
		if r is None: continue
		o = parse_item (r, pos)
		# print o
		n += 1
		if n % 100 == 0:
			warn ("...... read %d records" % n)
	warn ("ignored:")
	for (tag,count) in ignored.iteritems ():
		warn ("\t%d\t%s" % (count, tag))
	warn ("done.  read %d records" % n)

def encode_val (v):
	if isinstance (v, StringType):
		return v
	elif isinstance (v, UnicodeType):
		return v.encode ('utf8')
	else:
		die ("couldn't encode value: %s" % repr (v))

parse_input (sys.stdin)