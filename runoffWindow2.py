### ArcGIS pro Library를 이용한 사고지역 공간정보·기상 불러오기 & Runoff 산정 ###
# 1. 주소와 시작 연도 선택하여 강우유출량산정 시작
# 2. insertJusoData(dSql, iSql): 선택된 사고지점에 대한 simulation 정보 입력
# 3. calculate_runoff(): 강우 유출량 산정 시작 함수
#    1) [외부함수] gm.moving_from_origin(self.selAddress): 모델링 격자를 사고 지점으로 이동
#    2) [내부함수] processing_raster_data(point_moved): 격자 이동한 모델링 격자에 필요한 GIS DB 추출
#    3) [외부함수] fd.makeFlowDirection(): 모델링 격자 내부 강우 흐름 방향 계산
#    4) [내부함수] met_data_processing(): 기상 자료 처리
#    5) [내부함수] calculate_s_runoff(): Solid Runoff 산정
#    6) [내부함수] calculate_w_runoff(): Water Runoff 산정
##############################################################################

import arcpy
from arcpy import env
from arcpy.sa import *
import os
import shutil
import sqlite3
#import sys
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
import q_calculate_grid_move as gm
import q_flow_direction as fd

class ThreadClass(QtCore.QThread): 

    def __init__(self, parent = None): 
        super(ThreadClass,self).__init__(parent)

    def run(self): 
        print('Thread start')

