from PyQt5.QtCore import QTimer, Qt
import sqlite3
import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QInputDialog, QTableWidget,\
    QTableWidgetItem, QLineEdit
from random import choice

class KeyboardTrainer(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('TrainerLobby.ui', self)
        self.CurrentMode = 'По словам'
        self.Tries = 5
        self.LettersCount = 3
        self.difficulty = 100
        self.setFixedSize(450, 450)
        self.DifficultyChangeBtn.clicked.connect(self.DifficultyChange)
        self.ChangeDescription(self.CurrentMode)
        self.ModeButtonsGroup.buttonClicked.connect(self.ModeChange)
        self.ChangeTryAmount.clicked.connect(self.ChangeTries)
        self.StartTrainButton.clicked.connect(self.StartTraining)
        self.ShowRecordsBtn.clicked.connect(self.ShowRecords)
        self.ChangeLettersCountBtn.clicked.connect(self.ChangeLettersCount)

    def ChangeLettersCount(self):
        lettercount, okBtnPressed = QInputDialog.getInt(self, "Введите число",
                                                        "Введите количество букв в проверке 'По буквам'",
                                                        3, 1, 10, 1)
        if okBtnPressed:
            self.LettersCount = lettercount
            self.ChangeDescription(self.CurrentMode)

    def ShowRecords(self):
        self.RecordsWindow = Records(self)
        self.RecordsWindow.show()

    def DifficultyChange(self):
        percents, okBtnPressed = QInputDialog.getInt(self, "Введите число",
                                                     "Введите % сложности",
                                                     100, 50, 150, 1)
        if okBtnPressed:
            self.difficulty = percents
            self.ChangeDescription(self.CurrentMode)

    def ChangeTries(self):
        TryAmount, okBtnPressed = QInputDialog.getInt(self, "Введите число",
                                                      "Введите количество попыток",
                                                      5, 1, 10, 1)
        if okBtnPressed:
            self.Tries = TryAmount
            self.ChangeDescription(self.CurrentMode)

    def ModeChange(self, button):
        self.CurrentMode = button.text()
        self.ChangeDescription(self.CurrentMode)


    def ChangeDescription(self, descr):
        con = sqlite3.connect('description.db')
        cur = con.cursor()
        result = cur.execute("""SELECT Description FROM ModesDescription 
                WHERE ModeName like ?""", (descr,)).fetchall()
        for element in result:
            if self.CurrentMode != 'По буквам':
                self.ModeDescription.setText(str(element[0]) +
                                             '\nКоличество попыток: {}'.format(self.Tries) +
                                             '\nПроцент сложности: {}%'.format(self.difficulty))
            else:
                self.ModeDescription.setText(str(element[0]) +
                                             '\nКоличество попыток: {}'.format(self.Tries) +
                                             '\nПроцент сложности: {}%'.format(self.difficulty) +
                                             '\nКоличество букв: {}'.format(self.LettersCount))
        con.close()

    def StartTraining(self):
        self.TrainingWindow = Training(self, self.CurrentMode, self.Tries, self.difficulty, self.LettersCount)
        self.TrainingWindow.show()


class Records(QWidget):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi('records.ui', self)
        self.CurrentMode = 'По словам'
        self.setFixedSize(450, 400)
        self.ChangeModeButton.clicked.connect(self.ChangeMode)
        self.update_everything()

    def ChangeMode(self):
        ChosenMode, okBtnPressed = QInputDialog.getItem(self, "Введите число",
                                                        "Введите количество попыток",
                                                        ('По буквам', 'По словам', 'По предложениям'),
                                                        1, False)
        if okBtnPressed:
            self.CurrentMode = ChosenMode
            self.update_everything()

    def update_everything(self):
        self.CurrentModeLabel.setText('Выбранный режим: {}'.format(self.CurrentMode))
        con = sqlite3.connect("records.db")
        result = con.execute("""SELECT * FROM records WHERE mode = ? ORDER BY -record""", (self.CurrentMode,))
        self.RecordTable.setRowCount(0)
        for row_number, row_data in enumerate(result):
            if row_number < 10:
                self.RecordTable.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    self.RecordTable.setItem(row_number, column_number, QTableWidgetItem(str(data)))
        con.close()


class Training(QWidget):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi('training.ui', self)
        self.letter_count = args[-1]
        self.difficulty = args[-2] / 100
        self.ModeOn = args[-4]
        self.Tries = args[-3]
        self.ZeroTries = self.Tries
        self.points = 0
        self.setFixedSize(450, 400)
        self.LabelTries.setText(str(self.Tries))
        self.LabelPoints.setText(str(self.points))
        self.Pause = False
        self.WriteText = ''
        if self.ModeOn == 'По словам':
            con = sqlite3.connect("wordlist.db")
            cur = con.cursor()
            self.result = list(cur.execute("""SELECT * FROM WordModeDictionary"""))
            con.close()
        if self.ModeOn == 'По предложениям':
            con = sqlite3.connect("wordlist.db")
            cur = con.cursor()
            self.result = list(cur.execute("""SELECT * FROM SentenceModeDictionary"""))
            con.close()
        self.new_word()

    def new_word(self):
        if self.ModeOn != 'По буквам':
            self.check, self.Neededtime = choice(self.result)
        else:
            letters = 'йцукенгшщзхъфывапролджэячсмитьбюё'
            word = ''
            for _ in range(self.letter_count):
                word += choice(letters)
            self.check = word
            self.Neededtime = len(word) + 1
        self.Neededtime = self.Neededtime * (2 - self.difficulty) // 1
        self.ZeroTime = self.Neededtime
        self.LabelTime.setText(str(int(self.Neededtime)))
        self.Check.setText(str(self.check))
        if self.Tries != 0:
            self.timerstart()
        if self.Tries == 0:
            con = sqlite3.connect('records.db')
            cur = con.cursor()
            cur.execute("""INSERT INTO records(record, mode, tries, difficulty) VALUES(?, ?, ?, ?)""",
                        (self.points, self.ModeOn, self.ZeroTries,
                         (str(int(self.difficulty * 100 // 1)) + '%'))).fetchall()
            con.commit()
            self.Write.setReadOnly(True)

    def timerstart(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.ontime)
        self.timer.start(1000)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.Pause is False:
                self.timer.stop()
                self.Pause = True
                self.Write.setReadOnly(True)
            else:
                self.Pause = False
                self.timer.start(1000)
                self.Write.setReadOnly(False)


    def ontime(self):
        if self.Tries > 0 and self.Pause is False:
            self.Neededtime -= 1
            if self.Write.text() == self.check:
                self.Write.setText('')
                self.points += (self.difficulty * (len(self.check)
                                                    * 4 / (self.ZeroTime - self.Neededtime))) // 1
                self.LabelPoints.setText(str(int(self.points)))
                self.timer.stop()
                self.new_word()
            elif self.Neededtime == 0 and self.Write.text() != self.check:
                self.Tries -= 1
                self.Write.setText('')
                self.LabelTries.setText(str(self.Tries))
                self.timer.stop()
                self.new_word()
            self.LabelTime.setText(str(int(self.Neededtime)))


app = QApplication(sys.argv)
ex = KeyboardTrainer()
ex.show()
sys.exit(app.exec_())