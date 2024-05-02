############################################################ 
### 모형 결과 지도 보기 윈도우
#   매체 선택, 시간 선택,
#   결과 보기 버튼을 누르면 지도를 보여줌
#   
#   모형 결과 중 격자별 최대값과 최대값일 때 시간을 합쳐서 1장의 지도로 표출 
#   윈도우 기본 웹브라우저를 호출하여 지도를 출력
############################################################ 

import sys
import ctypes
import win32gui, win32con
from time import sleep

from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import os
import matplotlib as m
import numpy as np
import pandas as pd

# 한글 폰트 사용을 위해서 세팅
import matplotlib.font_manager as fm
from matplotlib import rc

import geopandas as gpd
import folium
from folium import plugins
import branca.colormap as cm

import platform
import sqlite3
import json
#import webview
import webbrowser

from urllib.request import urlopen
from urllib import parse
from urllib.request import Request
from urllib.error import HTTPError

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

### 전역변수
# Windows와 Mac을 구분하여 폴더 이름을 다르게 지정함
platform = platform.platform()
if platform.split('-')[0] =='Windows':
    folder = 'c:/CAM_test/pyWin4MMM/html/'
    shp_folder = 'c:/CAM_test/GIS_DB/MyProject/raster/'
else:
    folder = '/Users/gaia/Downloads/display_on_map/'
    shp_folder = '/Users/gaia/Downloads/CAM_test/GIS_DB/MyProject/raster/'

# 화학 사고 위치
address = '울산시 중구 함월15길 65' 

# 모델링 결과를 가져올 매체와 interval 설정
media = 'Air'
interval = '1hour_interval'

media_k = '대기' if media == 'Air' else '토양'
interval_k = '시간' if interval == '1hour_interval' else '분'

time_frames = 10   # 기본 지도 생성 숫자

class ThreadClass(QtCore.QThread): 

    def __init__(self, parent = None): 
        super(ThreadClass,self).__init__(parent)

    def run(self): 
        print('Thread start')

