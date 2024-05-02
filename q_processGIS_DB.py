### QGIS에서 GIS DB processing 하기 위한 모듈
# 1. 검색된 주소 중 주소 선택, 
# 2. QGIS 프로그램(q_main.py를 내부 콘솔에서 불러와서 GIS DB 처리) 호출 기능

import os
import win32gui, win32con
import shutil
import sqlite3
import sys
from math import *
import numpy as np
import pandas as pd
from time import sleep

from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# import q_SearchJuso as sj
# import calculate_grid_move as gm
# import flow_direction as fd

class ThreadClass(QtCore.QThread): 

    def __init__(self, parent = None): 
        super(ThreadClass,self).__init__(parent)

    def run(self): 
        print('Thread start')

class GISWindow(QWidget):
    def __init__(self, alist):
        # to hide command console python
        # the_program_to_hide = win32gui.GetForegroundWindow()
        # win32gui.ShowWindow(the_program_to_hide , win32con.SW_HIDE)
        
        # Thread 사용
        self.threadclass = ThreadClass()
        #super().__init__()
        super().__init__()
        #self.setupUI(self)
        # self.label = QLabel('New Window!')
        self.aList = alist
        #self.aList = ['대구광역시 서구 성서로 20', '대구광역시 서구 성서로 200', '대구광역시 서구 성서로 2000']

        self.initUI()

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
        # self.progressBar = []

        # grid layout list 변수 생성
        self.grid = []

        # groupbox list 변수 생성
        self.groupbox = []

        # Grid Layout으로 window 창 표시
        grid2 = QGridLayout()

        grid2.addWidget(self.createAccidentPlaceGroup(), 0, 0, 1, 1)
        grid2.addWidget(self.createStartYearGroup(), 1, 0, 1, 1)
        grid2.addWidget(self.createPushButtonGroup(), 2, 0, 1, 1)
        grid2.addWidget(self.createExplainGroup(), 0, 1, 3, 1)

        # grid layout list에 grid1 추가: self.grid[0]
        self.grid.append(grid2)

        # grid를 Window Layout에 할당
        self.setLayout(self.grid[0])

        # window Title 할당
        self.setWindowTitle('GIS와 기상 자료 처리')

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

    def dayOfYear(self, date: str) -> int: 
        # 1년 중 몇번째 일인지 리턴
        year, month, day = int(date.split('-')[0]), int(date.split('-')[1]), int(date.split('-')[2]) 

        if year == 2020:
            days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] 
        else:
            days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] 
        
        answer = sum(days[:month-1]) + day 
        
        return answer

    def timeOfYear(self, julDay: int, time: int) -> int:
        # 1년 중 몇번째 시간인지 리턴
        answer = (julDay - 1) * 24 + time

        return answer

    def remove_makeDir(self, filePath):
        if os.path.exists(filePath):
            shutil.rmtree(filePath)
            os.mkdir(filePath)
            return '>> Directory is removed and fresh directory is made.\n'
        else:
            return 'Directory not found'
    
    def createAccidentPlaceGroup(self):
        groupbox = QGroupBox('사고지점 선택')

        # 세로형 layout
        vlay = QVBoxLayout()

        # self에 radio_button list 생성
        self.aCheckbox = []

        groupcheck = QButtonGroup(self)
        
        for j in self.aList:
            checkbox1 = QCheckBox(j)       # QRadioButton 생성. j는 주소값
            print("new " + j)
            # radio1.toggled.connect(self.on_clicked)
            # radio1.setAutoExclusive(True)   # radio button 하나만 누르게 설정
            self.aCheckbox.append(checkbox1)
            groupcheck.addButton(checkbox1)
            vlay.addWidget(checkbox1)
        
        self.aCheckbox[0].setChecked(True)  # 첫번째 버튼 기본 선택 옵션 적용
        
        groupbox.setLayout(vlay)

        return groupbox

    def createStartYearGroup(self):
        groupbox = QGroupBox('시작년도 선택')
        # groupbox.setCheckable(True)
        # groupbox.setChecked(False)

        vbox = QVBoxLayout()

        yList = ['2017', '2018', '2019']
        self.yRadio_buttons = []

        for y in yList:
            radio1 = QRadioButton(y)
            self.yRadio_buttons.append(radio1)
            vbox.addWidget(radio1)

        self.yRadio_buttons[0].setChecked(True)
        # checkbox = QCheckBox('Independent Checkbox')
        # checkbox.setChecked(True)
        # vbox.addWidget(checkbox)
        # vbox.addStretch(1)

        groupbox.setLayout(vbox)

        return groupbox

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

    def createPushButtonGroup(self):
        groupbox = QGroupBox('제어 센터')
        #groupbox.setCheckable(True)
        #groupbox.setChecked(False)

        pushbutton = QPushButton('GIS와 기상 자료 처리')
        pushbutton.clicked.connect(self.on_clicked)
        self.button.append(pushbutton)

        # 전체용 progressBar
        # pbar0 = QProgressBar()
        # pbar0.setGeometry(30, 30, 230, 25)
        # self.progressBar.append(pbar0)
        
        # 모듈용 progressBar
        #pbar1 = QProgressBar()
        #pbar1.setGeometry(60, 30, 230, 25)
        #self.progressBar.append(pbar1)
        
        """
        togglebutton = QPushButton('Toggle Button')
        togglebutton.setCheckable(True)
        togglebutton.setChecked(True)
        flatbutton = QPushButton('Flat Button')
        flatbutton.setFlat(True)
        popupbutton = QPushButton('Popup Button')
        menu = QMenu(self)
        menu.addAction('First Item')
        menu.addAction('Second Item')
        menu.addAction('Third Item')
        menu.addAction('Fourth Item')
        popupbutton.setMenu(menu)
        """
        vbox = QVBoxLayout()
        vbox.addWidget(pushbutton)
        # vbox.addWidget(pbar0)
        # vbox.addWidget(pbar1)
        
        """
        vbox.addWidget(togglebutton)
        vbox.addWidget(flatbutton)
        vbox.addWidget(popupbutton)
        #vbox.addStretch(1)
        """
        groupbox.setLayout(vbox)

        return groupbox
    
    def append_text(self, text):
        # QTextEdit에 텍스트 출력
        self.textEdit[0].append(' ' + text + '\n')
        self.textEdit[0].moveCursor(QtGui.QTextCursor.End)
        self.textEdit[0].setFocus()
        QApplication.processEvents()    # QTextEdit 창을 refresh
    
    def insertJusoData(self, dSql, iSql):
        # SQLite DB 연결
        conn = sqlite3.connect(r"c:\CAM_test\GIS_DB\db4MMM.db")
        
        # Connection으로부터 Cursor 생성
        cur = conn.cursor()

        cur.execute(dSql)
        conn.commit()

        cur.execute(iSql)
        conn.commit()

        # Connection 닫기
        cur.close()
        conn.close()

    # button click 이벤트
    @QtCore.pyqtSlot()
    def on_clicked(self):

        # GIS와 기상 자료 처리 버튼 실행 시 작동
        # 주소와 연도를 sqlite db에 저장하고 QGIS file open(c:\CAM_test\py4MMM\Job_v1.qgz)
        
        i = 0
        for addbtn in self.aCheckbox:
            print(addbtn.text())
            if addbtn.isChecked():
                print("No. {} selected. address: {}".format(i, addbtn.text()))
                self.selAddress = addbtn.text()
                break
            i += 1

        for ybtn in self.yRadio_buttons:
            if ybtn.isChecked():
                self.sYear = ybtn.text()
                break

        # Control_In.csv 파일을 읽어서 sqlite simulation_info에 저장
        import csv
 
        f = open(r'c:\CAM_test\Inputs\Control_In.csv', 'r', encoding='utf-8')
        rdr = csv.reader(f)
        i = 0
        for line in rdr:
            if i == 1: 
                param_s = line
                print(param_s)
            i += 1
        f.close()    

        param_i = []
        # param_s = param_temp.split(',')
        
        for i in range(len(param_s)):
            param_i.append(int(param_s[i]))

        print('사고지점: \'' + self.selAddress + '\'\n 시뮬레이션 시작년도: \'' 
            + str(self.sYear)  + '년\'\n 위 설정을 적용하여 GIS와 기상 자료 처리를 시작합니다.')
        self.append_text('사고지점: \'' + self.selAddress + '\'\n 시뮬레이션 시작년도: \'' 
            + str(self.sYear)  + '년\'\n 위 설정을 적용하여 GIS와 기상 자료 처리를 시작합니다.')

        address_list = self.selAddress.split(' ')
        dSql ="DELETE FROM simulation_info"
        iSql ="INSERT INTO simulation_info (sido, sigungu, address, s_year, s_month, s_day, s_hour, s_minute, simulation_duration, gis_method) VALUES('{}', '{}', '{}', {}, {}, {}, {}, {}, {}, '{}');".format(
            address_list[0], address_list[1], self.selAddress, self.sYear, param_i[1], param_i[2], param_i[3], param_i[4], param_i[9], 'qgis')
        
        self.insertJusoData(dSql, iSql)
        
        self.button[0].setEnabled(False)                        

        self.append_text('모델링을 위한 사고 정보 세팅을 완료하였습니다. ')

        # QGIS File Open
        os.startfile('c:/CAM_test/pyWin4MMM/Job_v1.qgz')

        # 현재 창 닫기
        self.close()

        # self.button[0].setEnabled(True)
        # self.progressBar[0].setProperty("value", 0)
        #self.progressBar[1].setProperty("value", 0)
        #self.lineEdit[0].setText('')
        #self.removeFormLayout(self.grid[0])        

    def showModal(self):
        return super().exec_()

def main():
    app = QApplication(sys.argv)
    shower = GISWindow()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()