from conllu import parse
import pickle as pk

skip= ['SYM', '_', 'PART', 'X']

def read(debug=True):
	try:
		with open('transitions.pkl', mode='rb') as file:
			binary = pk.load(file)
			file.close()
		return binary
	except Exception as e:
		if debug: print("Fichier Cache des transitions non trouvé, recalcul")

	with open('corpus.conllu', encoding='utf-8') as file:
		sents = parse(file.read())

	tokens, tags = [], []

	

	for i, sent in enumerate(sents):
		tags.append('s')
		for word in sent:
			if word['upos'] in skip:
				continue
			# tokens.append(word['form'])
			tags.append(word['upos'].lower())
		tags.append('e')

	with open('transitions.pkl', mode='wb') as file:
			binary = pk.dump(tags, file)
			file.close()

	return tags
	