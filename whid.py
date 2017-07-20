#!/usr/bin/env python

import copy
import json
import os
import sys
import time

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtCore

base_entry = {'text': '',
              'start_date': None,
              'complete_date': None,
              'children': [],
              'delete': False,
              }
# How many elements of struct_time to consider when comparing dates
date_resolution = 3
# One hour
process_interval = 3600000

# Test values
#date_resolution = 5
#process_interval = 3000

class WHIDForm(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(WHIDForm, self).__init__()
        self.createUI()
        self.show()

        # These structures are persistent
        self.root_entry = copy.deepcopy(base_entry)
        self.days = {}
        self.completed = {}
        self.load()

        # These are not
        self.ignoreInputChange = False
        self.updateHistory = True
        self.processData()
        self.populateDay(time.time())
        self.processTimer = QtCore.QTimer()
        self.processTimer.start(process_interval)
        self.processTimer.timeout.connect(self.processData)

    def createUI(self):
        self.resize(1000, 600)
        self.setWindowTitle("What Have I Done?!")

        self.mainLayout = QtWidgets.QHBoxLayout(self)

        self.inputLayout = QtWidgets.QVBoxLayout()
        self.inputLayout.addWidget(QtWidgets.QLabel('In-Progress'))
        self.mainInput = QtWidgets.QTextEdit()
        self.mainInput.textChanged.connect(self.parseText)
        self.inputLayout.addWidget(self.mainInput)
        self.mainLayout.addLayout(self.inputLayout)

        self.dayLayout = QtWidgets.QVBoxLayout()
        self.dayLayout.addWidget(QtWidgets.QLabel('Today'))
        self.todayText = QtWidgets.QTextEdit()
        self.todayText.setReadOnly(True)
        self.dayLayout.addWidget(self.todayText)
        self.dayLayout.addWidget(QtWidgets.QLabel('History'))
        self.historyText = QtWidgets.QTextEdit()
        self.historyText.setReadOnly(True)
        self.dayLayout.addWidget(self.historyText)
        self.allButton = QtWidgets.QPushButton('All Days')
        self.allButton.pressed.connect(self.allPressed)
        self.dayLayout.addWidget(self.allButton)
        self.mainLayout.addLayout(self.dayLayout)

        self.allDialog = QtWidgets.QDialog(self)
        self.allDialog.setModal(False)
        self.allDialog.resize(600, 600)
        self.allDialog.setWindowTitle('All Days')
        self.allLayout = QtWidgets.QVBoxLayout(self.allDialog)
        self.allText = QtWidgets.QTextEdit()
        self.allLayout.addWidget(self.allText)

    def parseText(self):
        if self.ignoreInputChange:
            self.ignoreInputChange = False
            return
        self.processTimer.stop()
        now = time.time()
        text = self.mainInput.toPlainText()
        root = copy.deepcopy(base_entry)
        root['text'] = '__root__'
        parents = [root]
        previous = None
        for line in text.splitlines():
            new_entry = copy.deepcopy(base_entry)
            new_entry['text'] = line.lstrip('-')
            if new_entry['text'] + '***' in self.completed:
                # The user added a new entry with the same name as a previously
                # completed one.  Remove the old completion time.
                self.completed.pop(new_entry['text'] + '***')
            if new_entry['text'].endswith('***'):
                if new_entry['text'] in self.completed:
                    new_entry['complete_date'] = self.completed[new_entry['text']]
                else:
                    new_entry['complete_date'] = now
                    self.completed[new_entry['text']] = new_entry['complete_date']
            new_level = len(line) - len(new_entry['text'])
            if new_level > len(parents) - 1:
                parents.append(previous)
            if new_level < len(parents) - 1:
                parents.pop()
            parents[-1]['children'].append(new_entry)
            previous = new_entry
        self.root_entry = root
        self.populateDay(now)
        self.processData()
        self.processTimer.start(process_interval)

    def processData(self):
        now = time.localtime()
        self.processEntry(self.root_entry, now)
        self.cleanupEntries(self.root_entry)
        self.updateInput()
        self.populateDay(time.time())
        self.save()

    def processEntry(self, entry, now):
        if entry['complete_date']:
            local_date = time.localtime(entry['complete_date'])
            # Compare year, month, and day.  If the entry was completed on a
            # previous day then we can delete it.
            if local_date[0:date_resolution] != now[0:date_resolution]:
                entry['delete'] = True
                self.updateHistory = True

        for e in entry['children']:
            self.processEntry(e, now)

    def cleanupEntries(self, entry):
        entry['children'] = [e for e in entry['children'] if not e['delete']]
        for e in entry['children']:
            self.cleanupEntries(e)

    def updateInput(self):
        new_text = entryToText(self.root_entry).rstrip()
        # We don't care about trailing whitespace differences
        current = self.mainInput.toPlainText().rstrip()
        plain_text = new_text
        plain_text = plain_text.replace('<b>', '')
        plain_text = plain_text.replace('</b>', '')
        plain_text = plain_text.replace('<br>', '\n')
        if plain_text.rstrip() != current:
            self.ignoreInputChange = True
            self.mainInput.setPlainText(plain_text)

    def populateDay(self, now):
        # Called each time the input changes
        local_date = time.localtime(now)
        day_key = toDayKey(local_date)
        self.days.setdefault(day_key, [])
        self.days[day_key] = copy.deepcopy(self.root_entry)
        # Remove any entries that are not complete
        filterComplete(self.days[day_key])
        self.todayText.setHtml(entryToText(self.days[day_key]))
        if len(self.days) > 0 and self.updateHistory:
            text = self.getHistoryText(1)
            self.historyText.setHtml(text)
            self.updateHistory = False

    def getHistoryText(self, skip=0):
        text = ''
        for date, entry in reversed(sorted(self.days.items())):
            print skip, date, entry
            if entry['children'] and not skip:
                text += '<h3>%s</h3>' % date
                text += entryToText(entry)
            skip = max(skip - 1, 0)
        print
        return text

    def save(self):
        output = {}
        output['root_entry'] = self.root_entry
        output['days'] = self.days
        output['completed'] = self.completed
        with open(os.path.expanduser('~/.whid.json'), 'w') as f:
            f.write(json.dumps(output))

    def load(self):
        if not os.path.isfile(os.path.expanduser('~/.whid.json')):
            return
        with open(os.path.expanduser('~/.whid.json')) as f:
            data = json.loads(f.read())
        self.root_entry = data['root_entry']
        self.days = data['days']
        self.completed = data['completed']
        self.updateInput()

    def allPressed(self):
        self.allText.setHtml(self.getHistoryText())
        self.allDialog.show()


def entryToText(entry, level=-1):
    text = ''
    if entry['text'] != '__root__':
        text = '-' * level + entry['text']
        if entry['text'].endswith('***'):
            text = '<b>' + text + '</b>'
        text += '<br>'
    for e in entry['children']:
        text += entryToText(e, level + 1)
    return text

def filterComplete(entry):
    entry['children'] = [e for e in entry['children'] if hasComplete(e)]
    for e in entry['children']:
        filterComplete(e)

def hasComplete(entry):
    if entry['complete_date']:
        return True
    return any([hasComplete(e) for e in entry['children']])

def toDayKey(t):
    day_list = [str(i).zfill(2) for i in t[0:date_resolution]]
    day_key = '-'.join(day_list)
    return day_key


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    form = WHIDForm()

    sys.exit(app.exec_())