class SecondWindow(QWidget):
    def __init__(self, alist):
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
        self.progressBar = []

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
        self.setWindowTitle('강우 유출량 산정')

        # Window 위치와 사이즈: (x, y, width, height)
        self.setGeometry(300, 100, 700, 400)
        
        self.progressBar[0].setVisible(False)

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
        
        # if ((year % 4 == 0 and year % 100 != 0) or year % 400 == 0) and month > 2: 
        #    answer = answer + 1 
        
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

        pushbutton = QPushButton('강우 유출량 산정')
        pushbutton.clicked.connect(self.on_clicked)
        self.button.append(pushbutton)

        # 전체용 progressBar
        pbar0 = QProgressBar()
        pbar0.setGeometry(30, 30, 230, 25)
        self.progressBar.append(pbar0)
        
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
        vbox.addWidget(pbar0)
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

    # 강우 유출량 산정
    
    def calculate_runoff(self):
        self.threadclass.start()

        self.progressBar[0].setProperty("value", 0)
        self.progressBar[0].setAlignment(Qt.AlignCenter)

        point_moved = gm.moving_from_origin(self.selAddress)
        self.append_text('사고지점(' + self.selAddress + ')을 중앙으로하여 모델링 격자를 생성하였습니다.')
        # self.append_text(str(point_moved[0]) + ', ' + str(point_moved[1]))

        sleep(1)
        self.progressBar[0].setProperty("value", 10)

        self.append_text('모델링 격자에 해당하는 GIS 정보 추출 중...')

        self.processing_raster_data(point_moved)
        
        self.append_text('모델링 격자에 해당하는 GIS 정보를 성공적으로 추출하였습니다.')

        sleep(1)
        self.progressBar[0].setProperty("value", 30)

        fd.makeFlowDirection()

        self.append_text('모델링 격자간 강우 흐름 정보를 성공적으로 추출하였습니다.')
        
        sleep(1)
        self.progressBar[0].setProperty("value", 40)

        self.append_text('모델링 격자에 해당하는 강우유출량 산정용 변수 정보 추출 중...')

        self.met_data_processing()

        self.append_text('모델링 격자에 해당하는 강우유출량 산정용 변수 정보를 성공적으로 추출하였습니다.')

        sleep(1)
        self.progressBar[0].setProperty("value", 50)
        
        self.calculate_s_runoff()

        sleep(1)
        self.progressBar[0].setProperty("value", 75)

        self.calculate_w_runoff()

        self.progressBar[0].setProperty("value", 100)

        """
        for i in range(10, 110, 10):
            self.progressBar[0].setProperty("value", i)

            completed1 = 0.001
            while completed1 < 100:
                self.progressBar[1].setProperty("value", completed1)
                #self.progressBar[0].setText(str(completed))
                sleep(0.005)
                completed1 += 0.5
        """

    ######################################################################
    ### Processing Raster Data
    def processing_raster_data(self, grid_move):

        print("\n" + "-"*100)
        print("\n" + "### Getting GIS Data for preparing modeling input data ###")

        self.append_text("GIS 데이터 처리를 시작합니다.")
        
        # env.workspace = "c:/CAM_test/GIS_DB/MyProject/MyProject.gdb"

        ######################################################################
        ### 100m * 100m grid 이동 변수
        # calculate_grid_move.py를 import하여 moving_from_origin function을 사용
        # return 되는 list[0]이 x 좌표 이동값, list[1]이 y 좌표 이동값, 
        # sample address = "대전광역시 대덕구 상서로 20"

        # 매개변수가 몇 개인지 확인하여 한 줄의 주소 텍스트로 만듬.
        #address = js.findAddress()

        #grid_move = gm.moving_from_origin(address)
        #print("\n" + "-"*100 + "\n")    

        ######################################################################
        ### 중간 작업용 Raster Data가 생성되는 폴더 내 파일을 모두 지움
        rasterFilePath = "c:/CAM_test/GIS_DB/MyProject/raster"
        polygonFilePath = "c:/CAM_test/GIS_DB/MyProject/MyProject.gdb"
        print(self.remove_makeDir(rasterFilePath))

        rasterSourcePath = "c:/CAM_test/GIS_DB/Korea"

        ######################################################################
        # 기본 100 * 100 shape(Feature)를 Raster(100m*100m)로 변환
        print("Converting the features of domain to raster grids...")
        arcpy.FeatureToRaster_conversion(polygonFilePath + '/grid_100_v2', 'CELLID', rasterFilePath + '/grid_def', 100)
        print(">> The features to Raster is successfully converted.\n")

        ######################################################################
        # Raster의 이동(모델링 지점으로) +값은 x, y축의 오른쪽과 위로 이동, -값은 x, y축의 왼쪽과 아래쪽으로 이동
        # 이동 전 Grid CenterX: 423979.692659  CenterY: 334581.766996
        maskRaster = rasterFilePath + '/move_100by100'

        print("Moving raster grids to the modeling point...")
        arcpy.Shift_management(rasterFilePath + '/grid_def', maskRaster, str(grid_move[0]), str(grid_move[1]))
        #arcpy.Shift_management(rasterFilePath + '/grid_def', rasterFilePath + '/move_100by100', "-10000", "10000")
        print(">> The raster grids to the modeling point is successfully completed.\n")

        self.append_text("화학사고 지점에 대한 모델링 Grid를 생성하였습니다.")
        
        ######################################################################
        # 모델링 지점으로 이동한 raster를 polygon으로 conversion. 나중에 지도 위에 모델링 결과 보기 기능에 사용(folium).
        outputPolygon = 'c:/CAM_test/GIS_DB/MyProject/raster/grid_now.shp'
        field = "VALUE"  # raster의 grid value column
        arcpy.RasterToPolygon_conversion(maskRaster, outputPolygon, "NO_SIMPLIFY", field)
                
        self.progressBar[0].setProperty("value", 12)

        ######################################################################
        # Extract by Mask: 100by100_on Raster의 영역에 해당하는 Grid Data(DEM, K, Slope etc) 추출
        # 100미터 단위로 이동하지만 dem raster grid와 어긋낫 수 있으므로 polygon으로 변환함(polygon 개수는 22500개보다 훨씬 많음)
        # gridcode에 원하는 정보가 저장되어 있으며, 생성된 polygon을 mask raster grid cell size로 하여 
        # raster로 conversion하면 22500개 grid cell을 얻을 수 있음

        # 이 때 RasterToPolygon_conversion 함수는 Integer Raster만 입력변수로 가능함
        # (DEM, SL, SP, K의 경우 소수점이 있는 value이므로 conversion 전 10000을 곱했다가 conversion 후 10000으로 나눠줌)
        # mask raster grid cell에 제일 많은 면적을 차지하는 gridcode를 raster grid에 할당
        
        # [22500 grid cell size raster 생성]
        
        # (DEM: elevation) --------------------------------------------------------------------------
        print("Extracting elevation data about the modeling region...")
        
        # a. extract raster
        demByMask = ExtractByMask(rasterSourcePath +'/DEM_100', maskRaster)
        
        # b. (raster*1000) to polygon conversion
        intDemMasked = Int(demByMask * 10000)   # raster: float -> int
        outElPolygon = rasterFilePath + '/el_polygon_100.shp'
        arcpy.RasterToPolygon_conversion(intDemMasked, outElPolygon, "NO_SIMPLIFY", "VALUE")
        
        # c. polygon to raster conversion
        arcpy.PolygonToRaster_conversion(outElPolygon, "gridcode", rasterFilePath + '/el_mask_temp', "MAXIMUM_AREA", "NONE", maskRaster)
        
        # d. (raster/1000) and save
        el_mask = Raster(rasterFilePath + '/el_mask_temp') / 10000
        el_mask.save(rasterFilePath + '/el_mask')

        print(">> The elevation data is successfully extracted.\n")
        self.append_text("모델링 대상 지역에 대한 수치고도 자료를 추출하였습니다.")
        self.progressBar[0].setProperty("value", 14)

        # (Landuse)  --------------------------------------------------------------------------
        print("Extracting landuse data about the modeling region...")

        # a. extract raster
        luByMask = ExtractByMask(rasterSourcePath +'/lu_100_add_3', maskRaster)
        
        # b. (raster) to polygon conversion. landuse는 integer이므로 10000을 곱하고 나누는 것은 생략함
        outLuPolygon = rasterFilePath + '/lu_polygon_100.shp'
        arcpy.RasterToPolygon_conversion(luByMask, outLuPolygon, "NO_SIMPLIFY", "VALUE")

        # c. polygon to raster conversion and save
        arcpy.PolygonToRaster_conversion(outLuPolygon, "gridcode", rasterFilePath + '/lu_mask', "MAXIMUM_AREA", "NONE", maskRaster)
        
        print(">> The landuse data is successfully extracted.\n")
        self.append_text("모델링 대상 지역에 대한 토지피복도 자료를 추출하였습니다.")
        self.progressBar[0].setProperty("value", 16)

        # (Slope Length)  --------------------------------------------------------------------------
        print("Extracting slope length data about the modeling region...")

        # a. extract raster
        slByMask = ExtractByMask(rasterSourcePath +'/sll_100', maskRaster)

        # b. (raster*1000) to polygon conversion
        intSlMasked = Int(slByMask * 10000)   # raster: float -> int
        outSlPolygon = rasterFilePath + '/sl_polygon_100.shp'
        arcpy.RasterToPolygon_conversion(intSlMasked, outSlPolygon, "NO_SIMPLIFY", "VALUE")

        # c. polygon to raster conversion
        arcpy.PolygonToRaster_conversion(outSlPolygon, "gridcode", rasterFilePath + '/sl_mask_temp', "MAXIMUM_AREA", "NONE", maskRaster)
        
        # d. (raster/1000) and save
        sl_mask = Raster(rasterFilePath + '/sl_mask_temp') / 10000
        sl_mask.save(rasterFilePath + '/sl_mask')

        print(">> The slope length data is successfully extracted.\n")
        self.append_text("모델링 대상 지역에 대한 경사길이 자료를 추출하였습니다.")
        self.progressBar[0].setProperty("value", 18)

        # (Slope Percent) --------------------------------------------------------------------------
        print("Extracting slope percent data about the modeling region...")

        # a. extract raster
        spByMask = ExtractByMask(rasterSourcePath +'/slp_100', maskRaster)

        # b. (raster*1000) to polygon conversion
        intSpMasked = Int(spByMask * 10000)   # raster: float -> int
        outSpPolygon = rasterFilePath + '/sp_polygon_100.shp'
        arcpy.RasterToPolygon_conversion(intSpMasked, outSpPolygon, "NO_SIMPLIFY", "VALUE")

        # c. polygon to raster conversion
        arcpy.PolygonToRaster_conversion(outSpPolygon, "gridcode", rasterFilePath + '/sp_mask_temp', "MAXIMUM_AREA", "NONE", maskRaster)
        
        # d. (raster/1000) and save
        sp_mask = Raster(rasterFilePath + '/sp_mask_temp') / 10000
        sp_mask.save(rasterFilePath + '/sp_mask')

        print(">> The slope percent data is successfully extracted.\n")
        self.append_text("모델링 대상 지역에 대한 Slope percent 자료를 추출하였습니다.")
        self.progressBar[0].setProperty("value", 20)

        # ( K ) --------------------------------------------------------------------------
        print("Extracting K data about the modeling region...")

        # a. extract raster
        kByMask = ExtractByMask(rasterSourcePath +'/kvalue_100', maskRaster)

        # b. (raster*1000) to polygon conversion
        intKvMasked = Int(kByMask * 10000)   # raster: float -> int
        outKvPolygon = rasterFilePath + '/k_polygon_100.shp'
        arcpy.RasterToPolygon_conversion(intKvMasked, outKvPolygon, "NO_SIMPLIFY", "VALUE")

        # c. polygon to raster conversion
        arcpy.PolygonToRaster_conversion(outKvPolygon, "gridcode", rasterFilePath + '/k_mask_temp', "MAXIMUM_AREA", "NONE", maskRaster)
        
        # d. (raster/1000) and save
        k_mask = Raster(rasterFilePath + '/k_mask_temp') / 10000
        k_mask.save(rasterFilePath + '/k_mask')

        print(">> The K data is successfully extracted.\n")
        self.append_text("모델링 대상 지역에 대한 K 자료를 추출하였습니다.")
        self.progressBar[0].setProperty("value", 22)

        ######################################################################
        # RasterToNumPyArray
        print("\n" + "-"*100)
        print("Calculating runoff parameters about the modeling region...\n")

            # grid no.
        grid_np = np.arange(0, 22500)
        
            # DEM: elevation
        arr_el = arcpy.RasterToNumPyArray(el_mask, nodata_to_value=0)
        print("elevation array structure: {}".format(arr_el.shape))
        el_np1 = arr_el.ravel()
        el_np = np.around(el_np1, 2)   # 소수점 둘째자리로 반올림
        print(">> Elevation data is successfully calculated.\n")

            # Landuse
        arr_landuse = arcpy.RasterToNumPyArray(rasterFilePath + '/lu_mask', nodata_to_value=6)
        print("arr_landuse array structure: {}".format(arr_landuse.shape))
        lu_np = arr_landuse.ravel()
        print(">> Landuse data is successfully calculated.\n")

            # Slope Length
        arr_slopelength = arcpy.RasterToNumPyArray(rasterFilePath + '/sl_mask', nodata_to_value=0)
        sl_np = np.around(arr_slopelength.ravel(), 3) # 소수점 세째자리로 반올림
        print(">> Slope length data is successfully calculated.\n")

            # Slope Percent
        arr_slopepercent = arcpy.RasterToNumPyArray(rasterFilePath + '/sp_mask', nodata_to_value=0.0000000001)
        sp_np2 = arr_slopepercent.ravel()
        sp_np1 = np.where(sp_np2 <= 0.0, 0.0000000001, sp_np2)
        sp_np = np.around(sp_np1, 3) # 소수점 세째자리로 반올림
        print(">> Slope percent is successfully calculated.\n")

            # K
        arr_k = arcpy.RasterToNumPyArray(rasterFilePath + '/k_mask', nodata_to_value=0)
        k_np = np.around(arr_k.ravel(), 2)  # 소수점 둘째자리로 반올림
        print(">> K value data is successfully calculated.\n")

        ######################################################################
        # lu_np * [landuse 대분류] 1: 시가화 건조지역, 2: 농지, 3: 산림지역, 4: 초지, 5: 습지, 6: 나지, 7: 수역
        # 1차 조정
        # lu_np2 * [landuse 대분류 조정] 1: 시가화 건조지역, 2: 농지, 3: 산림지역, 4: 초지, 5->6: 습지, 6: 나지, 7->6: 수역
        # lu_np2 = np.where(lu_np == 7, 6, np.where(lu_np == 5, 6, np.where(lu_np == 6, 6, np.where(lu_np == 4, 4, np.where(lu_np == 3, 3, np.where(lu_np == 2, 2, 1))))))   
        ## 2차 조정
        # lu_np2 * [landuse 대분류 조정] 0->6:해역  1: 시가화 건조지역, 2: 농지, 3: 산림지역, 4: 초지, 5->6: 습지, 6: 나지, 7->6: 수역
        lu_np2 = np.where(lu_np == 0, 6, np.where(lu_np == 7, 6, np.where(lu_np == 5, 6, np.where(lu_np == 6, 6, np.where(lu_np == 4, 4, np.where(lu_np == 3, 3, np.where(lu_np == 2, 2, 1)))))))   

        ######################################################################
        # DR, C12_2, C3_6, C7_11, P는 landuse, slope length, slope percent value로 계산
        c12_np = np.where(lu_np2 == 6, 1, np.where(lu_np2 == 4, 1, np.where(lu_np2 == 2, 1, 0.001)))
        c03_np = np.where(lu_np2 == 6, 1, np.where(lu_np2 == 2, 1, 0.001))
        c07_np = np.where(lu_np2 == 6, 1, np.where(lu_np2 == 2, 0.3, np.where(lu_np2 == 4, 0.01,0.001)))
        
        cn_np = np.where(lu_np == 7, 81, np.where(lu_np == 6, 86, np.where(lu_np == 4, 69, np.where(lu_np == 3, 60, 98))))   
        
        # sp_np가 0일 때는 0.51 * np.log10(sp_np / 100) 항목을 0으로 적용
        dr_np1 = np.where(sp_np > 0, np.power(10, 4.5 - 0.23 * -2.0 + 0.51 * np.log10(sp_np / 100) - 2.79 * 0.60206), 0)
        # 원래 수식
        # dr_np1 = np.power(10, 4.5 - 0.23 * -2.0 + 0.51 * np.log10(sp_np / 100) - 2.79 * 0.60206)
        dr_np = np.around(dr_np1, 1) # 소수점 첫째자리로 반올림

        p_np_0_7   = np.where(lu_np2 == 6, 0.35, np.where(lu_np2 == 1, 0.01, np.where(lu_np2 == 4, 0.10, np.where(lu_np2 == 3, 0.55, 0.1))))   
        p_np_7_11  = np.where(lu_np2 == 6, 0.60, np.where(lu_np2 == 1, 0.01, np.where(lu_np2 == 4, 0.12, np.where(lu_np2 == 3, 0.60, 0.1))))   
        p_np_11_17 = np.where(lu_np2 == 6, 0.80, np.where(lu_np2 == 1, 0.01, np.where(lu_np2 == 4, 0.16, np.where(lu_np2 == 3, 0.80, 0.1))))   
        p_np_17_26 = np.where(lu_np2 == 6, 0.90, np.where(lu_np2 == 1, 0.01, np.where(lu_np2 == 4, 0.18, np.where(lu_np2 == 3, 0.90, 0.1))))   
        p_np_26_   = np.where(lu_np2 == 6, 1.00, np.where(lu_np2 == 1, 0.01, np.where(lu_np2 == 4, 0.20, np.where(lu_np2 == 3, 1.00, 0.1))))   

        p_np = p_np_26_
        i = 0
        for sp in sp_np2:
            if sp >= 0 and sp < 7.0:
                p_np[i] = p_np_0_7[i]
            elif sp >= 7.0 and sp < 11.3:
                p_np[i] = p_np_7_11[i]
            elif sp >= 11.3 and sp < 17.6:
                p_np[i] = p_np_11_17[i]
            elif sp >= 17.6 and sp < 26.8:
                p_np[i] = p_np_17_26[i]

            i += 1

        print(">> DR, C, P and CN data about the modeling region is successfully calculated.\n")
        
        self.append_text("모델링 대상 지역에 대한 GIS 자료를 추출하여 변수로 할당하였습니다.")
        self.progressBar[0].setProperty("value", 24)
        
        ######################################################################
        # grid_param을 구성하는 변수에 대한 numpy array를 합쳐서 테이블과 같은 형식으로 만들기
        # landuse 5와 7 값을 그대로 저장한 numpy array로 grid_param 생성

        # 가로로 구성된 np array를 연결
        g1_0 = np.concatenate((grid_np, el_np), axis=0)
        g2_0 = np.concatenate((g1_0, lu_np), axis=0)
        g3_0 = np.concatenate((g2_0, sl_np), axis=0)
        g4_0 = np.concatenate((g3_0, sp_np), axis=0)
        g5_0 = np.concatenate((g4_0, dr_np), axis=0)

        g6_0 = np.concatenate((g5_0, c12_np), axis=0)
        g7_0 = np.concatenate((g6_0, c03_np), axis=0)
        g8_0 = np.concatenate((g7_0, c07_np), axis=0)
        g9_0 = np.concatenate((g8_0, p_np), axis=0)
        g10_0 = np.concatenate((g9_0, cn_np), axis=0)

        g11_0 = np.concatenate((g10_0, k_np), axis=0)

        # grid_param table 구조와 같은 형식으로 
        g12_0 = g11_0.reshape(12, 22500)
        grid_param_0_np = g12_0.transpose()

        #print("grid_param")
        #print(grid_param_np)
        print("grid_param_0 structure: {}".format(grid_param_0_np.shape))

        # grid_param_np numpy to csv
        csv_header = "grid_no, elevation, landuse_0, slope_length, slope_percent, DR, C_12_2, C_3_6, C_7_11, P, CN, K"
        np.savetxt(r'c:\CAM_test\Inputs\db_grid_properties_0.csv', grid_param_0_np, delimiter=",", header=csv_header)

        ######################################################################
        # grid_param을 구성하는 변수에 대한 numpy array를 합쳐서 테이블과 같은 형식으로 만들기
        # landuse 5와 7을 6으로 조정한 numpy array로 grid_param 생성

        # 가로로 구성된 np array를 연결
        g1 = np.concatenate((grid_np, el_np), axis=0)
        g2 = np.concatenate((g1, lu_np2), axis=0)
        #g2 = np.concatenate((g1, lu_np), axis=0)
        g3 = np.concatenate((g2, sl_np), axis=0)
        g4 = np.concatenate((g3, sp_np), axis=0)
        g5 = np.concatenate((g4, dr_np), axis=0)

        g6 = np.concatenate((g5, c12_np), axis=0)
        g7 = np.concatenate((g6, c03_np), axis=0)
        g8 = np.concatenate((g7, c07_np), axis=0)
        g9 = np.concatenate((g8, p_np), axis=0)
        g10 = np.concatenate((g9, cn_np), axis=0)

        g11 = np.concatenate((g10, k_np), axis=0)

        # grid_param table 구조와 같은 형식으로 
        g12 = g11.reshape(12, 22500)
        grid_param_np = g12.transpose()

        #print("grid_param")
        #print(grid_param_np)
        print("grid_param structure: {}".format(grid_param_np.shape))

        ######################################################################
        # SQLite DB에 numpy array data 저장
        conn = sqlite3.connect(r"c:\CAM_test\GIS_DB\db4MMM.db")

        # Connection으로부터 Cursor 생성
        cur = conn.cursor()

        dTable = "grid_param"

        # 기존 records 삭제
        cur.execute("DELETE FROM {}".format(dTable))
        conn.commit()

        # numpy array 변수를 SQLite table에 insert
        # table name: meteo_raw2017, meteo_raw2018, meteo_raw2019, meteo_raw2020
        query = "insert into {} values (:grid_no, :elevation, :landuse, :slope_length, :slope_percent, :DR, :C_12_2, :C_3_6, :C_7_11, :P, :CN, :K)".format(dTable)

        print("\nInserting runoff parameter data about the modeling region to DB...")

        cur.executemany(query, grid_param_np)
        conn.commit()

        print("\nRunoff parameter data about the modeling region is successfully inserted to DB.")
        self.append_text("모델링 대상 지역에 대한 GIS 자료를 DB에 저장하였습니다.")
        self.progressBar[0].setProperty("value", 26)

        # Connection 닫기
        cur.close()
        conn.close()

        ######################################################################
        # grid_param_np numpy to csv
        csv_header = "grid_no, elevation, landuse, slope_length, slope_percent, DR, C_12_2, C_3_6, C_7_11, P, CN, K"
        np.savetxt(r'c:\CAM_test\Inputs\db_grid_properties.csv', grid_param_np, delimiter=",", header=csv_header)

        landuse_avg = np.zeros(1)
        landuse_avg[0] = np.bincount(lu_np2).argmax()
        csv_header = "landuse_most_common"
        np.savetxt(r'c:\CAM_test\Inputs\db_landuse_most_common.csv', landuse_avg, delimiter=",", header=csv_header)

        print("\n" + "-"*100)
        print("\nRunoff parameter data about the modeling region is successfully saved to csv file.")

        self.append_text("모델링 대상 지역에 대한 GIS 자료를 CSV 파일로 저장하였습니다.")
        self.progressBar[0].setProperty("value", 28)

    #############################################################################################
    # Meteological data processing 
    # 파이썬에 switch 기능을 지원하지 않아서 function을 이용하여 dictionary와 유사하게 입력값에 대한 리턴값으로 처리
    def met_city_st(self, x): 
        return {'서울': '서울시', '부산': '부산시', '대구': '대구시', '대전': '대전시', '광주': '광주시', '울산': '울산시', '인천': '인천시', '세종': '세종시' }[x]

    def local_do_st(self, x): 
        return {'충청남도': '충남', '충청북도': '충북', '전라북도': '전북', '전라남도': '전남', '경상북도': '경북', '경상남도': '경남' }[x]

    def met_data_processing(self):

        #############################################################################################
        # sqlite에서 데이터 가져오기: 해당 측정소, 해당 연도 set
        # SQLite DB 연결
        conn = sqlite3.connect(r"c:\CAM_test\GIS_DB\db4MMM.db")

        # Connection으로부터 Cursor 생성
        cur = conn.cursor()

        #############################################################################################
        ### 기상자료를 가져올 측정소 위치와 시작 년도 설정
        ### simulation_info table에서 가져옴
        #sido = "강원"; sigungu = "강릉시"
        #sYear = 2019 # start year: 2017, 2018, 2019만 가능

        sql = "SELECT sido, sigungu, address, s_year FROM simulation_info "
        cur.execute(sql)
        row = cur.fetchone()
        sido1 = row[0]; sigungu = row[1]; sYear = int(row[3])

        if len(sido1) == 4:
            sido = self.local_do_st(sido1)
        else:
            sido = sido1[:2]
        
        if sido == '서울' or sido == '부산' or sido == '대구' or sido == '대전' or sido == '광주' or sido == '인천' or sido == '울산' or sido == '세종':
            sigungu = self.met_city_st(sido)

        # year set(2 years) 만들기
        eYear = sYear + 1
        ylist = list()
        ylist.append(sYear); ylist.append(eYear)
        
        # Delete meteo_runoff records
        cur.execute("DELETE FROM meteo_runoff")
        conn.commit()

        # Yearly Data 가져오기 시작
        nRec = 1  # serial hour number 시작 

        for iYear in ylist:

            # 측정소 code 가져오기 
            # # year가 2019년까지 세종시 데이터는 sigungu 측정소를 '대전시' 측정소를 사용(세종시 측정소가 2019년 중반에 측정 시작함)
            if sido == '세종': 
                if iYear == 2020: 
                    sido1 = '세종'; sigungu1 = '세종시' 
                else:
                    sido1 = '대전'; sigungu1 = '대전시' 
            else:
                sido1 = sido; sigungu1 = sigungu
                
            sql = f"SELECT code1 FROM station WHERE sido = '{sido1}' AND sigungu = '{sigungu1}'"
            print(f'year: {iYear}, sql: {sql}')
            
            cur.execute(sql)
            row = cur.fetchone()
            stNo = int(row[0])  # station code
            
            # data Table 할당
            dTable = "meteo_full" + str(iYear)

            sql = 'SELECT date_time, temp, rain, wind_speed, wind_dir, rh, doc FROM {} WHERE st_no = {};'.format(dTable, stNo)
            cur.execute(sql)

            rows = cur.fetchall()

            print(f"{iYear}의 데이터 갯수: {len(rows)}")

            data = []

            for row in rows:
                data.append(row)

            # numpy 변수에 할당
            metData = np.array(data)

            # self.append_text("\n>> "+"Raw monitoring data structure of {} year (#{} site) is {}.".format(iYear, stNo, metData.shape))

            # self.append_text("\n>> "+"Yearly meteological data of #{} site ({}) is assigned to numpy array.".format(stNo, iYear))

            # 새로운 numpy 변수에 할당
            # metData2 = np.zeros(8760, 11)

            # year, month, day, hour, ltime, temp, rain, windX, windY, rh, doc 용 list 변수
            # SELECT date_time, temp, rain, wind_speed, wind_dir, rh, doc FROM 
            data2 = []  

            # met. data 변환
            self.append_text("{}년 기상자료 데이터 처리중...".format(iYear))

            cum_5d_list = np.zeros(120)
            for rec in metData:
                # 비어 있는 리스트 만들기
                list1 = list()
                
                # 1. date_time >> year, month, day, hour, ltime 변환
                date, time = rec[0].split(" ")[0], rec[0].split(" ")[1]

                year, month, day = int(date.split('-')[0]), int(date.split('-')[1]), int(date.split('-')[2]) 

                hour = int(time.split(":")[0])

                lDate = self.dayOfYear(date)
                lTime = self.timeOfYear(lDate, hour)
                lTime = nRec

                # 2. celcius temp >> absolute temp 변환
                kTemp = float(rec[1]) + 273.15

                # 3. rain은 그대로
                rain = float(rec[2])

                # 4. cum_5d_rain: 과거 5일 강수량 (t-120) ~ (t-0)
                if nRec < 121:
                    cum_5d_list[nRec-1] = rain
                else:
                    cum_5d_list = np.delete(cum_5d_list, 0)
                    cum_5d_list = np.append(cum_5d_list, rain)

                #if lTime % 100 == 1:
                #    print("Time: {}, structure: {}".format(lTime, cum_5d_list.shape))

                cum_5d_rain = sum(cum_5d_list)

                # 5. wind_speed, wind_dir >> wind_x, wind_y 변환
                # wind speed: m/s >> km/hour
                wind_kmh = float(rec[3]) * 3600 / 1000
                wind_rad = radians(float(rec[4]))
                #sin, cos값이 1.010E-16, 1.010E-17 등이면 0.0으로 할당. 90, 180, 270도인 경우 이런 상황 발생. 
                if abs(sin(wind_rad)) > 0.0000000001:
                    windX = wind_kmh * sin(wind_rad)
                else:
                    windX = 0.0

                if abs(cos(wind_rad)) > 0.0000000001:
                    windY = wind_kmh * cos(wind_rad)
                else:
                    windY = 0.0

                # 6. rh는 그대로
                rh = float(rec[5])

                # 7. doc는 그대로
                doc = int(rec[6])

                # np array를 만들기 위한 list1 변수에 데이터 추가
                list1.append(year); list1.append(month); list1.append(day); list1.append(hour); list1.append(lTime)
                list1.append(kTemp); list1.append(rain); list1.append(cum_5d_rain); list1.append(windX); list1.append(windY)
                list1.append(rh); list1.append(doc)

                # np array를 만들기 위한 list1 변수 추가: np
                for i in range(1,2):
                    zValue = 0.0
                    list1.append(zValue)

                data2.append(list1)

                # 시간의 일련번호
                nRec += 1

            # 기상자료를 numpy 변수에 할당
            met_runoff =np.array(data2)  

            """
            # 과거 5일 누적 강수량 계산
            i = 0
            for rec in met_runoff:
                cum_5d_rain = 0.0
                if i >= 121:
                    d5_start = i - 121
                    d5_end = i
                else:
                    d5_start = 0
                    d5_end = i if i > 0 else 1
                d5_range = str(d5_start) + ":" + str(d5_end)

                cum_5d_rain = sum(rec[d5_range,6])
                rec[7] = cum_5d_rain
                i += 1
            """

            # R 계산
            rain_np = met_runoff[:, 6]
            r_np = rain_np * (0.283 * (1 - 0.52 * np.exp(-0.042 * rain_np)) * rain_np)
            met_runoff[:, 12] = r_np


            print("\n>> "+"Data structure of {} year is {}.".format(iYear, met_runoff.shape))
            print("\n>> "+"Meteological data is assigned to numpy array.")

            # numpy array 변수를 SQLite table에 insert
            # table name: meteo_runoff
            print("\n"+"Inserting numpy array data to DB...")

            query = "insert into meteo_runoff values (:year, :month, :day, :hour, :ltime, :temp, :rain, :cum_5d_rain, :windX, :windY, :rh, :doc, :R)"

            cur.executemany(query, met_runoff)
            conn.commit()

        self.append_text("기상자료 데이터를 DB에 성공적으로 업로드하였습니다.")

        ######################################################################
        # met_runoff numpy to csv
        # sv_header = "year, month, day, hour, ltime, temp, rain, windX, windY, rh, doc, R"
        # np.savetxt(r'c:\CAM_test\Inputs\Meteo_data.csv', met_runoff, delimiter=",", header=csv_header)

        # sqlite > pandas > csv
        # 1st meteo_data file: db_meteo_data1.csv
        # year – month – day – hour – ltime – temp – rain – windX – windY – rh – doc - R
        sql = 'SELECT year, month, day, hour, ltime, temp, rain, windX, windY, rh, doc, R FROM meteo_runoff ORDER BY ltime '

        db_df1 = pd.read_sql_query(sql, conn)

        db_df1.to_csv(r'c:\CAM_test\Inputs\db_meteo_data1.csv', index=False)

        # 2nd meteo_data file: db_meteo_data2.csv
        # year – month – day – hour – ltime – cum_5d_rain
        sql = 'SELECT year, month, day, hour, ltime, temp, cum_5d_rain FROM meteo_runoff ORDER BY ltime '

        db_df2 = pd.read_sql_query(sql, conn)

        db_df2.to_csv(r'c:\CAM_test\Inputs\db_meteo_data2.csv', index=False)

        print("\n" + "-"*60)
        self.append_text("기상자료를 CSV 파일로 저장하였습니다.")

        # Connection 닫기
        cur.close()
        conn.close()

        print("\n" + "-"*100)

    ########################################################################################
    # grid_param table의 grid_no별 정보와 meteo_runoff table의 시간별 기상정보를 이용하여 계산
    # SL을 강수량(rain)에 따른 R을 시간별로 호출하여 계산

    def calculate_s_runoff(self):

        self.append_text("### Solid Runoff Rate 산정 ###")

        # ----------------------------------------------------------------------------------
        # SQLite DB 연결
        conn = sqlite3.connect(r"c:\CAM_test\GIS_DB\db4MMM.db")
        cur = conn.cursor()
        
        self.append_text("강우 유출량 산정을 위한 GIS 데이터를 DB에서 가져오는 중입니다...")
        
        sql = 'SELECT * FROM grid_param ORDER BY grid_no '
        cur.execute(sql)
        glist = cur.fetchall()

        grid_data = np.array(glist)

        self.append_text("강우 유출량 산정을 위한 GIS 데이터를 DB에서 성공적으로 가져왔습니다.")
        # self.append_text("\n>> "+"Number of grid data: {}, structure of grid data: {}".format(len(grid_data), grid_data.shape))

        self.append_text("강우 유출량 산정을 위한 기상 데이터를 DB에서 가져오는 중입니다...")
        
        sql = 'SELECT * FROM meteo_runoff ORDER BY ltime '
        cur.execute(sql)
        mlist = cur.fetchall()

        met_data = np.array(mlist)

        self.append_text("강우 유출량 산정을 위한 기상 데이터를 DB에서 성공적으로 가져왔습니다.")
        # self.append_text("\n>> "+"Number of met. data: {}, structure of met. data: {}".format(len(met_data), met_data.shape))
        
        self.append_text("Solid runoff rate 산정을 위한 변수들을 준비 중입니다...")
        
        # u_sro numpy array 변수 생성
        u_sro = np.zeros((22500, len(met_data)), np.float64)
        #print("\n>> "+"Structure of solid runoff rate data: {}\n".format(u_sro.shape))
        
        gn = np.array(grid_data[:,0], dtype=np.int32)
        #print("\n>> "+"Structure of Grid no. data: {}\n".format(gn.shape))

        dr = grid_data[:,5]
        dr_avg = np.mean(dr)
        #print("\n>> "+"Structure of DR data: {}\n".format(dr.shape))
        
        density_soil = 2650.0

        # R: rainfall energy
        r1 = met_data[:, 12]
        r = r1.T
        #print(r)
        #print("\n>> "+"Structure of R data: {}\n".format(r.shape))
        
        k = grid_data[:, 11]
        k_avg = np.mean(k)
        #print("\n>> "+"Structure of K data: {}\n".format(k.shape))
        ls = grid_data[:, 3]
        ls_avg = np.mean(ls)
        #print("\n>> "+"Structure of LS data: {}\n".format(ls.shape))
        c12 = grid_data[:, 6]
        c12_avg = np.mean(c12)
        #print("\n>> "+"Structure of C12 data: {}\n".format(c12.shape))
        c03 = grid_data[:, 7]
        c03_avg = np.mean(c03)
        #print("\n>> "+"Structure of C03 data: {}\n".format(c03.shape))
        c07 = grid_data[:, 8]
        c07_avg = np.mean(c07)
        #print("\n>> "+"Structure of C07 data: {}\n".format(c07.shape))
        p = grid_data[:, 9]
        p_avg = np.mean(p)
        #print("\n>> "+"Structure of P data: {}\n".format(p.shape))


        month = met_data[:, 1]
        ltime = np.array(met_data[:, 4], dtype=np.int32)

        # u_sro 평균값 계산용 2차원 np array 생성. (ltime, runoff_avg_from_grid_runoff, runoff_avg_from_grid_param_avg)
        u_sro_avg = np.zeros((len(ltime), 3), dtype=np.float64)

        # 시간별 R값에 대한 numpy array 22500개 만듬
        r_h_np = np.zeros(150*150)

        self.append_text("Solid runoff rate 산정을 위한 변수들이 생성되었습니다.")
        
        # U_sro 계산
        self.append_text("Solid runoff rate 산정 중입니다...")
        n4PBar = 50
        for t in ltime:   # serial time
            r_h_np = float(r[t-1])
        
            if int(month[t-1]) == 12 or int(month[t-1]) == 1 or int(month[t-1]) == 2:
                u_sro_temp = dr * (0.09 * r_h_np * k * ls * c12 * p) / 2650
                u_sro_avg_temp = dr_avg * (0.09 * r_h_np * k_avg * ls_avg * c12_avg * p_avg) / 2650
            elif int(month[t-1]) == 3 or int(month[t-1]) == 4 or int(month[t-1]) == 5 or int(month[t-1]) == 6:
                u_sro_temp = dr * (0.09 * r_h_np * k * ls * c03 * p) / 2650
                u_sro_avg_temp = dr_avg * (0.09 * r_h_np * k_avg * ls_avg * c03_avg * p_avg) / 2650
            else:
                u_sro_temp = dr * (0.09 * r_h_np * k * ls * c07 * p) / 2650
                u_sro_avg_temp = dr_avg * (0.09 * r_h_np * k_avg * ls_avg * c07_avg * p_avg) / 2650
            
            u_sro_avg[t-1][0] = t   # t 값
            u_sro_avg[t-1][1] = np.mean(u_sro_temp)   # 시간별 grid 전체 u_sro 평균
            u_sro_avg[t-1][2] = np.mean(u_sro_avg_temp)   # 시간별 grid 전체 u_sro 평균

            u_sro[:, t-1] = u_sro[:, t-1] + u_sro_temp.T   # np_array.T : 가로 array를 세로 array로 Transpose
            
            if (t % 700) == 0:
                n4PBar += 1
                self.progressBar[0].setProperty("value", n4PBar)

            if (t % 1000) == 0:
                self.append_text(" >>Solid runoff rate 산정: {} 시간 경과 중...".format(t))

        self.append_text("Solid Runoff rate 산정을 완료하였습니다.")

        print(u_sro)
        print("\n>> "+"Structure of solid runoff rate data: {}".format(u_sro.shape))

        csv_header = "ltime, solid_runoff_avg, solid_runoff_by_param_avg"
        np.savetxt(r"c:\CAM_test\Inputs\db_u_sro_avg.csv", u_sro_avg, delimiter=",", header=csv_header)

        self.append_text("Solid runoff rate 산정 결과가 CSV 파일로 저장되었습니다.")

        # sqlite close
        cur.close()
        conn.close()

    ########################################################################################
    # grid_param table의 grid_no별 정보와 meteo_runoff table의 시간별 기상정보를 이용하여 계산
    # CN, S, i_a, Q, U_wro

    def calculate_w_runoff(self):

        self.append_text("### Water Runoff Rate 산정 ###")

        # ----------------------------------------------------------------------------------
        # SQLite DB 연결
        conn = sqlite3.connect(r"c:\CAM_test\GIS_DB\db4MMM.db")
        cur = conn.cursor()
        
        self.append_text("Water Runoff Rate 산정을 위한 GIS 데이터를 준비 중입니다...")
        
        sql = 'SELECT * FROM grid_param ORDER BY grid_no '
        cur.execute(sql)
        glist = cur.fetchall()

        grid_data = np.array(glist)

        #self.append_text("\n"+"Number of grid data: {}, structure of grid data: {}".format(len(grid_data), grid_data.shape))

        self.append_text("Water Runoff Rate 산정을 위한 기상 데이터를 준비 중입니다...")
        
        sql = 'SELECT * FROM meteo_runoff ORDER BY ltime '
        cur.execute(sql)
        mlist = cur.fetchall()

        met_data = np.array(mlist)

        #self.append_text("\n"+"Number of met. data: {}, structure of met. data: {}".format(len(met_data), met_data.shape))

        self.append_text("Water Runoff Rate 산정을 위한 변수들을 준비 중입니다...")
        
        # SL numpy array 변수 생성
        #sl = np.zeros((22500, len(met_data)), np.float64)
        #print("Structure of SL data: {}\n".format(sl.shape))
        
        # u_wro numpy array 변수 생성  cn, S, i_a, Q, U_wro
        u_wro = np.zeros((22500, len(met_data)), np.float64)
        #print("Structure of Water runoff rate data: {}".format(u_wro.shape))
        
        # rain용 numpy array 변수
        rain_np = np.zeros(22500, np.float64)

        # grid no.
        gn = np.array(grid_data[:,0], dtype=np.int32)
        #print("Structure of Grid no. data: {}".format(gn.shape))

        cn_avg = grid_data[:,10]
        #print("Structure of Average CN data: {}".format(cn_avg.shape))
        
        rain = met_data[:,6]
        #print("Structure of Rain data: {}".format(rain.shape))
        
        cum_5d_rain = met_data[:,7]
        #print("Structure of Past 5-day rainfall data: {}".format(cum_5d_rain.shape))
        
        month = np.array(met_data[:, 1], dtype=np.int32)
        ltime = np.array(met_data[:, 4], dtype=np.int32)

        # u_wro 평균값 계산용 2차원 np array 생성. (ltime, avg)
        u_wro_avg = np.zeros((len(ltime), 3), dtype=np.float64)

        # U_wro 계산
        self.append_text("Water Runoff rate 산정을 시작합니다...")

        n4PBar = 75
        for t in ltime:   # serial time
            if int(month[t-1]) == 12 or int(month[t-1]) == 1 or int(month[t-1]) == 2:
                if cum_5d_rain[t-1] < 12.0:
                    cn =  4.2 * cn_avg / (10 - 0.058 * cn_avg)
                elif cum_5d_rain[t-1] >= 12.0 and cum_5d_rain[t-1] < 28:
                    cn =  cn_avg
                else:
                    cn =  23 * cn_avg / (10 + 0.13 * cn_avg)
            else:
                if cum_5d_rain[t-1] < 35.0:
                    cn =  4.2 * cn_avg / (10 - 0.058 * cn_avg)
                elif cum_5d_rain[t-1] >= 35.0 and cum_5d_rain[t-1] < 53:
                    cn =  cn_avg
                else:
                    cn =  23 * cn_avg / (10 + 0.13 * cn_avg)
            
            cn2 = np.where(cn > 99, 99, cn)
            s = 254 * (100 / cn2 - 1)
            i_a = 0.2 * s
            rain_np[:] = rain[t-1]
            q_temp = np.power((rain[t-1] - 0.2 * s), 2) / (rain[t-1] + 0.8 * s)
            q = np.where(rain_np <= i_a, 0.0, q_temp)

            u_wro_temp = q / 1000

            # grid param 평균값으로 시간별 runoff 계산
            cn2_avg = np.mean(cn2)
            s_avg = 254 * (100 / cn2_avg - 1)
            i_a_avg = 0.2 * s_avg
            
            if rain[t-1] <= i_a_avg: 
                q_avg = 0.0
            else:
                q_avg = ((rain[t-1] - 0.2 * s_avg) ** 2) / (rain[t-1] + 0.8 * s_avg)
            u_wro_avg_from_param_avg = q_avg / 1000
                    
            u_wro_avg[t-1][0] = t   # t 값
            u_wro_avg[t-1][1] = np.mean(u_wro_temp)   # 시간별 grid 전체 u_wro 평균
            u_wro_avg[t-1][2] = u_wro_avg_from_param_avg        # 시간별 grid param 평균을 이용한 runoff
            
            # grid별 runoff value를 t-1 열에 할당
            u_wro[:, t-1] = u_wro[:, t-1] + u_wro_temp.T
            
            if (t % 700) == 0:
                n4PBar += 1
                self.progressBar[0].setProperty("value", n4PBar)

            if (t % 1000) == 0:
                self.append_text(" >>Water runoff rate 산정: {} 시간 경과 중...".format(t))

        self.append_text("Water Runoff rate 산정을 완료하였습니다.")

        print(u_wro)
        print("\n"+"Structure of water runoff rate data: {}\n".format(u_wro.shape))

        # numpy array to csv
        csv_header = "ltime, water_runoff_avg, water_runoff_by_param_avg"
        np.savetxt(r"c:\CAM_test\Inputs\db_u_wro_avg.csv", u_wro_avg, delimiter=",", header=csv_header)

        self.append_text("Water runoff rate 산정 결과를 CSV 파일로 저장하였습니다.")

        # sqlite close
        cur.close()
        conn.close()

    # button click 이벤트
    @QtCore.pyqtSlot()
    def on_clicked(self):

        # 강우 유출량 산정 버튼 실행 시 작동
        
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
            + str(self.sYear)  + '년\'\n 위 설정을 적용하여 2년 동안 강우유출 산정을 시작합니다.')
        self.append_text('사고지점: \'' + self.selAddress + '\'\n 시뮬레이션 시작년도: \'' 
            + str(self.sYear)  + '년\'\n 위 설정을 적용하여 2년 동안 강우유출 산정을 시작합니다.')
        
        self.progressBar[0].setVisible(True)

        address_list = self.selAddress.split(' ')
        dSql ="DELETE FROM simulation_info"
        iSql ="INSERT INTO simulation_info (sido, sigungu, address, s_year, s_month, s_day, s_hour, s_minute, simulation_duration, gis_method) VALUES('{}', '{}', '{}', {}, {}, {}, {}, {}, {}, '{}');".format(
            address_list[0], address_list[1], self.selAddress, self.sYear, param_i[1], param_i[2], param_i[3], param_i[4], param_i[9], 'arcgis')
        
        self.insertJusoData(dSql, iSql)
        
        self.button[0].setEnabled(False)                        

        self.calculate_runoff()
        self.append_text('강우 유출량 산정이 완료되었습니다. ')

        self.button[0].setEnabled(True)
        self.progressBar[0].setProperty("value", 0)
        self.progressBar[0].setVisible(False)
        #self.progressBar[1].setProperty("value", 0)
        
        #self.lineEdit[0].setText('')

        #self.removeFormLayout(self.grid[0])        
        
    def showModal(self):
        return super().exec_()

def main():
    import sys
    app = QApplication(sys.argv)
    shower = SecondWindow()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()