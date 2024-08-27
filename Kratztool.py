import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QLabel
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
import tkinter as tk
from tkinter import simpledialog, messagebox
import ast
import darkdetect

"""
REQUIREMENTS
Python Version > 3.6


USAGE
1. Mount path where Kratztool.py and  requirements.txt are located: SHIFT + RIGHTCLICK on folder where files are located -> Open in Terminal

2. Install required packages: $pip install -r requirements.txt$

3. Run this script: $python Kratztool.py$
"""




""" Compile command for shell
PyInstaller --onefile --noconsole Kratztool.py

NOT POSSIBLE TO DO ON UNIVERSITY PC BECAUSE BIT DEFENDER INTERFERES!
ALSO DELETES COMPILED EXECUTABLES!!!!
"""
def init_app() -> None:
    # Initialize Tkinter window
    application_window = tk.Tk()
    application_window.withdraw()
    # Get valid User Input or cancel
    while True:
        aufgaben = simpledialog.askstring(title="Hallo, bitte notwendigen Eingaben für Kratztool eingeben",
            prompt="Bitte Aufgaben und zugehörige Punkte angeben (AUFGABE1:PUNKTE,AUFGABE2:PUNKTE,...)",
            parent=application_window,
            initialvalue='"Kurzfragen": 15,"A7": 10,"A8": 10,"A9": 10')
        if aufgaben is None: return
        try:
            aufgaben_dict = ast.literal_eval(f"{{{aufgaben}}}")
        except SyntaxError:
            messagebox.showerror('ALARM', 'Eignabe entspricht nicht Dictionary Formatierung: AUFGABE1:PUNKTE,AUFGABE2:PUNKTE,...!!!')
            continue
        if not all([(item > 0 and item < 27) for item in aufgaben_dict.values()]):
            messagebox.showerror('ALARM', 'Punkte pro Aufgabe muss größer 0 und kleiner 27 sein!!!')
            continue
        break
    klausuren_pro_mappe = simpledialog.askinteger(title="Das ist der letzte Input, ich schwöre",
        prompt="Wie viele Klausuren gibt es pro Mappe",
        parent=application_window,
        initialvalue=8,
        minvalue=1,
        maxvalue=20)
    if klausuren_pro_mappe is None: return
    # Unitialize tkinter window
    application_window.destroy()
    # Start main app
    app = QApplication(sys.argv)
    ex = Kratzomat(
        KLAUSUREN_PRO_MAPPE= klausuren_pro_mappe,
        AUFGABEN= aufgaben_dict
        )
    sys.exit(app.exec()) 