class Window(QWidget):
    
    def __init__(self, media, interval):
        # to hide command console python
        # the_program_to_hide = win32gui.GetForegroundWindow()
        # win32gui.ShowWindow(the_program_to_hide , win32con.SW_HIDE)
        
        # Thread 사용
        self.threadclass = ThreadClass()
        
        # QWidget의 __init__() 메서드 호출
        super().__init__()
        
        # 처음으로 지도보기 창을 호출할 때 초기 변수값: media, interval
        self.media = media
        self.interval = interval
        self.datatype = 'conc_max'
        
        print(f'{self.media} 매체, {self.interval} 시간 간격')
        
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

    def initUI(self):
        
        # python, pyqt5로 만든 프로그램창을 항상 맨 위에 있게 하려면 Qt.WindowStaysOnTopHint
        # self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        
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
        # >> 해석: (r, c) 좌표에 너비 크기 rowspan, 높이 크기 colspan의 QWidget 생성
        
        # window title
        grid1.addWidget(self.createTitleGroup(), 0, 0, 1, 2)
        
        # 매체 선택 widget
        grid1.addWidget(self.createSelectMediaGroup(), 1, 0, 1, 1)
        
        # 시간 간격 선택 widget
        grid1.addWidget(self.createSelectTimeGroup(), 2, 0, 1, 1)
        
        # 데이터 선택 widget
        grid1.addWidget(self.createSelectDatatypeGroup(), 3, 0, 1, 1)
        
        # 버튼과 진행바 선택 widget
        grid1.addWidget(self.createButtonGroup(), 4, 0, 1, 1)

        # 진행상활 알려주는 창 widget
        grid1.addWidget(self.createExplainGroup(), 1, 1, 4, 1)

        # grid layout list에 grid1 추가: self.grid[0]
        self.grid.append(grid1)

        # grid[0](grid1)를 Window Layout에 할당
        self.setLayout(self.grid[0])

        # window Title 할당
        self.setWindowTitle('모형결과 지도 보기')

        # Window 위치와 사이즈: (x, y, width, height)
        self.setGeometry(300, 100, 550, 400)

        # Window display
        self.center()
        self.show()

        # button[0] 활성화
        self.button[0].setEnabled(True)
        
        # self.append_text('매체와 시간 옵션을 선택하고 [모형 결과 지도 보기] 버튼을 누르시면 모형 결과를 지도에서 확인하실 수 있습니다. ')
        self.button[0].setEnabled(True)
        # self.label[0].hide()
        self.progressBar[0].setVisible(False)
        
        # python, pyqt5로 만든 프로그램창 항상 맨 위 해제
        self.setWindowFlags(self.windowFlags() & ~ QtCore.Qt.WindowStaysOnTopHint)
    
    def mRadiobuttonClickFunction(self):
        self.progressBar[0].setProperty("value", 0)
        if self.mRadio_buttons[0].isChecked(): self.append_text('대기 매체가 선택되었습니다.')
        elif self.mRadio_buttons[1].isChecked(): self.append_text('토양 매체가 선택되었습니다.')

    def hRadiobuttonClickFunction(self):
        self.progressBar[0].setProperty("value", 0)
        if self.hRadio_buttons[0].isChecked(): self.append_text('1시간 간격 모형 시뮬레이션 결과가 선택되었습니다.')
        elif self.hRadio_buttons[1].isChecked(): self.append_text('1분 간격 모형 시뮬레이션 결과가 선택되었습니다.')

    def cRadiobuttonClickFunction(self):
        self.progressBar[0].setProperty("value", 0)
        if self.cRadio_buttons[0].isChecked(): self.append_text('격자별 최대 농도 데이터가 선택되었습니다.')
        elif self.cRadio_buttons[1].isChecked(): self.append_text('시계열 농도 데이터가 선택되었습니다.')
        
    def center(self):
        # 창을 데스크탑 센터에 띄우기
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def createTitleGroup(self):
        groupbox = QGroupBox(' ')

        hbox = QHBoxLayout(self)
        pixmap = QPixmap(r"c:\CAM_test\pyWin4MMM\images\view_model_results_on_map.png")

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

        # window를 호출할 때 변수값으로 보낸 매체에 따라 라디오 버튼이 선택되도록 설정
        if self.media == 'Air': self.mRadio_buttons[0].setChecked(True)
        else: self.mRadio_buttons[1].setChecked(True)

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

        # window를 호출할 때 변수값으로 보낸 매체에 따라 라디오 버튼이 선택되도록 설정
        if self.interval == '1hour_interval': self.hRadio_buttons[0].setChecked(True)
        else: self.hRadio_buttons[1].setChecked(True)

        groupbox.setLayout(hbox)
        groupbox.setFixedWidth(250)

        self.groupbox.append(hbox)

        return groupbox

    def createSelectDatatypeGroup(self):
        groupbox = QGroupBox('데이터 타입 선택')

        # 텍스트 입력 받기 위한 QLineEdit 추가
        # lineEdit = QLineEdit()
        # self.lineEdit.append(lineEdit)    # self.lineEdit list에 추가

        # 가로형 BoxLayout 생성
        vbox = QVBoxLayout()

        cList = ['격자별 최대 농도', '시계열 농도']
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

        guideText3 = "매체와 시간, 데이터 타입 선택 옵션을 \n선택하고 [결과 지도 보기] 버튼을 \n선택하세요." 
        labelExp3 = QLabel(guideText3, self)

        searchButton = QPushButton('결과 지도 보기', self)         # button
        searchButton.clicked.connect(self.sClickMethod)  # button click event 연결
        self.button.append(searchButton)

        # 세로형 BoxLayout 생성
        vbox = QVBoxLayout()

        vbox.addWidget(searchButton)    # searchButton을 위젯으로 추가

        vbox.addWidget(labelExp3)

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
        te.setText(" 여기에 진행상황을 안내합니다. \n " + "매체와 시간 선택 옵션을 선택하고 [모형 결과 지도 보기] 버튼을 누르세요.")

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

    def get_grid_data_all(self, media, interval):
        # media, interval 값에 해당하는 농도 자료 불러와서 numpy 변수인 conc에 할당
        
        npy_filename = f'c:/CAM_test/OutFile/{media}_{interval}.npy'

        media_k = '대기' if media == 'Air' else '토양'
        time_u = '시간 단위' if interval == '1hour_interval' else '분 단위'

        print(f'{media_k} 매체 시뮬레이션 {time_u} 결과 자료를 읽어들이고 있습니다...')
        self.append_text(f'{media_k} 매체 시뮬레이션 {time_u} 결과 자료를 읽어들이고 있습니다...')
        
        zarray = np.load(npy_filename)
        print(f'{media_k} 매체 시뮬레이션 {time_u} 결과 자료를 성공적으로 읽어서 변수에 할당하였습니다.')
        self.append_text(f'{media_k} 매체 시뮬레이션 {time_u} 결과 자료를 성공적으로 읽어서 변수에 할당하였습니다.')
        
        time_frames = zarray.shape[2]

        # result conc.를 저장하기 위한 numpy 변수 생성
        conc = np.zeros((22500, time_frames))
        serial_no = []
        for i in range(1, 22501):
            serial_no.append(i)
        cellid = np.array(serial_no)

        conc_max = np.zeros(time_frames)

        # result conc.를 numpy 변수에 저장
        i = 0
        for za in range(time_frames):
            # print('loading {}...'.format(res))
            tmp_conc = zarray[:,:,i]
            tmp_conc_r = np.ravel(tmp_conc)
            conc[:, i] = tmp_conc_r
            conc_max[i] = np.max(tmp_conc_r)

            i += 1

        return conc

    def get_time_data(self, conc, time_frame):
        # geopandas 연결하기 위해서 time_frame에 해당하는 농도를 선택하여 ['gridcode', 'conc'] 열로 구성된 pandas table 만들기
        
        serial_no = []
        for i in range(1, 22501):
            serial_no.append(i)
        cellid = np.array(serial_no)

        # print(cellid)

        col_names = ['gridcode', 'conc']
        data = np.c_[cellid, conc[:, time_frame]]
        data_df = pd.DataFrame(data, columns=col_names)
        data_df = data_df.astype({'gridcode':'int'})

        # print(data_df)
        
        return data_df

    def get_concmax_time_data(self, conc_max):
        # geopandas 연결하기 위해서 ['gridcode', 'conc', 'time'] 열로 구성된 pandas table 만들기
        
        serial_no = []
        for i in range(1, 22501):
            serial_no.append(i)
        cellid = np.array(serial_no)

        col_names = ['conc', 'time']
        conc_df = pd.DataFrame(conc_max, columns=col_names)
        conc_df.insert(0, 'gridcode', cellid)
        conc_df = conc_df.astype({'gridcode':'int'})
        
        print(conc_df.head())    

        #col_names = ['gridcode', 'conc', 'time']
        #data0 = np.c_[cellid, conc[:, 0]]
        #data1 = np.c_[data0, conc[:, 1]]
        #data_df = pd.DataFrame(data0, columns=col_names)
        #data_df = data_df.astype({'gridcode':'int'})

        # np.savetxt('concmax_time.csv', conc_df, delimiter=',')
        
        return conc_df

    def getAddressWithShpFile(self):
        # sqlite에서 데이터 가져오기: 사고 주소
        # SQLite DB 연결
        conn = sqlite3.connect(r"c:\CAM_test\GIS_DB\db4MMM.db")

        # Connection으로부터 Cursor 생성
        cur = conn.cursor()

        sql = "SELECT address, gis_method FROM simulation_info "
        cur.execute(sql)
        row = cur.fetchone()
        
        address = row[0]
        gis_method = row[1]
        
        shp_file = 'c:/CAM_test/GIS_DB/QGIS/moved_vector.shp' if gis_method == 'qgis' else 'c:/CAM_test/GIS_DB/MyProject/raster/grid_now.shp'
        
        # Connection 닫기
        cur.close()
        conn.close()
        
        return address, shp_file

    def view_results_on_map(self, media, interval):
        # 시간/분별 농도 자료를 지도에 보여주기. 분별 자료는 최대 10개까지 보여줌
        
        hue = ['BuPu', 'YlGn', 'PuRd', 'OrRd', 'YlGnBu']
        
        self.append_text(f'\n####################################')
        self.append_text(f'화학사고 모형 결과 지도 생성을 시작합니다...')

        # 해당 메체와 시간 간격에 대한 농도 자료 가져오기: 형식 - dataframe['CELLID', 'conc']
        conc = self.get_grid_data_all(media, interval)
        time_frames = conc.shape[1]    # 시간 간격 숫자 가져오기
        
        ### conversion shape file to geojson by geopandas. 
        shp_file = self.getAddressWithShpFile()[1]
        geo_data = gpd.read_file(shp_file, encoding='utf-8')    # EPSG:5186 (UTM 좌표)
        geo_data = geo_data.to_crs("EPSG:4326")                 # EPSG:4326 (경위도 좌표로 변환; geopandas table 내 geometry column의 좌표가 변환됨)

        print(f'shp_file: {shp_file}')
        print(geo_data.head())
        
        self.progressBar[0].setProperty("value", 5)
        
        # CELLID(QGIS) 또는 gridcode(ArcGIS)와 geometry(polygon) 추출
        if shp_file == 'c:/CAM_test/GIS_DB/QGIS/moved_vector.shp':
            geo_data1 = geo_data[['CELLID', 'geometry']]
        else:
            geo_data1 = geo_data[['gridcode', 'geometry']]
        
        geo_data1.columns = ['gridcode', 'geometry'] # geopandas column name change
        print('geo_data1')
        print(geo_data1.head())

        # modeling region 전체 중심점 x, y 좌표 찾기. 지도 표시할 때 중심으로 활용함.
        center_x = geo_data1.centroid.x.mean()
        center_y = geo_data1.centroid.y.mean()
        center = [center_y, center_x]       # shp -> geojson 경위도 좌표로 변환시 long, lati가 되므로 x, y를 바꿔준다.(이유는 TM 좌표가 경도에 해당하는 것이 x, 위도에 해당하는 것이 y임)
        print(f'중심점 좌표: ({center_y},{center_x})')
        
        # 22500개 Grid cell의 중심점 x(경도), y(위도) 좌표에 주소 정보 추가: 단점은 주소 정보에 추가에 시간이 많이 걸린다. 일단 보류 중 
        geo_center = pd.DataFrame(np.vstack([geo_data1.gridcode, geo_data1.centroid.x, geo_data1.centroid.y]).T, columns=['gridcode', 'x', 'y'])
        geo_center = geo_center.astype({'gridcode':'int'})    # gridcode 속성을 int로 변경
        geo_center['address'] = self.getAddressWithShpFile()[0]
        """
        # geo_center의 cell의 중심점 x(경도), y(위도) 좌표에 해당하는 주소 불러와서 address column에 저장
        for i in range(0, geo_center.shape[0]):
            geo_center.loc[i,'address'] = ga.get_address(geo_center.iloc[i]['x'], geo_center.iloc[i]['y'])
        """        
        print(geo_center.head())
        self.append_text(f'사고 지점의 모형 지도를 불러왔습니다.')
        self.progressBar[0].setProperty("value", 10)

        # html folder의 파일 지우기
        def DeleteAllFiles(filePath):
            if os.path.exists(filePath):
                for file in os.scandir(filePath):
                    os.remove(file.path)
                return 'Removed All Files'
        
        DeleteAllFiles(folder)
        
        media_k = '대기' if media == 'Air' else '토양'
        unit_k = 'ug/m3' if media == 'Air' else 'ug/kg'
        time_k = '시간' if interval == '1hour_interval' else '분'
        
        map_frames = time_frames if time_frames < 10 else 10
        
        step_value = round((90 / map_frames) / 5, 0)
        pbar_value = 10

        for i in range(0, map_frames):

            # i 시간에 해당하는 농도 data 불러오기. 시간/분 단위 농도 data(22500 grid data)
            df = self.get_time_data(conc, i)
            print(f'\n{i+1}{time_k} 경과 후 {media_k} 매체의 농도 자료를 가져왔습니다. ')
            star = '*' * (i+1)
            self.append_text(f'\n{star}')
            self.append_text(f'{i+1}{time_k} 경과 후 {media_k} 매체의 농도 자료를 가져왔습니다. ')
            
            # geojson 파일에 df data를 merge(CELLID를 기반으로)
            geo_conc= geo_data1.merge(df, on='gridcode')
            print(geo_conc.head())
            print(f'{i+1}{time_k} 경과 후 {media_k} 매체의 농도 자료를 지도에 병합하였습니다.  ')
            self.append_text(f'>> {i+1}{time_k} 경과 후 {media_k} 매체의 농도 자료를 지도에 병합하였습니다.  ')
            
            pbar_value += step_value; self.progressBar[0].setProperty("value", pbar_value)
            
            # 맵이 center 에 위치하고, zoom 레벨은 11로 시작하는 맵 m을 만듭니다. cartodbpositron 지도를 기본으로 지도 생성
            m = folium.Map(location=center, zoom_start=12, tiles='openstreetmap')
            
            # 'stamenwatercolor', 'cartodbpositron', 'openstreetmap', 'stamenterrain' 네 개의 기본 지도를 지도에 추가. layer control에 들어간다.
            tiles = ['openstreetmap', 'stamenwatercolor', 'cartodbpositron', 'stamenterrain']
            for tile in tiles:
                folium.TileLayer(tile).add_to(m)
                
            print(f'기본 배경 지도를 생성하였습니다. ')
            self.append_text(f'>> 기본 배경 지도를 생성하였습니다. ')
            
            pbar_value += step_value; self.progressBar[0].setProperty("value", pbar_value)
            
            # Choropleth 레이어를 만들고, 맵 m에 추가합니다.
            self.append_text(f'Choropleth 지도(농도 표시한 지도)를 생성하고 있습니다... ')
            
            # geo_conc의 conc 열의 값의 구간별 scale 적용. 구간별 다른 색상을 적용하기 위함. threshhold_scale에 할당. 
            # bins의 구간과 동일하게 되어야 함. 10개를 넘어가니, Diverging Color Scale만 됨
            # Color 참고: https://github.com/python-visualization/folium/issues/403
            # Diverging Color : Spectral, RdYlGn, RdYlBu, RdGy, RdBu, PuOr, PRGn, PiYG, BrBG
            # Sequential Color - Multi-hue: BuPu, YlGn, PuRd, OrRd, YlGnBu
            myscale = (geo_conc['conc'].quantile((0.0, 0.0000000001, 0.000000001, 0.00000001, 0.0000001, 0.000001, 0.00001, 0.0001, 0.001))).tolist()
            # myscale = (geo_conc['conc'].quantile((0.0, 0.0000000001, 0.000000001, 0.00000001, 0.0000001, 0.000001, 0.00001, 0.0001, 0.001, 0.01, 0.1))).tolist()
            
            choropleth = folium.Choropleth(
                geo_data=geo_conc,
                name=f'모형 결과 - {media_k}',  # 지도 위에 출력된 그림의 이름. layer control할 때 사용함.
                data=geo_conc,
                columns=['gridcode', 'conc'],
                key_on='feature.properties.gridcode',
                fill_color='Spectral_r',
                fill_opacity=0.5,
                line_color='#ffffff',
                line_opacity=0.01,
                line_weight=0,
                smooth_factor=0,
                legend_name=f'{media_k} 중 농도({unit_k})',
                # threshhold_scale=myscale,
                # bins=[0.0, 0.0000000001, 0.000000001, 0.00000001, 0.0000001, 0.000001, 0.00001, 0.0001, 0.001]
            ).add_to(m)
            print(f'Choropleth 지도(농도 표시한 지도)를 추가하였습니다. ')
            self.append_text(f'>> Choropleth 지도(농도 표시한 지도)를 추가하였습니다. ')
            
            pbar_value += step_value; self.progressBar[0].setProperty("value", pbar_value)
            
            self.append_text(f'GeoJson 지도(마우스 오버 툴팁 지도)를 생성하고 있습니다... ')
            
            style_function = lambda x: {'fillColor': '#ffffff', 
                                    'color':'#000000', 
                                    'fillOpacity': 0.1, 
                                    'weight': 0.1}
            highlight_function = lambda x: {'fillColor': '#000000', 
                                            'color':'#000000', 
                                            'fillOpacity': 0.50, 
                                            'weight': 0.1}
            NIL = folium.features.GeoJson(
                geo_conc,
                style_function=style_function, 
                control=False,
                highlight_function=highlight_function, 
                tooltip=folium.features.GeoJsonTooltip(
                    fields=['gridcode', 'conc'],
                    aliases=['Grid ID: ', f'농도({unit_k}): '],
                    style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"), 
                    sticky=True,
                )
            )
            m.add_child(NIL)
            m.keep_in_front(NIL)
            print(f'GeoJson 지도(마우스 오버 툴팁 지도)를 추가하였습니다. ')
            self.append_text(f'>> GeoJson 지도(마우스 오버 툴팁 지도)를 추가하였습니다. ')
            
            pbar_value += step_value; self.progressBar[0].setProperty("value", pbar_value)
            
            self.append_text(f'지도 파일을 생성하고 있습니다...')
            
            # add map scroll function
            plugins.MousePosition().add_to(m)

            """
            # 지도에 원하는 변수 이름 나오게 설정
            choropleth.geojson.add_child(
                folium.features.GeoJsonTooltip(['tooltip1'], labels=False)
            )
            """
            
            # 지도의 제목 추가
            title_html = f'<center><h4 style="font-size:16px"><b>{i+1} {time_k} 후 화학사고 모형 결과 - {media_k}</b></h4></center>'
            m.get_root().html.add_child(folium.Element(title_html))
            folium.LayerControl().add_to(m)

            # 맵 m을  html file로 저장합니다.
            if (i+1) < 10: 
                m.save(f'{folder}conc_map_0{i+1}.html')
                print(f'지도 파일 conc_map_0{i+1}.html을 성공적으로 생성하였습니다.')
                self.append_text(f'>> 지도 파일 conc_map_0{i+1}.html을 성공적으로 생성하였습니다.')
            else: 
                m.save(f'{folder}conc_map_{i+1}.html')
                print(f'지도 파일 conc_map_{i+1}.html을 성공적으로 생성하였습니다.')
                self.append_text(f'>> 지도 파일 conc_map_{i+1}.html을 성공적으로 생성하였습니다.')

            pbar_value += step_value; self.progressBar[0].setProperty("value", pbar_value)
            
        # home.html 생성
        html_text = """
            <!DOCTYPE html>
            <html>
            <head>
            <title>Chemical Accident: Concentration Map</title>
            </head>

            <frameset rows="105,*" frameborder="0" border="0" framespacing="0">
                <frame name="menu" src="menu.html" marginheight="0" marginwidth="0" scrolling="auto" noresize>
                <frame name="content" src="conc_map_01.html" marginheight="0" marginwidth="0" scrolling="auto" noresize>

            <noframes>
            <p>This section (everything between the 'noframes' tags) will only be displayed if the users' browser doesn't support frames. You can provide a link to a non-frames version of the website here. Feel free to use HTML tags within this section.</p>
            </noframes>

            </frameset>
            </html>
        """
        with open(f'{folder}home.html', 'w') as html_file:
            html_file.write(html_text)

        # menu.html 생성
        html_text_01 = """
            <!DOCTYPE html>
            <html>
            <head>
            <title>HTML Frames Example - Menu 1</title>
            <style type="text/css">
            body {
                font-family:verdana,arial,sans-serif;
                font-size:10pt;
                margin:10px;
                background-color:#dddfdb;
                }
            </style>
            </head>
            <body>
        """
        
        address_acc = self.getAddressWithShpFile()[0]
        html_text_02 = f'<center><h3 style="font-size:20px">화학사고 지점: {address_acc}</h3></center>\n'
                
        html_text_03 = """
                <style type="text/css">
                    table.example1 {background-color:transparent;border-collapse:collapse;}
                    table.example1 td {border:1px solid black;padding:10px;}
                </style>
                <center>
                <table>
                    
                        <tr>
                            <td style="font-size:16px"><b>사고 후 경과 시간: </b></td>\n
                            <td style="font-size:16px">
        """
        
        html_text_04 = ""
        for i in range(0, map_frames):
            if (i+1) < 10:
                html_text_04 += f'    <b><a href=conc_map_0{i+1}.html target=content>[{i+1}{time_k}]</a></b>   \n'
            else:
                html_text_04 += f'    <b><a href=conc_map_{i+1}.html target=content>[{i+1}{time_k}]</a></b>   \n'                   

        html_text_05 = """
                            </td>
                        </tr>
                    
                </table>
                </center>

            </body>
            </html>
        """
        html_text = html_text_01 + html_text_02 + html_text_03 + html_text_04 + html_text_05
        with open(f'{folder}menu.html', 'w') as html_file:
            html_file.write(html_text)
            
        self.append_text(f'\n  화학사고 모형 결과 지도 파일이 완성되었습니다. \n\n  지도 파일을 불러옵니다. \n')

        # webview web browser window 생성
        # window = webview.create_window('모형 결과 지도 보기', f'{folder}home.html', width=1024, height=680)
        # webview web browser window 시작
        #webview.start(gui='qt')
        
        # HTML 파일을 웹브라우저로 열기
        webbrowser.open_new_tab(f'{folder}home.html')

    def get_concmax_timeframe(self, conc):
        # conc(22500, timeframe) np array에서 격자별(22500) 최대값과 최대값의 시간 뽑아내기
        
        max_time = np.argmax(conc, axis=1)    # axis=1 : 22500 격자별(array 가로) time별 농도값 중 최대값 위치(time)
        concmax_time = np.zeros((22500, 2))
        i = 0 
        for time in max_time:
            concmax_time[i][0] = conc[i][time]   # 해당 격자의 최대 농도
            concmax_time[i][1] = time            # 해당 격자의 최대 농도가 나타난 시간
            i += 1 
        
        # np.savetxt('concmax_time_1st.csv', concmax_time, delimiter=',')
        
        return concmax_time
            
    def view_conc_max_on_map(self, media, interval):
        # 농도 최대값을 뽑아서 지도에 보여주기
        
        hue = ['BuPu', 'YlGn', 'PuRd', 'OrRd', 'YlGnBu']
        
        self.append_text(f'\n####################################')
        self.append_text(f'화학사고 모형 결과 지도 생성을 시작합니다...')

        # 해당 메체와 시간 간격에 대한 농도 자료 가져오기: 형식 - dataframe['CELLID', 'conc']
        conc = self.get_grid_data_all(media, interval)
        
        # 해당 메체와 시간 간격에 대한 농도 자료 중 최대값과 해당 시간
        conc_max = self.get_concmax_timeframe(conc)
        print(conc_max)
        
        time_frames = 1    # 최대 농도값
        
        ### conversion shape file to geojson by geopandas. 
        shp_file = self.getAddressWithShpFile()[1]
        geo_data = gpd.read_file(shp_file, encoding='utf-8')    # EPSG:5186 (UTM 좌표)
        geo_data = geo_data.to_crs("EPSG:4326")                 # EPSG:4326 (경위도 좌표로 변환; geopandas table 내 geometry column의 좌표가 변환됨)

        print(f'shp_file: {shp_file}')
        print(geo_data.head())
        
        self.progressBar[0].setProperty("value", 5)
        
        # CELLID(QGIS) 또는 gridcode(ArcGIS)와 geometry(polygon) 추출
        if shp_file == 'c:/CAM_test/GIS_DB/QGIS/moved_vector.shp':
            geo_data1 = geo_data[['CELLID', 'geometry']]
        else:
            geo_data1 = geo_data[['gridcode', 'geometry']]
        
        geo_data1.columns = ['gridcode', 'geometry'] # geopandas column name change
        print('geo_data1')
        print(geo_data1.head())

        # modeling region 전체 중심점 x, y 좌표 찾기. 지도 표시할 때 중심으로 활용함.
        center_x = geo_data1.centroid.x.mean()
        center_y = geo_data1.centroid.y.mean()
        center = [center_y, center_x]       # shp -> geojson 경위도 좌표로 변환시 long, lati가 되므로 x, y를 바꿔준다.(이유는 TM 좌표가 경도에 해당하는 것이 x, 위도에 해당하는 것이 y임)
        print(f'중심점 좌표: ({center_y},{center_x})')
        
        # 22500개 Grid cell의 중심점 x(경도), y(위도) 좌표에 주소 정보 추가: 단점은 주소 정보에 추가에 시간이 많이 걸린다. 일단 보류 중 
        geo_center = pd.DataFrame(np.vstack([geo_data1.gridcode, geo_data1.centroid.x, geo_data1.centroid.y]).T, columns=['gridcode', 'x', 'y'])
        geo_center = geo_center.astype({'gridcode':'int'})    # gridcode 속성을 int로 변경
        geo_center['address'] = self.getAddressWithShpFile()[0]
        """
        # geo_center의 cell의 중심점 x(경도), y(위도) 좌표에 해당하는 주소 불러와서 address column에 저장
        for i in range(0, geo_center.shape[0]):
            geo_center.loc[i,'address'] = ga.get_address(geo_center.iloc[i]['x'], geo_center.iloc[i]['y'])
        """        
        print(geo_center.head())
        self.append_text(f'사고 지점의 모형 지도를 불러왔습니다.')
        self.progressBar[0].setProperty("value", 10)

        # html folder의 파일 지우기
        def DeleteAllFiles(filePath):
            if os.path.exists(filePath):
                for file in os.scandir(filePath):
                    os.remove(file.path)
                return 'Removed All Files'
        
        DeleteAllFiles(folder)
        
        media_k = '대기' if media == 'Air' else '토양'
        unit_k = 'ug/m3' if media == 'Air' else 'ug/kg'
        time_k = '시간' if interval == '1hour_interval' else '분'
        
        map_frames = time_frames if time_frames < 10 else 10
        
        step_value = round((90 / map_frames) / 5, 0)
        pbar_value = 10

        for i in range(0, map_frames):

            # i 시간에 해당하는 농도 data 불러오기. 시간/분 단위 농도 data(22500 grid data)
            df = self.get_concmax_time_data(conc_max)
            print(f'\n{media_k} 매체의 농도 최대값 자료를 가져왔습니다. ')
            # star = '*' * (i+1)
            # self.append_text(f'\n{star}')
            self.append_text(f'{media_k} 매체의 농도 최대값 자료를 가져왔습니다. ')
            
            # geojson 파일에 df data를 merge(CELLID를 기반으로)
            geo_conc= geo_data1.merge(df, on='gridcode')
            print(geo_conc.head())
            print(f'{media_k} 매체의 농도 최대값 자료를 지도에 병합하였습니다.  ')
            self.append_text(f'>> {media_k} 매체의 농도 최대값 자료를 지도에 병합하였습니다.  ')
            
            pbar_value += step_value; self.progressBar[0].setProperty("value", pbar_value)
            
            # 맵이 center 에 위치하고, zoom 레벨은 11로 시작하는 맵 m을 만듭니다. cartodbpositron 지도를 기본으로 지도 생성
            m = folium.Map(location=center, zoom_start=12, tiles='openstreetmap')
            
            # 'stamenwatercolor', 'cartodbpositron', 'openstreetmap', 'stamenterrain' 네 개의 기본 지도를 지도에 추가. layer control에 들어간다.
            tiles = ['openstreetmap', 'stamenwatercolor', 'cartodbpositron', 'stamenterrain']
            for tile in tiles:
                folium.TileLayer(tile).add_to(m)
                
            print(f'기본 배경 지도를 생성하였습니다. ')
            self.append_text(f'>> 기본 배경 지도를 생성하였습니다. ')
            
            pbar_value += step_value; self.progressBar[0].setProperty("value", pbar_value)
            
            # Choropleth 레이어를 만들고, 맵 m에 추가합니다.
            self.append_text(f'Choropleth 지도(농도 표시한 지도)를 생성하고 있습니다... ')
            
            # geo_conc의 conc 열의 값의 구간별 scale 적용. 구간별 다른 색상을 적용하기 위함. threshhold_scale에 할당. 
            # bins의 구간과 동일하게 되어야 함. 10개를 넘어가니, Diverging Color Scale만 됨
            # Color 참고: https://github.com/python-visualization/folium/issues/403
            # Diverging Color : Spectral, RdYlGn, RdYlBu, RdGy, RdBu, PuOr, PRGn, PiYG, BrBG
            # Sequential Color - Multi-hue: BuPu, YlGn, PuRd, OrRd, YlGnBu
            # myscale = (geo_conc['conc'].quantile((0.0, 0.0000000001, 0.000000001, 0.00000001, 0.0000001, 0.000001, 0.00001, 0.0001, 0.001))).tolist()
            myscale = (geo_conc['conc'].quantile((0.0, 0.0000000001, 0.000000001, 0.00000001, 0.0000001, 0.000001, 0.00001, 0.0001, 0.001, 0.01, 0.1))).tolist()
            print(f'myscale: {myscale}')
            
            # myscale = (geo_conc['conc'].quantile((0.0, 0.0000000001, 0.000000001, 0.0000001, 0.00001, 0.001))).tolist()
            # myscale = (geo_conc['conc'].quantile((0.0000000001, 0.000000001, 0.0000001, 0.00001, 0.001, 0.1))).tolist()
            
            choropleth = folium.Choropleth(
                geo_data=geo_conc,
                name=f'모형 결과 - {media_k}',  # 지도 위에 출력된 그림의 이름. layer control할 때 사용함.
                data=geo_conc,
                columns=['gridcode', 'conc'],
                key_on='feature.properties.gridcode',
                fill_color='Spectral_r',   # 'PuRd' 'YlOrRd' 'RdBu_r'
                fill_opacity=0.5,
                line_color='#ffffff',
                line_opacity=0.01,
                line_weight=0,
                smooth_factor=0,
                legend_name=f'{media_k} 중 농도({unit_k}l)',
                # threshhold_scale=myscale,
                # bins=[0.0, 0.0000000001, 0.000000001, 0.00000001, 0.0000001, 0.000001, 0.00001, 0.0001, 0.001], # color bar 구간과 색 적용
                # bins=[0.0, 0.0000000001, 0.000000001, 0.00000001, 0.0000001, 0.000001, 0.00001, 0.0001, 0.001, 0.01, 0.1], # color bar 구간과 색 적용
                # bins=[0, 20, 40, 60, 80, 100]
            ).add_to(m)
            print(f'Choropleth 지도(농도 표시한 지도)를 추가하였습니다. ')
            self.append_text(f'>> Choropleth 지도(농도 표시한 지도)를 추가하였습니다. ')
            
            pbar_value += step_value; self.progressBar[0].setProperty("value", pbar_value)
            
            self.append_text(f'GeoJson 지도(마우스 오버 툴팁 지도)를 생성하고 있습니다... ')
            
            style_function = lambda x: {'fillColor': '#ffffff', 
                                    'color':'#000000', 
                                    'fillOpacity': 0.1, 
                                    'weight': 0.1}
            highlight_function = lambda x: {'fillColor': '#000000', 
                                            'color':'#000000', 
                                            'fillOpacity': 0.50, 
                                            'weight': 0.1}
            NIL = folium.features.GeoJson(
                geo_conc,
                style_function=style_function, 
                control=False,
                highlight_function=highlight_function, 
                tooltip=folium.features.GeoJsonTooltip(
                    fields=['gridcode', 'time', 'conc'],
                    aliases=['격자 번호: ', f'최대값 표출시간({time_k}): ', f'최대값 농도({unit_k}): '],
                    style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"), 
                    sticky=True,
                )
            )
            m.add_child(NIL)
            m.keep_in_front(NIL)
            print(f'GeoJson 지도(마우스 오버 툴팁 지도)를 추가하였습니다. ')
            self.append_text(f'>> GeoJson 지도(마우스 오버 툴팁 지도)를 추가하였습니다. ')
            
            pbar_value += step_value; self.progressBar[0].setProperty("value", pbar_value)
            
            self.append_text(f'지도 파일을 생성하고 있습니다...')
            
            # add map scroll function
            plugins.MousePosition().add_to(m)

            """
            # 지도에 원하는 변수 이름 나오게 설정
            choropleth.geojson.add_child(
                folium.features.GeoJsonTooltip(['tooltip1'], labels=False)
            )
            """
            
            # 지도의 제목 추가
            title_html = f'<center><h4 style="font-size:16px"><b>[화학사고 모형 시뮬레이션] {media_k} 매체 {time_k} 단위 결과 - 격자별 농도 최대값</b></h4></center>'
            m.get_root().html.add_child(folium.Element(title_html))
            folium.LayerControl().add_to(m)

            # 맵 m을  html file로 저장합니다.
            if (i+1) < 10: 
                m.save(f'{folder}conc_map_0{i+1}.html')
                print(f'지도 파일 conc_map_0{i+1}.html을 성공적으로 생성하였습니다.')
                self.append_text(f'>> 지도 파일 conc_map_0{i+1}.html을 성공적으로 생성하였습니다.')
            else: 
                m.save(f'{folder}conc_map_{i+1}.html')
                print(f'지도 파일 conc_map_{i+1}.html을 성공적으로 생성하였습니다.')
                self.append_text(f'>> 지도 파일 conc_map_{i+1}.html을 성공적으로 생성하였습니다.')

            pbar_value += step_value; self.progressBar[0].setProperty("value", pbar_value)
            
        # home.html 생성
        html_text = """
            <!DOCTYPE html>
            <html>
            <head>
            <title>Chemical Accident: Concentration Map</title>
            </head>

            <frameset rows="65,*" frameborder="0" border="0" framespacing="0">
                <frame name="menu" src="menu.html" marginheight="0" marginwidth="0" scrolling="auto" noresize>
                <frame name="content" src="conc_map_01.html" marginheight="0" marginwidth="0" scrolling="auto" noresize>

            <noframes>
            <p>This section (everything between the 'noframes' tags) will only be displayed if the users' browser doesn't support frames. You can provide a link to a non-frames version of the website here. Feel free to use HTML tags within this section.</p>
            </noframes>

            </frameset>
            </html>
        """
        with open(f'{folder}home.html', 'w') as html_file:
            html_file.write(html_text)

        # menu.html 생성
        html_text_01 = """
            <!DOCTYPE html>
            <html>
            <head>
            <title>HTML Frames Example - Menu 1</title>
            <style type="text/css">
            body {
                font-family:verdana,arial,sans-serif;
                font-size:10pt;
                margin:10px;
                background-color:#dddfdb;
                }
            </style>
            </head>
            <body>
        """
        
        address_acc = self.getAddressWithShpFile()[0]
        html_text_02 = f'<center><h3 style="font-size:20px">화학사고 지점: {address_acc}</h3></center>\n'
                
        html_text_03 = """
                <style type="text/css">
                    table.example1 {background-color:transparent;border-collapse:collapse;}
                    table.example1 td {border:1px solid black;padding:10px;}
                </style>
                

            </body>
            </html>
        """
        html_text = html_text_01 + html_text_02 + html_text_03 
        with open(f'{folder}menu.html', 'w') as html_file:
            html_file.write(html_text)
            
        self.append_text(f'\n  화학사고 모형 결과 지도 파일이 완성되었습니다. \n\n  지도 파일을 불러옵니다. \n')

        # webview web browser window 생성
        # window = webview.create_window('모형 결과 지도 보기', f'{folder}home.html', width=1024, height=680)
        # webview web browser window 시작
        #webview.start(gui='qt')
        
        # HTML 파일을 웹브라우저로 열기
        webbrowser.open_new_tab(f'{folder}home.html')

    def sClickMethod(self):
        
        # button[0] 비활성화
        self.button[0].setEnabled(False)
        
        self.progressBar[0].setVisible(True)
        
        # 검색 버튼 click event
        slmedia = ""
        sltint = ""
        sldatatype = ""

        # self.progressBar[0].setFormat('지도 제작 진행률')
        self.progressBar[0].setProperty("value", 0)
        self.progressBar[0].setAlignment(Qt.AlignCenter)
        
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
                datatype_temp = crbtn.text()
                
                if datatype_temp == '격자별 최대 농도': sldatatype = 'conc_max' ; self.datatype = 'conc_max'
                else: sldatatype = 'conc_all' ; self.datatype = 'conc_all'
                break

        
        slmedia_k = '대기' if slmedia == 'Air' else '토양'
        sltint_k = '1시간 간격' if sltint == '1hour_interval' else '1분 간격'
        
        print(f'{slmedia_k} 매체에 대한 {sltint_k} 모형 시뮬레이션 결과를 선택하였습니다. ')        
        self.append_text(f'{slmedia_k} 매체에 대한 {sltint_k} 모형 시뮬레이션 결과를 선택하였습니다. ')        
        
        if sldatatype == 'conc_max':
            self.view_conc_max_on_map(slmedia, sltint)
        else:
            self.view_results_on_map(slmedia, sltint)
        
        # button[0] 활성화
        self.button[0].setEnabled(True)

        self.progressBar[0].setProperty("value", 0)
        self.progressBar[0].setVisible(False)

def main():
    argument = sys.argv
    
    app = QApplication(argument)
    
    del argument[0]			# 첫번째 인자는 self_filename.py 즉 실행시킨 파일명이 되기 때문에 지운다
    
    main = Window(argument[0], argument[1])
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()