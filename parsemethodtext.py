# coding=utf-8
import nltk         # http://nltk.org/
import collections
import string
import re
import os.path
import glob
import cPickle as pickle

from sklearn.manifold import MDS
import numpy as np
import matplotlib.pyplot as plt

# NB you must have run the nltk.download() before first use, to get a language model for english

qual_numbers = [43, 39, 11, 8]

from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
	def __init__(self):
		self.reset()
		self.fed = []
	def handle_data(self, d):
		self.fed.append(d)
	def get_data(self):
		return ''.join(self.fed)
def strip_tags(html):
	s = MLStripper()
	s.feed(html)
	return s.get_data()

def ie_preprocess(document):
	document = document.lower()
	document = re.sub(r'[^\w\s]','',document)
	sentences = strip_tags(document)
	sentences = nltk.sent_tokenize(document)
	sentences = [nltk.word_tokenize(sent) for sent in sentences]
	sentences = [[w for w in sent if w not in nltk.stem.stopwords.words('english')] for sent in sentences]
	sentences = [nltk.pos_tag(sent) for sent in sentences]
	return sentences




def text_to_counts(document):
	print "NLTK preprocessing..."
	sentences = ie_preprocess(strip_tags(document))

	print "Counting..."
	countlist = []
	ngramlens = [1, 2]
	for sent in sentences:
		#print sent
		#print ""
		for ngramlen in ngramlens:
			for position in range(len(sent) + 1 - ngramlen):
				#print sent[position:position+ngramlen]
				#print [x[0] for x in sent[position:position+ngramlen]]
				countlist.append(" ".join([x[0] for x in sent[position:position+ngramlen]]))

	counted = collections.Counter(countlist)
	print "==================="
	print "Most common %i-grams:" % ngramlen
	for item in counted.most_common(20):
		print item
	return counted

def analyse_folderfull_of_methods(folder):
	filepaths = glob.glob("%s/*/*.methods" % folder)
	analyses = {}
	grandwordlist = collections.Counter()
	for fp in filepaths:
		basename = os.path.basename(fp)
		try:
			f = open("%s.pickle" % fp, 'rb')
			analyses[basename] = pickle.load(f)
			f.close()
		except:
			f = open(fp, 'r')
			thetext = f.read()
			f.close()
			analyses[basename] = text_to_counts(thetext)
			pickle.dump(analyses[basename], open("%s.pickle" % fp, 'wb'), -1)
		grandwordlist.update(analyses[basename])

	print "GRAND MOST COMMON:"
	print grandwordlist.most_common(20)
	return (analyses, grandwordlist)

def mds_of_wordbags(analyses, grandwordlist):
	basenames = sorted(analyses.keys())
	idnumbers = [int(basename.split('.')[0]) for basename in basenames]
	wordlist = sorted(grandwordlist.keys())
	# reduce dimnality
	#wordlist = wordlist[0::15]
	wordlist = [x[0] for x in grandwordlist.most_common(300)]
	print "dimensionality of wordlist: %i" % len(wordlist)
	print wordlist
	countsmat = []
	#print basenames
	for index, basename in enumerate(basenames):
		someresults = [analyses[basename].get(aword, 0) for aword in wordlist]
		countsmat.append(someresults)
	countsmat = np.array(countsmat)


	# For each pair, find Hamming distance
	#distances = [[sum(countsmat[x][d] != countsmat[y][d] for d in range(len(wordlist))) for y in range(len(countsmat))] for x in range(len(countsmat))]
	distances = [[sum(abs(countsmat[x][d] - countsmat[y][d]) for d in range(len(wordlist))) for y in range(len(countsmat))] for x in range(len(countsmat))]
	#print "Pairwise distances:"
	#for distrow in distances:
	#	print distrow

	######################################################################
	# Construct a 2D MDS embedding using our distances
	metric = True
	mds = MDS(n_components=2, metric=metric, max_iter=3000, eps=1e-12,
			dissimilarity="precomputed", n_jobs=1, n_init=1)
	pos = mds.fit_transform(np.array(distances))

	plt.figure()
	plt.plot(pos[:,0], pos[:,1], 'x')
	qualpos = [[],[]]
	for whichitem, idnumber in enumerate(idnumbers):
		"""
		if idnumber in qual_numbers:
			postfix = '<<<Q';
		else:
			postfix = ''
		plt.text(pos[whichitem, 0], pos[whichitem, 1], "%i%s" % (idnumber, postfix), fontsize='xx-small')
		"""
		if idnumber in qual_numbers:
			qualpos[0].append(pos[whichitem, 0])
			qualpos[1].append(pos[whichitem, 1])
	plt.plot(qualpos[0], qualpos[1], 'rx')
	#plt.plot(pos[:n,0], pos[:n,1], 'x')
	#plt.plot(pos[n:,0], pos[n:,1], '+')
	#plt.show()
	plt.xticks([])
	plt.yticks([])
	plt.savefig("plot_parsemethodtext.pdf", papertype='A4', format='pdf')

	######################################################################
	# Construct a larger MDS embedding in order to classify by NN
	metric = True
	n_components=4
	mds = MDS(n_components=n_components, metric=metric, max_iter=3000, eps=1e-12,
			dissimilarity="precomputed", n_jobs=1, n_init=1)
	pos = mds.fit_transform(np.array(distances))

	n_true = 0
	n_false = 0
	for whichitem, idnumber in enumerate(idnumbers):
		# find NNs for this item
		bestother = 0
		bestdist = 9e99
		for whichother, otheridnumber in enumerate(idnumbers):
			distance = 0
			for dim in range(n_components):
				distance += abs(pos[whichitem,dim] - pos[whichother,dim])
			if distance < bestdist:
				bestdist = distance
				bestother = otheridnumber
		# decide if matches
		hasmatched = ((idnumber in qual_numbers) == (bestother in qual_numbers))
		print hasmatched
		if hasmatched:
			n_true += 1
		else:
			n_false += 1

	print "%i matched, %i failed" % (n_true, n_false)

################################################
if __name__=='__main__':
	#analyse_some_text(text)
	(analyses, grandwordlist) = analyse_folderfull_of_methods('Resources/peerj')
	mds_of_wordbags(analyses, grandwordlist)