class Kratzomat(QWidget):
    key_up = Qt.Key.Key_Up.value
    key_down = Qt.Key.Key_Down.value
    key_left = Qt.Key.Key_Left.value
    key_right = Qt.Key.Key_Right.value
    key_esc = Qt.Key.Key_Escape.value
    key_return = Qt.Key.Key_Return.value
    key_delete = Qt.Key.Key_Delete.value

    def __init__(self, KLAUSUREN_PRO_MAPPE: int = 8, AUFGABEN: dict = {"Kurzfragen": 15,"A7": 10,"A8": 10,"A9": 10}):
        super().__init__()
        self.KLAUSUREN_PRO_MAPPE = KLAUSUREN_PRO_MAPPE
        self.AUFGABEN = AUFGABEN
        self.AUFGABEN_PRO_KLASUR = len(AUFGABEN)
        self.PUNKTE_PRO_AUFGABE = list(AUFGABEN.values())
        self.PUNKTE_GESAMT = sum(self.PUNKTE_PRO_AUFGABE)
        self.PREFIX_SPALTEN = 1
        self.SUFFIX_SPALTEN = 1
        self.SUMME_SPALTEN = self.PUNKTE_GESAMT + self.PREFIX_SPALTEN + self.AUFGABEN_PRO_KLASUR + self.SUFFIX_SPALTEN
        # 2 Zeilen für Header: Aufgabentitel + Buchstaben bzw. SIGMA + Zeilensumme
        self.PREFIX_ZEILEN = 2
        self.SUFFIX_ZEILEN = 1
        self.SUMME_ZEILEN = self.PREFIX_ZEILEN + KLAUSUREN_PRO_MAPPE + self.SUFFIX_ZEILEN
        # Benötigte Matrizen und Vektoren definieren
        self.PUNKTE_SPALTEN = np.arange(0,self.KLAUSUREN_PRO_MAPPE) + self.PREFIX_ZEILEN
        self.positions = [(x, y) for x in range(self.SUMME_ZEILEN) for y in range(self.SUMME_SPALTEN)]  # Alle Positionen im GRID
        self.romans = range(self.PREFIX_ZEILEN, self.PREFIX_ZEILEN + KLAUSUREN_PRO_MAPPE) # Vektor mit Positionen für römische Zahlen
        self.aufgabenpos = self._calcHeaderPositions()
        self.PUNKTE_ZEILEN, self.BUCHSTABEN_ZEILEN, self.PUNKTE_ZEILEN_GETRENNT = self._calcPointColumns()
        self.AUFGABEN_SUMMEN_POSITION = self._calcAufgabenSumPositions()
        self.initUI()
        self.PUNKTE_MATRIX_MITWIDGETS, self.PUNKTE_MATRIX_MITPUNKTEN = self._initpunktematrix_widgets()       #   -> HIER WEITERMACHEN
        self.AUFGABEN_SUMMEN_MATRIX = self._calcAufgabenSumMatrix()
        self.ZEILENSUMMEN_WIDGET_VEKTOR = self._initZeilenSummenWidgetVektor()
        self.SPALTENSUMMEN_WIDGET_VEKTOR = self._initSpaltenSummenWidgetVektor()
        self.SUMMENSUMMEN_WIDGET = self._getLabelfromCoord(self.SUMME_ZEILEN-1,self.SUMME_SPALTEN-1)
        self._EinzelPunkteSumme()
        self._highlightPointSum()
        # Übersicht Koordinaten:
        # -> x entspricht SUMME_ZEILEN entspricht positions[1]
        # |
        # v
        # y entspricht SUMME_SPALTEN entspricht positions[0]
        self.CUR_ZEILE = 0
        self.CUR_SPALTE = 0
        self._highlightCurCell()

    def initUI(self):   
        self.grid = QGridLayout()  
        self.setLayout(self.grid)
        self._widgets_points = list()
        # Loop über GRID und beschrifte Felder
        for idx, position in enumerate(self.positions):
            # 1. Zeile Clear Button
            row_span = None
            col_span = None
            if position == (0, 0):
                # element = QPushButton("Clear")
                # element.clicked.connect(self._resetAllPoints)
                element = None                              # -> TEMPORÄRER FIX
            else:   # Alle anderen Instrumente sind QLabel's
                # Labels unterscheiden sich nur im Text:
                # X0,Y1: Mappe, damit roman Zahlen ersichtlich sind
                if position == (1,0):
                    text = "Klausur:"
                elif position == (self.SUMME_ZEILEN-1,self.SUMME_SPALTEN-1):
                    text = "SUMMISUM"
                # X0,Yend: Text für Spaltensumme
                elif position == (self.SUMME_ZEILEN-1,0): # -1 weil bei 0 gestartet wird
                    text = "Spalten-" + "\u03A3" + ":"
                # Xend,Y0: Text für Zeilensumme
                elif position == (0,self.SUMME_SPALTEN-1):
                    text = "Zeilen-" + "\u03A3" + ":"
                    row_span = 2
                    col_span = 1
                elif position == (1,self.SUMME_SPALTEN-1):
                    text = None
                # Aufgaben-Überschriften
                elif position[0] == 0 and position[1] in self.aufgabenpos[:,1]:
                    idx = np.where(self.aufgabenpos[:,1] == position[1])
                    idx = idx[0][0]
                    text = list(self.AUFGABEN.keys())[idx]
                    row_span = 1
                    col_span = self.aufgabenpos[idx,3]
                # Einzel Summen-Aufgaben
                elif position[0] == (self.SUMME_ZEILEN-1) and position[1] in self.aufgabenpos[:,1]:
                    idx = np.where(self.aufgabenpos[:,1] == position[1])
                    idx = idx[0][0]
                    text = "AUFGABEN-" + "\u03A3"
                    row_span = 1
                    col_span = self.aufgabenpos[idx,3]
                # Summenzeichen für Aufgaben hinzufügen
                elif position[0] == 1 and position[1] in self.AUFGABEN_SUMMEN_POSITION:
                    text = "\u03A3"
                # Übrig gebliebene Zeilen entfernen
                elif position[0] == 0:
                    text = None
                elif position[0] == self.SUMME_ZEILEN-1:
                    text = None
                # X0,Y-Range: Roman Zahlen für Mappen
                elif position[1] == 0 and position[0] in self.romans:
                    text = self._to_roman_numeral(position[0]-1)
                # Buchstaben Übersicht
                elif position[0] == 1 and position[1] in self.PUNKTE_ZEILEN:
                    text = self.BUCHSTABEN_ZEILEN[np.where(self.PUNKTE_ZEILEN == position[1])]
                    text = text[0]
                # Punkte-Felder
                elif position[1] in self.PUNKTE_ZEILEN and position[0] in self.romans:
                    text = "-"
                    self._widgets_points.append(position)
                else:
                    text = f"F{idx},X{position[0]},Y{position[1]}"
                if text is not None:
                    element = QLabel(text)
                else:
                    element = None
            if element is not None:
                if (col_span is None) and (row_span is None):
                    self.grid.addWidget(element, *position)
                else:
                    #align = Qt.AlignmentFlag.AlignCenter
                    #align = Qt.AlignmentFlag.AlignRight
                    #align = Qt.AlignmentFlag.AlignLeft
                    align = Qt.AlignmentFlag.AlignVCenter
                    self.grid.addWidget(element, *position,row_span,col_span,align)
        self.move(300, 150)
        self.setWindowTitle('Kratztool: ESC reset all (dauert ein bisschen, pls chill bre), DEL reset single entry, UP 1, DOWN 0, LEFT and RIGHT to navigate')  
        self.show()

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        for widget in self.children():
            if isinstance(widget,QLabel):
                pass
                #print(f"Widget-Text: {widget.text()} at position x{widget.x()} - y{widget.y()}")
            elif isinstance(widget,QGridLayout):
                pass
        if a0.key() == self.key_up:
            # print("Key up pressed")
            self.setPoint(1)
            self._EinzelPunkteSumme()
            self.step(1)
        elif a0.key() == self.key_down:
            self.setPoint()
            self._EinzelPunkteSumme()
            self.step(1)
            # print("Key down pressed")
        elif a0.key() == self.key_left:
            # print("Key left pressed")
            self.step(-1)
        elif a0.key() == self.key_right:
            # print("Key right pressed")
            self.step(1)
        elif a0.key() == self.key_esc:
            # print("Key escape pressed")
            self._resetAllPoints()
        elif a0.key() == self.key_return:
            pass
            # print("Key return pressed")
        elif a0.key() == self.key_delete:
            self._resetSinglePoint(self.CUR_ZEILE,self.CUR_SPALTE)
        else:           
            print(f"Unknown key pressed, ID: {a0.key()}")
    

    def _to_roman_numeral(self,value):
        roman_map = {                                   # 1
            1: "I", 5: "V",
            10: "X", 50: "L", 
            100: "C", 500: "D",
            1000: "M",
        }
        result = ""
        remainder = value
        for i in sorted(roman_map.keys(), reverse=True):# 2
            if remainder > 0:
                multiplier = i
                roman_digit = roman_map[i]

                times = remainder // multiplier         # 3
                remainder = remainder % multiplier      # 4
                result += roman_digit * times           # 4
        return result
    
    def _calcHeaderPositions(self) -> np.array:
        PUNKTE_PRO_AUFGABE_INKL_SIGMA = [x+1 for x in self.PUNKTE_PRO_AUFGABE] # Spaltenbreite muss um jeweils 1 erhöht werden damit Platz für SIGMA Zeichen ist
        aufgabenpos = np.zeros((self.AUFGABEN_PRO_KLASUR,4),int)
        for idx, val in enumerate(self.PUNKTE_PRO_AUFGABE):
            aufgabenpos[idx][1] = self.PREFIX_SPALTEN+sum(PUNKTE_PRO_AUFGABE_INKL_SIGMA[:idx])
            aufgabenpos[idx][3] = val+1
        return aufgabenpos
    
    def _calcAufgabenSumPositions(self) -> np.array:
        size = len(self.PUNKTE_PRO_AUFGABE)
        aufgabensum = np.zeros([1,size],int)
        for idx in range(size):
            aufgabensum[0][idx] = self.aufgabenpos[:,1][idx] + self.aufgabenpos[:,3][idx] - 1
        #print(f"AufgabenSummenPosition: {aufgabensum}")
        return aufgabensum

    def _calcPointColumns(self) -> np.array:
        size = sum(self.PUNKTE_PRO_AUFGABE)
        point_col = np.zeros((1,size),int)
        point_letters = np.zeros((1,size),str)
        point_col_seperated = np.zeros((1,len(self.PUNKTE_PRO_AUFGABE)),dtype=object)
        for r_idx,row in enumerate(zip(self.aufgabenpos,self.PUNKTE_PRO_AUFGABE)):
            for c_idx in range(row[1]):
                index = row[0][1] - r_idx + c_idx - 1
                point_col[0][index] = row[0][1] + c_idx
                point_letters[0][index] = chr(65+c_idx)
            point_col_seperated[0][r_idx] = np.arange(0,self.PUNKTE_PRO_AUFGABE[r_idx]-1)+self.aufgabenpos[r_idx][1]
        return point_col, point_letters, point_col_seperated
    
    def _calcAufgabenSumMatrix(self) -> np.empty:
        sum_mat = np.zeros((self.KLAUSUREN_PRO_MAPPE,self.AUFGABEN_PRO_KLASUR),dtype= QLabel)
        for pos,widget in np.ndenumerate(sum_mat):
            sum_mat[pos] = self._getLabelfromCoord(self.PUNKTE_SPALTEN[pos[0]],self.AUFGABEN_SUMMEN_POSITION[0][pos[1]])
        return sum_mat

    def step(self,step: int) -> None:
        # Überhang berechnen
        next_c =  self.CUR_SPALTE + step
        # Positiver Schritt
        if next_c >= self.PUNKTE_GESAMT and self.CUR_ZEILE < self.KLAUSUREN_PRO_MAPPE-1 and step > 0:
            self.CUR_SPALTE = next_c - self.PUNKTE_GESAMT
            self.CUR_ZEILE += 1
        elif next_c >= 0 and next_c < self.PUNKTE_GESAMT and step > 0:
            self.CUR_SPALTE += step
        elif next_c < 0 and self.CUR_ZEILE > 0 and step < 0:
            self.CUR_ZEILE -= 1
            self.CUR_SPALTE = next_c + self.PUNKTE_GESAMT
        elif next_c >= 0 and step < 0:
            self.CUR_SPALTE += step
        else:
            print("Nichts verschoben")
        self._highlightCurCell()
        # print(f"CUR_SPALTE: {self.CUR_SPALTE}, CUR_ZEILE: {self.CUR_ZEILE}")
        
    def _EinzelPunkteSumme(self) -> None:
        for pos, widget in np.ndenumerate(self.PUNKTE_MATRIX_MITWIDGETS):
            widget_text = str(widget.text())
            # Fill PUNKTE_MATRIX_MITPUNKTEN
            if widget_text.isdigit():
                self.PUNKTE_MATRIX_MITPUNKTEN[pos] = int(widget_text)
        # Berechne Summen
        for pos, widget in np.ndenumerate(self.AUFGABEN_SUMMEN_MATRIX):
            # Loop over einzelne Aufgaben
            teilaufgabe_punkte_start = self.aufgabenpos[pos[1]][1]-self.PREFIX_SPALTEN-pos[1]
            teilaufgabe_punkte_ende = self.aufgabenpos[pos[1]][1] + self.aufgabenpos[pos[1]][3] - self.PREFIX_SPALTEN-1-pos[1]
            # print(f"pos: {pos},anfang: {teilaufgabe_punkte_start}, ende: {teilaufgabe_punkte_ende}")
            teilaufgabe_punkte = sum(self.PUNKTE_MATRIX_MITPUNKTEN[pos[0]][teilaufgabe_punkte_start:teilaufgabe_punkte_ende])
            # Prüfen, ob alle Punkte pro Teilaufgabe vergeben wurden
            einzelpunkte_widgets = self.PUNKTE_MATRIX_MITWIDGETS[pos[0]][teilaufgabe_punkte_start:teilaufgabe_punkte_ende]
            # if '-' in [x.text() for x in einzelpunkte_widgets]:
            # if False:
            #     text = '-'
            # else:
            #     text = f"{teilaufgabe_punkte}"
            text = f"{teilaufgabe_punkte}"
            widget.setText(text)
        self._GesamtSummen()

    def _initZeilenSummenWidgetVektor(self) -> np.array:
        vektor = np.empty([1,self.KLAUSUREN_PRO_MAPPE],dtype=QLabel)
        for idx in range(self.KLAUSUREN_PRO_MAPPE):
            vektor[0][idx] = self._getLabelfromCoord(self.PREFIX_ZEILEN+idx,self.SUMME_SPALTEN-1)
        return vektor

    def _initSpaltenSummenWidgetVektor(self) -> np.array:
        vektor = np.empty([1,self.AUFGABEN_PRO_KLASUR],dtype=QLabel)
        for idx in range(self.AUFGABEN_PRO_KLASUR):
            vektor[0][idx] = self._getLabelfromCoord(self.SUMME_ZEILEN-1,self.aufgabenpos[:,1][idx])
        return vektor

    def _GesamtSummen(self) -> None:
        # Spalten-Summen
        sum_col = 0
        for pos, widget in np.ndenumerate(self.SPALTENSUMMEN_WIDGET_VEKTOR):
            values = [elem.text() for elem in self.AUFGABEN_SUMMEN_MATRIX[:,pos[1]]]
            if all([item == '-' for item in values]):
                text = "AUFGABEN-" + "\u03A3:"
            else:
                sum_cur_col = sum([int(digit) for digit in values if digit.isdigit()])
                sum_col += sum_cur_col
                text = f"AUFGABEN-\u03A3: {sum_cur_col}"
            widget.setText(text)
        # Zeilen-Summen:
        sum_row = 0
        for pos, widget in np.ndenumerate(self.ZEILENSUMMEN_WIDGET_VEKTOR):
            values = [elem.text() for elem in self.AUFGABEN_SUMMEN_MATRIX[pos[1],:]]
            if all([item == '-' for item in values]):
                text = "AUFGABEN-" + "\u03A3:"
            else:
                sum_cur_row = sum([int(digit) for digit in values if digit.isdigit()])
                sum_row += sum_cur_row
                text = f"AUFGABEN-\u03A3: {sum_cur_row}"
            widget.setText(text)
        # Summen-Summe
        self.SUMMENSUMMEN_WIDGET.setText(f"{sum_col} - {sum_row}")
        if sum_row == sum_col and sum_col != 0:
            self.SUMMENSUMMEN_WIDGET.setStyleSheet("background-color: green; color: white")
        else:
            self.SUMMENSUMMEN_WIDGET.setStyleSheet("background-color: none")
            
    
    def _initpunktematrix_widgets(self) -> np.empty:
        punktematrix_widgets = np.empty([self.KLAUSUREN_PRO_MAPPE,self.PUNKTE_GESAMT],dtype=QLabel)
        punktematrix_punkte = np.zeros([self.KLAUSUREN_PRO_MAPPE,self.PUNKTE_GESAMT],dtype=int)
        for i_x in range(self.PUNKTE_GESAMT):
            for i_y in range(self.KLAUSUREN_PRO_MAPPE):
                # Get corresponding rows and colums of point fields
                i_col = self.PUNKTE_ZEILEN[0][i_x]
                i_row = self.PUNKTE_SPALTEN[i_y]
                #print(f"({self.PUNKTE_ZEILEN[0][i_y]},{i_x})")
                punktematrix_widgets[i_y][i_x] = self._getLabelfromCoord(i_row,i_col)
        return punktematrix_widgets, punktematrix_punkte

    def setPoint(self,point: int = 0) -> None:
        widget = self.PUNKTE_MATRIX_MITWIDGETS[self.CUR_ZEILE][self.CUR_SPALTE]
        widget.setText(str(point))

    def _getLabelfromCoord(self,row,col) -> QLabel:
        lay = self.layout()
        widgets = (lay.itemAt(i).widget() for i in range(lay.count()))
        for widget in widgets:
            if isinstance(widget, QLabel):
                row_w, col_w, cols_w, rows_w = lay.getItemPosition(lay.indexOf(widget))
                if row_w == row and col_w == col:
                    return widget
        return None

    def _resetSinglePoint(self,row: int, col: int) -> None:
        self.PUNKTE_MATRIX_MITWIDGETS[row][col].setText("-")
        self._EinzelPunkteSumme()

    def _resetAllPoints(self) -> None:
        for idx, widget in np.ndenumerate(self.PUNKTE_MATRIX_MITWIDGETS):
            widget.setText('-')
            self.CUR_SPALTE = 0
            self.CUR_ZEILE = 0
            self.PUNKTE_MATRIX_MITPUNKTEN[idx[0]][idx[1]] = 0
            self._highlightCurCell()
            self._EinzelPunkteSumme()
        
    
    def _highlightCurCell(self):
        if darkdetect.isDark():
            for index, widget in np.ndenumerate(self.PUNKTE_MATRIX_MITWIDGETS):
                if index[0] == self.CUR_ZEILE and index[1] == self.CUR_SPALTE:
                    widget.setStyleSheet("background-color: green")
                elif index[0] == self.CUR_ZEILE or index[1] == self.CUR_SPALTE:
                    widget.setStyleSheet("background-color: darkkhaki")
                else:
                    widget.setStyleSheet("background-color: none")
        else:
            for index, widget in np.ndenumerate(self.PUNKTE_MATRIX_MITWIDGETS):
                if index[0] == self.CUR_ZEILE and index[1] == self.CUR_SPALTE:
                    widget.setStyleSheet("background-color: lightgreen")
                elif index[0] == self.CUR_ZEILE or index[1] == self.CUR_SPALTE:
                    widget.setStyleSheet("background-color: yellow")
                else:
                    widget.setStyleSheet("background-color: none")
            

    def _highlightPointSum(self) -> None:
        if darkdetect.isDark():
            for index, widget in np.ndenumerate(self.AUFGABEN_SUMMEN_MATRIX):
                widget.setStyleSheet("background-color: purple; color: white")
        else:
             for index, widget in np.ndenumerate(self.AUFGABEN_SUMMEN_MATRIX):
                widget.setStyleSheet("background-color: magenta; color: white")


if __name__ == '__main__':
    init_app()