# coding=utf-8
import nltk         # http://nltk.org/
import collections
import string
import re
import os.path
import glob
import cPickle as pickle
import copy
import urllib

from sklearn.manifold import MDS
import numpy as np
import matplotlib.pyplot as plt

from math import sqrt

# NB you must have run the nltk.download() before first use, to get a language model for english

qual_filepaths = ["Resources/peerj/qual/43.methods", "Resources/peerj/qual/39.methods", "Resources/peerj/qual/11.methods", "Resources/peerj/qual/8.methods"]

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
	ngramlens = [1, 2]
	counted = collections.Counter()
	for ngramlen in ngramlens:
		thisgramcounter = collections.Counter()
		for sent in sentences:
			for position in range(len(sent) + 1 - ngramlen):
				thisgramcounter.update({" ".join([x[0] for x in sent[position:position+ngramlen]]): 1}) # add 1
		# next we up-weight the counts by raising them to the power of their ngram length (to account for the null model rarity of long ngrams)
		thisgramcounter = {k:v**ngramlen for k,v in thisgramcounter.items()}
		counted.update(thisgramcounter)

	print "==================="
	print "Most common ngrams:"
	for item in counted.most_common(20):
		print item
	return counted

def analyse_folderfull_of_methods(globber):
	filepaths = glob.glob(globber)
	analyses = {}
	grandwordlist = collections.Counter()
	for fp in filepaths:
		#basename = os.path.basename(fp)
		try:
			f = open("%s.pickle" % fp, 'rb')
			analyses[fp] = pickle.load(f)
			f.close()
		except:
			f = open(fp, 'r')
			thetext = f.read()
			f.close()
			analyses[fp] = text_to_counts(thetext)
			pickle.dump(analyses[fp], open("%s.pickle" % fp, 'wb'), -1)
		grandwordlist.update(analyses[fp])

	print "GRAND MOST COMMON:"
	print grandwordlist.most_common(20)
	return (analyses, grandwordlist)

def mds_of_wordbags(train_analyses, test_analyses, grandwordlist):
	analyses = copy.copy(train_analyses)
	analyses.update(test_analyses)
	filepaths = sorted(analyses.keys())
	train_filepaths = sorted(train_analyses.keys())
	test_filepaths = sorted(test_analyses.keys())
	wordlist = sorted(grandwordlist.keys())
	# reduce dimnality
	#wordlist = wordlist[0::100]
	wordlist = [x[0] for x in grandwordlist.most_common(300)]  # 300
	print "dimensionality of wordlist: %i" % len(wordlist)
	print wordlist
	countsmat = []
	for index, filepath in enumerate(filepaths):
		someresults = [analyses[filepath].get(aword, 0) for aword in wordlist]
		countsmat.append(someresults)
	countsmat = np.array(countsmat)

	# For each pair, find distance
	#distances = [[sum(countsmat[x][d] != countsmat[y][d] for d in range(len(wordlist))) for y in range(len(countsmat))] for x in range(len(countsmat))]
	distances = [[sum(abs(countsmat[x][d] - countsmat[y][d]) for d in range(len(wordlist))) for y in range(len(countsmat))] for x in range(len(countsmat))]
	#distances = [[sqrt(sum((countsmat[x][d] - countsmat[y][d])**2 for d in range(len(wordlist)))) for y in range(len(countsmat))] for x in range(len(countsmat))]
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
	for whichitem, filepath in enumerate(train_filepaths):
		"""
		if idnumber in qual_numbers:
			postfix = '<<<Q';
		else:
			postfix = ''
		plt.text(pos[whichitem, 0], pos[whichitem, 1], "%i%s" % (idnumber, postfix), fontsize='xx-small')
		"""
		if filepath in qual_filepaths:
			qualpos[0].append(pos[whichitem, 0])
			qualpos[1].append(pos[whichitem, 1])
	plt.plot(qualpos[0], qualpos[1], 'rx')
	#plt.plot(pos[:n,0], pos[:n,1], 'x')
	#plt.plot(pos[n:,0], pos[n:,1], '+')
	#plt.show()
	plt.xticks([])
	plt.yticks([])
	plt.title("Papers organised by unigram/bigram distance (red=qualitative)", fontsize='xx-small')
	plt.savefig("plot_parsemethodtext.pdf", papertype='A4', format='pdf')

	######################################################################
	# Construct a larger MDS embedding in order to classify by NN
	metric = True
	n_components= 4
	mds = MDS(n_components=n_components, metric=metric, max_iter=3000, eps=1e-12,
			dissimilarity="precomputed", n_jobs=1, n_init=1)
	pos = mds.fit_transform(np.array(distances))

	tp = 0
	tn = 0
	fp = 0
	fn = 0
	for whichitem, filepath in enumerate(train_filepaths):
		# find NNs for this item
		bestother = 0
		bestdist = 9e99
		for whichother, otherfilepath in enumerate(train_filepaths):
			if otherfilepath==filepath: continue
			distance = 0
			for dim in range(n_components):
				distance += abs(pos[whichitem,dim] - pos[whichother,dim])
			if distance < bestdist:
				bestdist = distance
				bestother = otherfilepath
		# decide if matches
		if (filepath in qual_filepaths):
			if (bestother in qual_filepaths):
				tp += 1
			else:
				fn += 1
		else:
			if (bestother in qual_filepaths):
				fp += 1
			else:
				tn += 1

	print tp
	print tn
	print fp
	print fn

	n_true = tp + tn
	n_false = fp + fn
	print "%i matched, %i failed (%0.3g%%)" % (n_true, n_false, (100. * n_true) / (n_true + n_false))

	print "====================================-================"
	print "Articles from biomed which I hope may be qualitative:"

	for whichitem, filepath in enumerate(test_filepaths):
		# find NNs for this item
		bestother = 0
		bestdist = 9e99
		for whichother, otherfilepath in enumerate(train_filepaths):
			if otherfilepath==filepath: continue
			distance = 0
			for dim in range(n_components):
				distance += abs(pos[whichitem,dim] - pos[whichother,dim])
			if distance < bestdist:
				bestdist = distance
				bestother = otherfilepath
		# decide if matches
		if (bestother in qual_filepaths):
			print urllib.unquote(os.path.basename(os.path.dirname(filepath)))


################################################
if __name__=='__main__':
	grandwordlist = collections.Counter()
	(train_analyses, train_grandwordlist) = analyse_folderfull_of_methods('Resources/peerj/*/*.methods')
	grandwordlist.update(train_grandwordlist)
	(test_analyses, test_grandwordlist) = analyse_folderfull_of_methods('harvest/hostdata/www.biomedcentral.com/*/methods.txt')
	grandwordlist.update(test_grandwordlist)
	mds_of_wordbags(train_analyses, test_analyses, grandwordlist)

