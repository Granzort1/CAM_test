############################################################ 
### 모형 결과 보기 윈도우
#   매체 선택, 시간 선택, 차트 선택 메뉴
#   결과 보기 버튼을 누르면 차트를 보여줌
#   결과 파일을 위 Grid를 출력하고 자동으로 1시간 간격 데이터와 
#   1분 간격 데이터를 load하여 numpy array zarray[150, 150, time_frame] 형태로 저장
#   air_h_zarray[150,150,11]
#   air_m_zarray[150,150,660]
#   soil_h_zarray[150,150,11]
#   soil_m_zarray[150,150,660]
#   
#   text file의 데이터를 불러와서 numpy 변수에 저장하고, 이를 다시 .npy로 저장
#   이 파일을 파이썬 파일에서 호출하여 holoviews 그래프 보여주는 bokeh server를 띄우도록 함
############################################################ 

import sys
import ctypes
from time import sleep

from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import os
import matplotlib as m
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import sys
import matplotlib.font_manager as fm

# ploting module
import holoview_ManySubplots_slider_v4 as hms
import holoview_image_slider_n_play_v4 as his
import holoview_3dSurface_slider_n_play_v4 as hts

import holoviews as hv
hv.extension('bokeh', 'plotly')

# 한글 폰트 사용을 위해서 세팅
import matplotlib.font_manager as fm
from matplotlib import rc

font_path = "C:/Windows/Fonts/malgun.ttf"
font = fm.FontProperties(fname=font_path).get_name()
rc('font', family=font)

# colormap 색 설정
cdict = {
  'red'  :  ( (0.0, 0.25, .25), (0.02, .59, .59), (1., 1.00, 1.00)),
  'green':  ( (0.0, 0.00, 0.0), (0.02, .45, .45), (1., .970, .970)),
  'blue' :  ( (0.0, 1.00, 1.0), (0.02, .75, .75), (1., 0.45, 0.45))
}

# generating a smoothly-varying LinearSegmentedColormap
cm = m.colors.LinearSegmentedColormap('my_colormap', cdict, 1024)

# from viewResultsInManySubplots import viewResults

class ThreadClass(QtCore.QThread): 

    def __init__(self, parent = None): 
        super(ThreadClass,self).__init__(parent)

    def run(self): 
        print('Thread start')

class SubWindow(QDialog):
    def __init__(self, media, interval, chart_type, zarray):
        super().__init__()

        self.media = media
        self.interval = interval
        self.chart_type = chart_type
        self.zarray = zarray
        
        self.initUI()
    
    def initUI(self):
        title = self.media + ', ' + self.interval + ', ' + self.chart_type
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 200, 100)

        layout = QVBoxLayout()
        layout.addStretch(1)
        
        edit = QLineEdit()
        font = edit.font()
        font.setPointSize(20)
        edit.setFont(font)
        self.edit = edit
        edit.setText('shape = {}'.format(self.zarray.shape))
        
        subLayout = QHBoxLayout()
        
        btnOK = QPushButton("확인")
        btnOK.clicked.connect(self.onOKButtonClicked)
        btnCancel = QPushButton("취소")
        btnCancel.clicked.connect(self.onCancelButtonClicked)
        
        layout.addWidget(edit)
        
        subLayout.addWidget(btnOK)
        subLayout.addWidget(btnCancel)
        layout.addLayout(subLayout)
        layout.addStretch(1)
        self.setLayout(layout)

        """
        # media, interval, chart_type
        if self.chart_type == 'multichart': 
            hms.viewResults(self.media, self.interval, self.zarray)
        elif self.chart_type == '2D_animation': 
            his.viewResults(self.media, self.interval, self.zarray)
        else:
            hts.viewResults(self.media, self.interval, self.zarray)
        """
        
    def onOKButtonClicked(self):
        self.accept()
    def onCancelButtonClicked(self):
        self.reject()
    def showModal(self):
        return super().exec_()

