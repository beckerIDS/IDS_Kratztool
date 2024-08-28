import logging
import os

ICON_FULLPATH = os.path.join(os.getcwd(),"ressources","icon.ico")


STANDARD_AUFGABEN_STR = '"Kurzfragen": 15,"A7": 10,"A8": 10,"A9": 10'
STANDARD_AUFGABEN_DICT = {"Kurzfragen": 15,"A7": 10,"A8": 10,"A9": 10}
ASK_AUFGABEN_TITLE = "Hallo, bitte notwendigen Eingaben für Kratztool eingeben"
ASK_AUFGABEN_AUFFORDERUNG = "Bitte Aufgaben und zugehörige Punkte angeben (AUFGABE1:PUNKTE,AUFGABE2:PUNKTE,...)"
ASK_AUFGABEN_DICT_ERROR = 'Eignabe entspricht nicht Dictionary Formatierung: AUFGABE1:PUNKTE,AUFGABE2:PUNKTE,...!!!'
ASK_AUFGABEN_PUNKTZAHL_ERROR = 'Punkte pro Aufgabe muss größer 0 und kleiner 27 sein!!!'
ASK_ANZAHLKLAUSUREN_TITLE = "Das ist der letzte Input, ich schwöre"
ASK_ANZAHLKLAUSUREN_AUFFORDERUNG = "Wie viele Klausuren gibt es pro Mappe"
TOOL_TITLE = 'Kratztool: ESC reset all (dauert ein bisschen, pls chill bre), DEL reset single entry, UP 1, DOWN 0, LEFT and RIGHT to navigate'


logger_format = '%(asctime)s [Thread: %(threadName)s, Name: %(name)s:%(lineno)d] %(levelname)s: %(message)s'
logger_custom_level = {
    "ressources.functions": logging.DEBUG,
    "__main__":logging.INFO
}