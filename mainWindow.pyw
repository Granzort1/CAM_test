import sys
# import numpy as np
# import sqlite3
from time import sleep

from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import q_SearchJuso as sj
# import calculate_grid_move as gm
# import clsProcessingGISDB as pg
# import processingGISDB as pg
# import processingMetDB as pm

from runoffWindow2 import SecondWindow

class ThreadClass(QtCore.QThread): 

    def __init__(self, parent = None): 
        super(ThreadClass,self).__init__(parent)

    def run(self): 
        print('Thread start')

class Window(QWidget):
    
    def __init__(self):
        self.threadclass = ThreadClass()
        # QWidget의 __init__() 메서드 호출
        super().__init__()
        #self.setupUi(self)
        #  주소 목록을 받아서 self.aList에 할당
        self.aList = []
        # 시작시 초기 함수 호출
        self.initUI()

        # 추가 window 설정
        #self.new_window = SecondWindow(self)

    def initUI(self):
        
        # python, pyqt5로 만든 프로그램창을 항상 맨 위에 있게 하려면 Qt.WindowStaysOnTopHint
        # self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowStaysOnTopHint)
        
        # 선택한 주소값과 시작년도
        self.selAddress = ""
        self.sYear = 2017

        # button list 변수 생성
        self.button = []

        # lineEdit list 변수 생성
        self.lineEdit = []

        # textEdit list 변수 생성
        self.textEdit = []

        # progress bar list 변수 생성
        self.progressBar = []

        # grid layout list 변수 생성
        self.grid = []

        # groupbox list 변수 생성
        self.groupbox = []

        # Grid Layout으로 window 창 표시
        grid1 = QGridLayout()
        
        # self의 function을 호출하여 해당 에 할당
        # addWidget(QWidget, int r, int c, int rowspan, int columnspan)
        grid1.addWidget(self.createSearchGroup(), 0, 0, 1, 1)
        # 사고지점 선택과 시작년도 선택 widget은 일단 비워두고 시작

        # grid1.addWidget(self.createAccidentPlaceGroup(), 0, 0, 1, 1)
        # grid1.addWidget(self.createStartYearGroup(), 1, 0, 1, 1)
        # grid1.addWidget(self.createPushButtonGroup(), 2, 0, 1, 1)
        grid1.addWidget(self.createExplainGroup(), 0, 1, 1, 1)

        # grid layout list에 grid1 추가: self.grid[0]
        self.grid.append(grid1)

        # grid를 Window Layout에 할당
        self.setLayout(self.grid[0])

        # window Title 할당
        self.setWindowTitle('화학사고 지점 검색')

        # Window 위치와 사이즈: (x, y, width, height)
        self.setGeometry(300, 100, 700, 400)

        # Window display
        self.center()
        self.show()
    
    def center(self):
        # 창을 데스크탑 센터에 띄우기
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def createSearchGroup(self):
        groupbox = QGroupBox('사고지점 검색')

        # 텍스트 입력 받기 위한 QLineEdit 추가
        lineEdit = QLineEdit()
        self.lineEdit.append(lineEdit)    # self.lineEdit list에 추가

        guideText1 = "위 입력창에 사고지점 주소 또는 건물명을 입력하고 \n검색 버튼을 누르세요.\n(예시:  \'세종로 100\' 또는 \'종로구청\')" 
        labelExp1 = QLabel(guideText1, self)

        searchButton = QPushButton('검색', self)         # button
        searchButton.clicked.connect(self.sClickMethod)  # button click event 연결

        guideText2 = "\n안내: \n해당 검색어로 10개 이하의 주소가 검색되면 \n강우 유출량 산정을 위한 새 창으로 이동합니다. \n" + \
                        "새 창에서 사고 주소와 시작년도를 선택하여 \n강우 유출량 산정을 하시면 됩니다."
        labelExp2 = QLabel(guideText2, self)

        # 세로형 BoxLayout 생성
        vbox = QVBoxLayout()
        vbox.addWidget(lineEdit)       # lineEdit을 위젯으로 추가
        vbox.addWidget(labelExp1)
        vbox.addWidget(searchButton)    # searchButton을 위젯으로 추가
        vbox.addWidget(labelExp2)
        vbox.addStretch(1)              # 빈 줄

        # vbox를 groupbox layout으로 할당
        groupbox.setLayout(vbox)

        return groupbox
    
    def append_text(self, text):
        # QTextEdit에 텍스트 출력
        self.textEdit[0].append(' ' + text + '\n')
        self.textEdit[0].moveCursor(QtGui.QTextCursor.End)
        self.textEdit[0].setFocus()
        QApplication.processEvents()    # QTextEdit 창을 refresh

    def createExplainGroup(self):
        groupbox = QGroupBox('진행상황')
        groupbox.setFlat(True)   # groupbox border없게 설정

        # textEdit widget 생성
        te = QTextEdit()
        self.textEdit.append(te)
        te.setText("여기에 진행상황을 안내합니다. \n")

        vbox = QVBoxLayout()
        vbox.addWidget(te)

        groupbox.setLayout(vbox)
        self.groupbox.append(groupbox)

        return groupbox
    
    def sClickMethod(self):
        # 주소 검색 버튼
        print('검색어: ' + self.lineEdit[0].text())
        self.append_text('\'' + self.lineEdit[0].text() + '\' 검색어로 주소를 검색합니다.')
        
        self.aList = sj.findAddress(self.lineEdit[0].text())

        print(self.aList)

        if self.aList[0] == '9999':
            self.append_text(self.aList[1])
            self.lineEdit[0].setText('')
        else:
            """
            addPrint = ""
            for i in self.aList:
                addPrint += i + ' '
            """
            self.append_text(' ' + str(len(self.aList)) + '개의 주소가 검색되었습니다.\n강우 유출량 산정을 위한 새 창으로 이동합니다.\n')

            #self.grid[0].addWidget(self.createAccidentPlaceGroup(), 1, 0, 1, 1)
            #self.grid[0].addWidget(self.createStartYearGroup(), 2, 0, 1, 1)
            #self.grid[0].addWidget(self.createPushButtonGroup(), 3, 0, 1, 1)
            
            self.win = SecondWindow(self.aList)
            r = self.win.showModal
            

def main():
    app = QApplication(sys.argv)
    main = Window()
    main.show()
    # s = SecondWindow()
    # main.textChanged.connect(s.text.append)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()