class Window(QWidget):
    
    def __init__(self):
        # to hide command console python
        # ctypes.windll.user32.ShowWindow( ctypes.windll.kernel32.GetConsoleWindow(), 0 )
        
        self.threadclass = ThreadClass()
        
        # QWidget의 __init__() 메서드 호출
        super().__init__()
        
        #self.setupUi(self)
        # 주소 목록을 받아서 self.aList에 할당
        self.aList = []
        # 시작시 초기 함수 호출
        self.initUI()

        # 추가 window 설정
        #self.new_window = SecondWindow(self)
        self.mRadio_buttons[0].clicked.connect(self.mRadiobuttonClickFunction)
        self.mRadio_buttons[1].clicked.connect(self.mRadiobuttonClickFunction)

        self.hRadio_buttons[0].clicked.connect(self.hRadiobuttonClickFunction)
        self.hRadio_buttons[1].clicked.connect(self.hRadiobuttonClickFunction)

        self.cRadio_buttons[0].clicked.connect(self.cRadiobuttonClickFunction)
        self.cRadio_buttons[1].clicked.connect(self.cRadiobuttonClickFunction)
        self.cRadio_buttons[2].clicked.connect(self.cRadiobuttonClickFunction)
        self.cRadio_buttons[3].clicked.connect(self.cRadiobuttonClickFunction)

    def initUI(self):
        
        # python, pyqt5로 만든 프로그램창을 항상 맨 위에 있게 하려면 Qt.WindowStaysOnTopHint
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        
        # 선택한 주소값과 시작년도
        # self.selAddress = ""

        # subwindow에 넘겨주는 변수
        self.media = 'Air'
        self.interval = '1hour_interval'
        self.chart_type = 'multichart'
        self.zarray_h4plot = np.zeros((150, 150, 11))
        self.zarray_m4plot = np.zeros((150, 150, 660))
        """
        # zarray 변수 4가지
        self.air_h_zarray = []
        self.air_m_zarray = []
        self.soil_h_zarray = []
        self.soil_m_zarray = []
        """
        # radio button용 변수
        self.tinterval = '1hour_interval'
        self.charttype = 'multichart'

        # label list 변수 생성
        self.label = []

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
        grid1.addWidget(self.createTitleGroup(), 0, 0, 1, 2)
        
        grid1.addWidget(self.createSelectMediaGroup(), 1, 0, 1, 1)
        grid1.addWidget(self.createSelectTimeGroup(), 2, 0, 1, 1)
        grid1.addWidget(self.createSelectChartGroup(), 3, 0, 1, 1)
        grid1.addWidget(self.createButtonGroup(), 4, 0, 1, 1)

        # grid1.addWidget(self.createAccidentPlaceGroup(), 0, 0, 1, 1)
        # grid1.addWidget(self.createStartYearGroup(), 1, 0, 1, 1)
        # grid1.addWidget(self.createPushButtonGroup(), 2, 0, 1, 1)
        grid1.addWidget(self.createExplainGroup(), 1, 1, 4, 1)

        # grid layout list에 grid1 추가: self.grid[0]
        self.grid.append(grid1)

        # grid를 Window Layout에 할당
        self.setLayout(self.grid[0])

        # window Title 할당
        self.setWindowTitle('화학사고 모형 결과 보기')

        # Window 위치와 사이즈: (x, y, width, height)
        self.setGeometry(300, 100, 550, 400)

        # Window display
        self.center()
        self.show()

        self.button[0].setEnabled(False)
        
        # 모형 결과 파일을 읽어서 Numpy 변수에 할당
        
        self.progressBar[0].setProperty("value", 0)
        self.air_h_zarray = self.load__model_results('Air', '1hour_interval')
        self.progressBar[0].setProperty("value", 5)
        self.air_m_zarray = self.load__model_results('Air', '1minute_interval')
        self.progressBar[0].setProperty("value", 50)
        self.soil_h_zarray = self.load__model_results('Soil', '1hour_interval')
        self.progressBar[0].setProperty("value", 55)
        self.soil_m_zarray = self.load__model_results('Soil', '1minute_interval')
        self.progressBar[0].setProperty("value", 100)
        
        
        #print('air 1hour shape: {}'.format(self.air_h_zarray.shape))
        #print('air 1min shape: {}'.format(self.air_m_zarray.shape))
        #print('soil 1hour shape: {}'.format(self.soil_h_zarray.shape))
        #print('soil 1min shape: {}'.format(self.soil_m_zarray.shape))

        self.append_text('모형 결과를 읽어서 변수에 할당하는 것을 완료하였습니다.')
        self.button[0].setEnabled(True)
        self.label[0].hide()
        self.progressBar[0].setVisible(False)
        
        # python, pyqt5로 만든 프로그램창을 항상 맨 위에 있게 하려면 Qt.WindowStaysOnTopHint
        self.setWindowFlags(self.windowFlags() & ~ QtCore.Qt.WindowStaysOnTopHint)
    
    def mRadiobuttonClickFunction(self):
        self.progressBar[0].setProperty("value", 0)
        if self.mRadio_buttons[0].isChecked(): self.append_text('대기 매체가 선택되었습니다.')
        elif self.mRadio_buttons[1].isChecked(): self.append_text('토양 매체가 선택되었습니다.')

    def hRadiobuttonClickFunction(self):
        self.progressBar[0].setProperty("value", 0)
        if self.hRadio_buttons[0].isChecked(): 
            # self.cRadio_buttons[0].setChecked(True)
            # self.cRadio_buttons[1].setEnabled(True)
            self.cRadio_buttons[2].setEnabled(True)
            self.append_text('1시간 간격 모형 시뮬레이션 결과가 선택되었습니다.')
        elif self.hRadio_buttons[1].isChecked(): 
            self.cRadio_buttons[0].setChecked(True)
            self.cRadio_buttons[1].setEnabled(True)
            self.cRadio_buttons[2].setEnabled(True)
            self.append_text('1분 간격 모형 시뮬레이션 결과가 선택되었습니다.')

    def cRadiobuttonClickFunction(self):
        self.progressBar[0].setProperty("value", 0)
        if self.cRadio_buttons[0].isChecked(): 
            self.append_text('2D 애니메이션 차트 보기가 선택되었습니다.')
        elif self.cRadio_buttons[1].isChecked(): 
            self.append_text('3D 애니메이션 차트 보기가 선택되었습니다.')
        elif self.cRadio_buttons[2].isChecked(): 
            self.append_text('다중 차트 보기가 선택되었습니다.')
        elif self.cRadio_buttons[3].isChecked(): 
            self.append_text('지도 보기가 선택되었습니다.')

    def center(self):
        # 창을 데스크탑 센터에 띄우기
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def createTitleGroup(self):
        groupbox = QGroupBox(' ')

        hbox = QHBoxLayout(self)
        pixmap = QPixmap(r"c:\CAM_test\pyWin4MMM\images\view_model_results.png")

        lbl = QLabel(self)
        lbl.setPixmap(pixmap)
        self.resize(150,50)

        hbox.addWidget(lbl)

        groupbox.setLayout(hbox)
        groupbox.setStyleSheet("QGroupBox { border: 0px solid }")

        return groupbox

    def createSelectMediaGroup(self):
        groupbox = QGroupBox('매체 선택')

        # 텍스트 입력 받기 위한 QLineEdit 추가
        # lineEdit = QLineEdit()
        # self.lineEdit.append(lineEdit)    # self.lineEdit list에 추가

        # 가로형 BoxLayout 생성
        hbox = QHBoxLayout()

        mList = ['대기', '토양']
        self.mRadio_buttons = []

        for m in mList:
            radio1 = QRadioButton(m)
            self.mRadio_buttons.append(radio1)
            hbox.addWidget(radio1)

        self.mRadio_buttons[0].setChecked(True)

        groupbox.setLayout(hbox)
        groupbox.setFixedWidth(250)

        self.groupbox.append(hbox)

        return groupbox

    def createSelectTimeGroup(self):
        groupbox = QGroupBox('시간 선택')

        # 텍스트 입력 받기 위한 QLineEdit 추가
        # lineEdit = QLineEdit()
        # self.lineEdit.append(lineEdit)    # self.lineEdit list에 추가

        # 가로형 BoxLayout 생성
        hbox = QHBoxLayout()

        hList = ['1시간 간격', '1분 간격']
        self.hRadio_buttons = []

        for h in hList:
            radio2 = QRadioButton(h)
            self.hRadio_buttons.append(radio2)
            hbox.addWidget(radio2)

        self.hRadio_buttons[0].setChecked(True)

        groupbox.setLayout(hbox)
        groupbox.setFixedWidth(250)

        self.groupbox.append(hbox)

        return groupbox

    def createSelectChartGroup(self):
        groupbox = QGroupBox('결과 보기 선택')

        # 텍스트 입력 받기 위한 QLineEdit 추가
        # lineEdit = QLineEdit()
        # self.lineEdit.append(lineEdit)    # self.lineEdit list에 추가

        # 가로형 BoxLayout 생성
        vbox = QVBoxLayout()

        cList = ['2D 애니메이션 차트', '3D 애니메이션 차트', '다중 차트', '지도']
        self.cRadio_buttons = []

        for c in cList:
            radio3 = QRadioButton(c)
            self.cRadio_buttons.append(radio3)
            vbox.addWidget(radio3)

        self.cRadio_buttons[0].setChecked(True)

        groupbox.setLayout(vbox)
        groupbox.setFixedWidth(250)

        self.groupbox.append(vbox)

        return groupbox

    def createButtonGroup(self):
        groupbox = QGroupBox('제어 센터')

        # 텍스트 입력 받기 위한 QLineEdit 추가
        # lineEdit = QLineEdit()
        # self.lineEdit.append(lineEdit)    # self.lineEdit list에 추가

        #guideText3 = "위 매체와 시간 선택 옵션을 선택하고 결과 보기를 선택하세요." 
        #labelExp3 = QLabel(guideText3, self)

        guideText4 = "모형 결과 데이터를 읽는 중..." 
        labelExp4 = QLabel(guideText4, self)
        self.label.append(labelExp4)

        searchButton = QPushButton('결과 보기', self)         # button
        searchButton.clicked.connect(self.sClickMethod)  # button click event 연결
        self.button.append(searchButton)

        # 세로형 BoxLayout 생성
        vbox = QVBoxLayout()

        vbox.addWidget(searchButton)    # searchButton을 위젯으로 추가

        vbox.addWidget(labelExp4)

        # 전체용 progressBar
        pbar0 = QProgressBar()
        pbar0.setGeometry(30, 30, 230, 25)
        self.progressBar.append(pbar0)
        vbox.addWidget(pbar0)

        groupbox.setLayout(vbox)
        groupbox.setFixedWidth(250)

        return groupbox

    def createExplainGroup(self):
        groupbox = QGroupBox('진행상황')
        groupbox.setFlat(True)   # groupbox border없게 설정

        # textEdit widget 생성
        te = QTextEdit()
        self.textEdit.append(te)
        te.setText(" 여기에 진행상황을 안내합니다. \n " + "매체와 시간 선택 옵션을 선택하고 결과 보기 버튼을 누르세요.")

        vbox = QVBoxLayout()
        vbox.addWidget(te)

        groupbox.setLayout(vbox)
        groupbox.setFixedWidth(300)
        #self.groupbox.append(groupbox)

        return groupbox

    def append_text(self, text, lf=True):
        # QTextEdit에 텍스트 출력
        if lf: self.textEdit[0].append(' ' + text + '\n') 
        else: self.textEdit[0].append(' ' + text)

        self.textEdit[0].moveCursor(QtGui.QTextCursor.End)
        self.textEdit[0].setFocus()
        QApplication.processEvents()    # QTextEdit 창을 refresh

    def load__model_results(self, media, interval):

        if media == 'Air': media_k = '대기' ; pbar_value_ini = 0
        else: media_k = '토양' ; pbar_value_ini = 50
        if interval == '1hour_interval': interval_k = '시간 단위' ; pbar_size = 5
        else: interval_k = '분 단위' ; pbar_value_ini += 5 ; pbar_size = 45

        # 150 * 150  x, y grid array 생성
        x = np.arange(1, 151)
        y = np.arange(1, 151)

        # load result text files
        folder = f'c:/CAM_test/OutFile/Concentration/{interval}/{media}/'
        fileList = os.listdir(folder)

        print('loading text files...')
        self.append_text(f'{media_k} 매체의 {interval_k} 형 결과 파일들을 읽고 있습니다...')

        # result file의 갯수
        nfiles = len(fileList)

        # x는 150개, y는 150개, z는 150 * 150  x, y, z numpy array 생성
        zarray = np.zeros((150, 150, nfiles))

        # result conc.를 저장하기 위한 numpy 변수 생성
        conc = np.zeros((22500, nfiles))

        # result conc.를 numpy 변수에 저장
        i = 0
        for res in fileList:
            print(f'{res} 파일을 읽고 있습니다...')
            self.append_text(f'{res} 파일을 읽고 있습니다...', False)
            # print('loading {}...'.format(res))
            tmp_conc = np.loadtxt(folder + res, dtype='float')
            tmp_conc_r = np.ravel(tmp_conc)
            conc[:, i] = tmp_conc_r

            # 22500개 1차원 np array를 150*150 2차원 np array로 변환
            tmp_conc_rs = tmp_conc_r.reshape(150,150)
            zarray[:,:, i] = tmp_conc_rs

            pbar_value = round(pbar_value_ini + (pbar_size * (i/nfiles)), 1)
            self.progressBar[0].setProperty("value", pbar_value)

            i += 1
        
        self.append_text(f'{media_k} 매체의 {interval_k} 모형 결과 파일들을 읽어 변수에 할당하였습니다.')

        # .npy filename
        npy_file = f'c:/CAM_test/OutFile/{media}_{interval}.npy'
        np.save(npy_file, zarray)
        return zarray

    def sClickMethod(self):
        # 검색 버튼 click event
        slmedia = ""
        sltint = ""

        self.progressBar[0].setVisible(False)
        self.progressBar[0].setProperty("value", 0)
        
        for mrbtn in self.mRadio_buttons:
            if mrbtn.isChecked():
                media_temp = mrbtn.text()
                # self.media = mrbtn.text()
                if media_temp == '대기': slmedia = 'Air' ; self.media = 'Air'
                else: slmedia = 'Soil' ; self.media = 'Soil'
                break

        for hrbtn in self.hRadio_buttons:
            if hrbtn.isChecked():
                self.tinterval = hrbtn.text()
                if self.tinterval == '1시간 간격': sltint = '1hour_interval' ; self.interval = '1hour_interval'
                else: sltint = '1minute_interval' ; self.interval = '1minute_interval'
                break

        for crbtn in self.cRadio_buttons:
            if crbtn.isChecked():
                self.charttype = crbtn.text()
                if self.charttype == '2D 애니메이션 차트': slchart = '2D_animation' ; self.chart_type = '2D_animation'
                elif self.charttype == '3D 애니메이션 차트': slchart = '3D_animation' ; self.chart_type = '3D_animation'
                elif self.charttype == '다중 차트': slchart = 'multichart' ; self.chart_type = 'multichart'
                elif self.charttype == '지도': slchart = 'mapview' ; self.chart_type = 'mapview'
                else: slchart = 'mapview' ; self.chart_type = 'mapview'
                break
        
        slmedia_k = '대기' if slmedia == 'Air' else '토양'
        sltint_k = '1시간 간격' if sltint == '1hour_interval' else '1분 간격'
        
        print(f'{slmedia_k} 매체에 대한 {sltint_k} 모형 시뮬레이션 결과를 {self.charttype} 보기로 선택하였습니다. ')        
        self.append_text(f'{slmedia_k} 매체에 대한 {sltint_k} 모형 시뮬레이션 결과를 {self.charttype} 보기로 선택하였습니다. ')        
        
        if slchart == 'multichart': 
            # holoviews(image), panel, bokeh server 사용 2d animantion
            os.system(f'c:/ProgramData/Anaconda3/python.exe c:/CAM_test/pyWin4MMM/holoview_ManySubplots_slider_v4.py {slmedia} {sltint}')
            # os.system('c:/ArcGISpro/bin/Python/envs/arcgispro-py3/python.exe c:/CAM_test/pyWin4MMM/holoview_ManySubplots_slider_v4.py {} {}'.format(slmedia, sltint))
            # self.win = hms.viewResults(slmedia, sltint, zarray4plot)
            # r = self.win.showModal

        elif slchart == '2D_animation': 
            # holoviews(image), panel, bokeh server 사용 2d animantion
            os.system(f'c:/ProgramData/Anaconda3/python.exe c:/CAM_test/pyWin4MMM/holoview_image_slider_n_play_v4.py {slmedia} {sltint}')
            # matplotlib 사용 2d animation
            # os.system('c:/ArcGISpro/bin/Python/envs/arcgispro-py3/python.exe c:/CAM_test/pyWin4MMM/viewModelResults.py {} {}'.format(slmedia, sltint))
            # self.win = his.viewResults(slmedia, sltint, zarray4plot)
            # r = self.win.showModal
            
        elif slchart == '3D_animation': 
            # print('매체: {}, 간격: {}'.format(slmedia, sltint))
            # holoviews
            os.system(f'c:/ProgramData/Anaconda3/python.exe c:/CAM_test/pyWin4MMM/holoview_3dsurface_slider_n_play_v4.py {slmedia} {sltint}')
            # matplotlib
            # os.system('c:/ArcGISpro/bin/Python/envs/arcgispro-py3/python.exe c:/CAM_test/pyWin4MMM/viewResults_3D_surface_v2.py {} {}'.format(slmedia, sltint))
            # self.win = hts.viewResults(slmedia, sltint, zarray4plot)
            # r = self.win.showModal
            
        else:
            # 기본 web browser 사용, 시계별 결과 지도 보기
            # os.system(f'c:/ProgramData/Anaconda3/pythonw.exe c:/CAM_test/pyWin4MMM/viewResultsOnMapWindow_v1.pyw {slmedia} {sltint}')
            # 기본 web browser 사용, 최대농도와 시계열 결과 지도 보기
            os.system(f'c:/ProgramData/Anaconda3/pythonw.exe c:/CAM_test/pyWin4MMM/viewResultsOnMapWindow_v3.pyw {slmedia} {sltint}')
            # webview 사용, 결과 지도 보기
            # os.system(f'c:/ProgramData/Anaconda3/pythonw.exe c:/CAM_test/pyWin4MMM/viewResultsOnMapWindow_v1.pyw {slmedia} {sltint}')
            
        # self.win = viewResults(self.media, self.tinterval)
        # r = self.win.showModal
        
        # win = SubWindow(self.media, self.interval, self.chart_type)

def main():
    app = QApplication(sys.argv)
    main = Window()
    main.show()
    # s = SecondWindow()
    # main.textChanged.connect(s.text.append)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()