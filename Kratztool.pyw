"""
Python 3 required

Install required packages:
$pip install -r requirements.txt$

Create requirements.txt file if new packages have been used (ONLY WHEN USING VIRTUAL ENVIRONMENT):
$pip freeze > requirements.txt$

Command to pack tool to single .exe file
$python -m nuitka --remove-output --enable-plugin=pyqt6 --enable-plugin=tk-inter --windows-console-mode=disable --onefile .\Kratztool.pyw$

ToDo:
-Alle int's die Spalten oder Zeilen definieren in Config schreiben und eindeutige Namen geben, wofür die jeweiligen Indizes stehen
-Functionen die nicht Klassenspezifisch sind herauslösen und in ressources.functions schieben

"""
import sys
import numpy as np
from PySide6 import QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QGridLayout, QLabel
import tkinter as tk
from tkinter import simpledialog, messagebox
import ast
import darkdetect
import logging
from typing import Optional
# Import custom packages
import ressources.config as cfg
import ressources.functions as fnc

# Initialize logger
log = logging.getLogger(__name__)


def init_app() -> None:
    # Initialize Tkinter window
    application_window = tk.Tk()
    application_window.withdraw()
    application_window.iconbitmap(default=cfg.ICON_FULLPATH)
    # Get valid User Input or cancel
    while True:
        aufgaben = simpledialog.askstring(title=cfg.ASK_AUFGABEN_TITLE,
            prompt=cfg.ASK_AUFGABEN_AUFFORDERUNG,
            parent=application_window,
            initialvalue=cfg.STANDARD_AUFGABEN_STR
            )
        if aufgaben is None: return
        try:
            aufgaben_dict = ast.literal_eval(f"{{{aufgaben}}}")
        except SyntaxError:
            messagebox.showerror('ALARM', cfg.ASK_AUFGABEN_DICT_ERROR)
            continue
        if not all([(item > 0 and item < 27) for item in aufgaben_dict.values()]):
            messagebox.showerror('ALARM', cfg.ASK_AUFGABEN_PUNKTZAHL_ERROR)
            continue
        break
    klausuren_pro_mappe = simpledialog.askinteger(title=cfg.ASK_ANZAHLKLAUSUREN_TITLE,
        prompt=cfg.ASK_ANZAHLKLAUSUREN_AUFFORDERUNG,
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
    def __init__(self, KLAUSUREN_PRO_MAPPE: int = 8, AUFGABEN: dict = cfg.STANDARD_AUFGABEN_DICT):
        """Initializer für das eigentliche Tool.

        Args:
            KLAUSUREN_PRO_MAPPE (int, optional): Anzahl der Klausuren pro Mappe. Defaults to 8.
            AUFGABEN (dict, optional): Aufteilung der Punkteverteilung pro Aufgabe: {str("AUFGABE"):int(ANZAHL_PUNKTE),...}. Defaults to cfg.STANDARD_AUFGABEN_DICT.
        """
        super().__init__()
        self.KLAUSUREN_PRO_MAPPE = KLAUSUREN_PRO_MAPPE
        self.AUFGABEN = AUFGABEN
        self.AUFGABEN_PRO_KLASUR = len(AUFGABEN)
        self.PUNKTE_PRO_AUFGABE = list(AUFGABEN.values())
        self.PUNKTE_GESAMT = sum(self.PUNKTE_PRO_AUFGABE)
        self.reset_active = False
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
        self.PUNKTE_MATRIX_MITWIDGETS, self.PUNKTE_MATRIX_MITPUNKTEN = self._initpunktematrix_widgets()
        self.AUFGABEN_SUMMEN_MATRIX = self._calcAufgabenSumMatrix()
        self.ZEILENSUMMEN_WIDGET_VEKTOR = self._initZeilenSummenWidgetVektor()
        self.SPALTENSUMMEN_WIDGET_VEKTOR = self._initSpaltenSummenWidgetVektor()
        self.SUMMENSUMMEN_WIDGET = self._getLabelfromCoord(self.SUMME_ZEILEN-1,self.SUMME_SPALTEN-1)
        self._EinzelPunkteSumme()
        self._highlightPointSum()
        self.last_key = None
        # Übersicht Koordinaten:
        # -> x entspricht SUMME_ZEILEN entspricht positions[1]
        # |
        # v
        # y entspricht SUMME_SPALTEN entspricht positions[0]
        self.CUR_ZEILE = 0
        self.CUR_SPALTE = 0
        self._highlightCurCell()


    def initUI(self, alignment_header: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignVCenter):
        """Füllt alle Widgets mit dem Starttext

        Args:
            alignment_header (Qt.AlignmentFlag, optional): Alignment des Textes der Header Widgets (GLAUBE ICH, MUSS NOCH BESTÖTIGT WERDEN). Defaults to Qt.AlignmentFlag.AlignVCenter.
        """
        self.grid = QGridLayout()  
        self.setLayout(self.grid)
        self._widgets_points = list()
        # Loop über GRID und beschrifte Felder
        for idx, position in enumerate(self.positions):
            # 1. Zeile Clear Button
            row_span = None
            col_span = None
            if position == (0, 0):
                element = None
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
                    text = fnc._to_roman_numeral(position[0]-1)
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
                    self.grid.addWidget(element, *position,row_span,col_span,alignment_header)
        self.move(300, 150)
        self.setWindowTitle(cfg.TOOL_TITLE)
        self.setWindowIcon(QtGui.QIcon(cfg.ICON_FULLPATH))
        self.show()


    def keyPressEvent(self, a0: QtGui.QKeyEvent, debug_mode: Optional[bool] = False) -> None:
        """Funktion um auf Tastatur Input zu reagieren

        Args:
            a0 (QtGui.QKeyEvent): Gedrückte Taste.
            debug_mode (Optional[bool]): Gibt die aktuellen Texte aller Widgets in der Konsole aus. Defaults to False.
        """
        if debug_mode:
            for widget in self.children():
                if isinstance(widget,QLabel):
                    log.debug(f"Widget-Text: {widget.text()} at position x{widget.x()} - y{widget.y()}")
                elif isinstance(widget,QGridLayout):
                    pass
        if a0.key() == Qt.Key.Key_Up.value:
            self.setPoint(1)
            self._EinzelPunkteSumme()
            self.step(1)
        elif a0.key() == Qt.Key.Key_Down.value:
            self.setPoint()
            self._EinzelPunkteSumme()
            self.step(1)
        elif a0.key() == Qt.Key.Key_Left.value:
            self.step(-1)
        elif a0.key() == Qt.Key.Key_Right.value:
            self.step(1)
        elif a0.key() == Qt.Key.Key_Escape.value:
            if a0.key() != self.last_key: self._resetAllPoints()
        elif a0.key() == Qt.Key.Key_Return.value:
            pass
        elif a0.key() == Qt.Key.Key_Delete.value:
            self._resetSinglePoint(self.CUR_ZEILE,self.CUR_SPALTE)
        else:           
            log.warning(f"Unknown key pressed, ID: {a0.key()}, name {a0.text()}")
        self.last_key = a0.key()
    

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
        log.debug(f"AufgabenSummenPosition: {aufgabensum}")
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
            log.debug("Nichts verschoben")
        self._highlightCurCell()
        log.debug(f"CUR_SPALTE: {self.CUR_SPALTE}, CUR_ZEILE: {self.CUR_ZEILE}")
        
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
            log.debug(f"pos: {pos},anfang: {teilaufgabe_punkte_start}, ende: {teilaufgabe_punkte_ende}")
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
                log.debug(f"({self.PUNKTE_ZEILEN[0][i_y]},{i_x})")
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
        """Setzt alle Punkte auf 0 und wählt erstes Instrument aus
        """
        self.reset_active = True
        for idx, widget in np.ndenumerate(self.PUNKTE_MATRIX_MITWIDGETS):
            widget.setText('-')
            self.CUR_SPALTE = 0
            self.CUR_ZEILE = 0
            self.PUNKTE_MATRIX_MITPUNKTEN[idx[0]][idx[1]] = 0
        self._highlightCurCell()
        self._EinzelPunkteSumme()
        self.reset_active = False
        
    
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
    fnc.start_log()
    init_app()