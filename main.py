"""
Aniss HALFAOUI

annotation des corpus en utilsant modèle markov cachée, l'apprentissage est fait sur le corpus déjà annoté
par Sequoia.

Ce programme n'est utilisé que dans le cadre d'un mémoire de recherche et non redistributable.
Ce programme n'est pas optimisé pour annoter de larges corpus.

Université Hassiba Benaouli de Chlef
"""

import sys
from collections import Counter
from sequoia import read
import pandas as pd
import pickle as pk
from copy import deepcopy

Translate = {
	'ADJ:ind': 'adj', 
	'PRE': 'adp', 
	'ART:ind': 'det',
	'LIA': 'nom',
	'VER': 'verb',
	'ART:def': 'det',
	'PRO:dem': 'pron',
 	'PRO:ind': 'pron',
 	'ADJ:dem': 'det',
 	'PRO:int': 'pron',
 	'ONO': 'noun',
 	'ONO': 'intj',
 	'PRO:per': 'pron',
 	'PRO:pos': 'det',
 	'ADJ:int': 'adj', 
 	'CON': 'cconj', 
 	'AUX': 'aux',
 	'ADV': 'adv',
 	'ADJ:pos': 'adj',
 	'PRO:rel': 'sconj',
 	'ADJ:num': 'num',
 	'NOM': 'noun',
 	'ADJ': 'adj'
}


class Transition(object):
	def __init__(self):
		self._cgrams = read()
		self._cgrams_set = list(set(self._cgrams))
		self.bigram = [(cgram1, cgram2) for cgram1, cgram2 in zip(self._cgrams, self._cgrams[1:])]

		
		self._tag_count = Counter(self._cgrams)
		self._bigram_count = Counter(self.bigram)

	def get_transition(self, prev, next):
		prev =  prev.lower()
		next = next.lower()
		try:
			return self._bigram_count.get((prev, next))/self._tag_count.get(prev)
		except TypeError:
			if prev in self._cgrams_set and next in self._cgrams_set:
				return 0
			else:
				return KeyError('catégorie grammaticale non trouvé')

	def get_all_transition_given(self, prev):
		probs = {}
		for cgram in self._cgrams_set:
			probs[cgram] = self.get_transition(prev, cgram)
		return probs

	def get_max_transition_given(self, prev):
		return sorted(self.get_all_transition_given(prev).items(), key=lambda x: x[1], reverse=True)[0]

class Variation(object):
	def __init__(self, flex, lemme, cgram, freq):
		self.flex = flex
		self.lemme = lemme
		self.cgram = cgram
		self.freq = freq

	def __repr__(self):
		return self.flex

class Dictionnaire(object):
	def __init__(self):
		self.words = {}

	def add(self, word, lemme, cgram, freq):
		if word not in self.words.keys():
			self.words[word] = []
		try:
			freq = float(freq.replace(',', '.'))
			self.words[word].append(Variation(word, lemme, Translate[cgram], freq))
		except Exception as e:
			print("le mot", word, "a été ignoré: ", e)

		return self

	def get(self, word):
		# Pour les mots avec l'apostrophe
		if "'" in word:

			try:
				return self.words[word]
			except KeyError:
				return self.words[word.replace("'", "")]

		return self.words[word]



	def get_prob_by_word(self, word, cgram):
		try:
			cgrams = {el.cgram: el.freq for el in self.get(word)}
			return cgrams[cgram]/sum(v for k,v in cgrams.items())
		except KeyError:
			return 0

	@staticmethod
	def from_pickle(file):
		try:
			with open('dic.pkl', mode='rb') as file:
				binary = pk.load(file)
				file.close()
			dic = binary
		except Exception:
			print('INFO:','Fichier pickle non trouvé, chargement à partir du fichier csv')
			dic = Dictionnaire.from_df('dictionnaire.csv')
		return dic

	@staticmethod
	def from_df(file):
		dic = Dictionnaire()

		df = pd.read_csv(file)
		length = len(df)
		for i, row in df.iterrows():
			if i % 1000 == 0:
				print("Chargement du dictionnaire {}%".format(round((i/length)*100)),end='\r')

			dic.add(row['ortho'], row['lemme'], row['cgram'], row['freqlivres'])

		with open('dic.pkl', mode='wb') as file:
			pk.dump(dic, file)
			file.close
		return dic

class Etiqueteur(object):
	def __init__(self, debug=False):
		self._debug = debug
		if self._debug: print("INFO","Chargement du dictionnaire")
		self._dic = Dictionnaire.from_pickle('dic.pkl')
		if self._debug: print("INFO", "Chargement terminé avec", len(self._dic.words), 'mots')
		if self._debug: print("INFO",'Chargement des probabilté de transitions')
		self._transition = Transition()
		if self._debug: print("INFO", "Chargé avec", len(self._transition._bigram_count), 'combinations')
		self._prev_cgram = 's'

	def decouper(self, phrase):
		import re
		words = re.findall(r"[a-zéèêâàçûù-]+[']*", phrase.lower())
		return words

	def	etiqueter(self, phrase):
		structure, obs = self.viterbi(phrase)
		return structure, obs

	def viterbi(self, sentence):

		states = deepcopy(self._transition._cgrams_set)
		states.remove('s')
		states.remove('e')
		obs = self.decouper(sentence)
		start_prob = {k:v for k, v in self._transition.get_all_transition_given('S').items() if v != 0}

		V = [{}]

		path = {}

		# Étape 0
		for y in states:
			#print(start_prob[y], self._dic.get_prob_by_word(obs[0], y))
			V[0][y] = start_prob[y] * self._dic.get_prob_by_word(obs[0], y)
			path[y] = [y]

		# mot introuvable 
		# if max(V[0][y] for y in states) == 0:
		# 	V[0]['propn'] = 1.0

		for t in range(1, len(obs)):

			V.append({})
			newpath = {}

			for y in states:
				"""
				V => trellis
				Tm => Probabilité de transition
				Em => Probabilité d'émission

				k ← argmax(k in trellis[k, o-1] * Tm[k, s] * Em[s, o])
            	trellis[s, o] ← trellis[k, o-1] * Tm[k, s] * Em[s, o]
            	pointers[s, o] ← k
				"""
				(prob, state) = max((V[t-1][y0] * self._transition.get_transition(y0, y) * self._dic.get_prob_by_word(obs[t], y), y0) for y0 in states)
				V[t][y] = prob
				newpath[y] = path[state] + [y]
			path = newpath


		if len(obs) == 1:
			(prob, state) = max((V[0][y], y) for y in states)
			return path[state], obs
			
		(prob, state) = max((V[t][y], y) for y in states)
		if self._debug : print((prob, path[state]))

		if self._debug: print(V)
		return path[state], obs


t = Etiqueteur()

probs = {}

for y in t._transition._cgrams_set:
	probs[y] = t._transition.get_all_transition_given(y)

data = {}
order = []
from lang import LANG

for cgram,prob in probs.items():
	data[cgram] = []
	order.append(cgram)
	for k,v in prob.items():
		data[cgram].append(str(v).replace(".", ","))

# for k,d in data.items():
# 	print("===={}====".format(LANG["Fr"][k]))
# 	print(list(zip(order, d)))

# print(data)

df = pd.DataFrame(data=data, index=order)
df.to_csv("probs.csv")
print(df.head())