import os
import shutil
import sqlite3
#import sys
from math import *
import numpy as np
import pandas as pd
from time import sleep

from PyQt5.QtWidgets import (QApplication, QButtonGroup, QDesktopWidget, QDial, QDialog, QLabel, QLineEdit, QMainWindow, QProgressBar, QWidget, QGroupBox, QRadioButton
, QCheckBox, QPushButton, QMenu, QGridLayout, QVBoxLayout, QTextEdit)
from PyQt5 import QtCore
from PyQt5 import QtGui

import q_SearchJuso as sj
import calculate_grid_move as gm
import flow_direction as fd

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
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowStaysOnTopHint)
        
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

        days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] 

        answer = sum(days[:month-1]) + day 
        
        if ((year % 4 == 0 and year % 100 != 0) or year % 400 == 0) and month > 2: 
            answer = answer + 1 
        
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
    ### Processing Raster Data: QGIS 내부에서 실행
    
    ######################################################################
    ### Processing Meteorological Data
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

        sql = "SELECT code1 FROM station WHERE sido = '{}' AND sigungu = '{}'".format(sido, sigungu)
        print(sql)
        cur.execute(sql)
        row = cur.fetchone()
        stNo = int(row[0])  # station code

        # Yearly Data 가져오기 시작
        nRec = 1  # serial hour number 시작 

        for iYear in ylist:

            # data Table 할당
            dTable = "meteo_raw" + str(iYear)

            sql = 'SELECT date_time, temp, rain, wind_speed, wind_dir, rh, doc FROM {} WHERE st_no = {};'.format(dTable, stNo)
            cur.execute(sql)

            rows = cur.fetchall()

            print("{}의 데이터 갯수: {}".format(iYear, cur.rowcount))

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

        address_list = self.selAddress.split(' ')
        dSql ="DELETE FROM simulation_info"
        iSql ="INSERT INTO simulation_info (sido, sigungu, address, s_year, s_month, s_day, s_hour, s_minute, simulation_duration) VALUES('{}', '{}', '{}', {}, {}, {}, {}, {}, {});".format(
            address_list[0], address_list[1], self.selAddress, self.sYear, param_i[1], param_i[2], param_i[3], param_i[4], param_i[9])
        
        self.insertJusoData(dSql, iSql)
        
        self.button[0].setEnabled(False)                        

        self.calculate_runoff()
        self.append_text('강우 유출량 산정이 완료되었습니다. ')

        self.button[0].setEnabled(True)
        self.progressBar[0].setProperty("value", 0)
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