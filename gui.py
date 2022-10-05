import PySimpleGUI as sg
from main import Etiqueteur
from lang import LANG


langage = "Fr"

layout_main = [[sg.Text('Étiquetage morpho-syntaxique', font="Arial 12")],
			   [sg.Multiline(key="phrase", size=(30, 5))],
			   [sg.Text('', size=(40, None), key='structure', visible=False)],
			   [sg.Button('Valider')], 
			   [sg.Text('@Aniss Université Hassiba benbouali de Chlef')]]


window = sg.Window("Étiqueteur", layout_main, element_justification='c')

from main import Dictionnaire, Variation
tagger = Etiqueteur(debug=True)

while True:
	event, values = window.read()
	if event == 'Valider':
		try:
			if values["phrase"] != '':
				resultat, phrase = tagger.etiqueter(values['phrase'])
				print(resultat)
				resultat = [LANG[langage][x] for x in resultat]
				print(resultat, phrase)
				window['structure'].update(list(zip(resultat, phrase)), visible=True)
		except Exception as e:
			window['structure'].update({e: e}, visible=True)

	if event == sg.WIN_CLOSED or event == "Quitter":
		break

	print(values)

window.close()