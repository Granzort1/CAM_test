### QGIS GIS DB processing이 포함된 사고지역 공간정보·기상 불러오기 main window ###
# 1. q_SearchJuso.py (file import하여 function 호출): 주소 검색
# 2. q_processGIS_DB.py GISWindow: 새 창(GISWindow)을 열어 호출
#         QGIS에서 GIS DB processing 하기 위한 주소와 연도를 선택하고, 
#         QGIS(q_main.py)를 호출하여 GIS DB 처리
# 3. sClickMethod2 function
#    1) q_processingMetDB.py (file import하여 function 호출): 기상 자료 처리
#    2) 내부 function 호출: Solid Runoff, Water Runoff 산정
#                    calculate_s_runoff()
#                    calculate_w_runoff()
##################################################################################

import sys
import win32gui, win32con
import numpy as np
import sqlite3
from time import sleep

from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import q_SearchJuso as sj
from q_processGIS_DB import GISWindow
import q_processingMetDB as pm

class ThreadClass(QtCore.QThread): 

    def __init__(self, parent = None): 
        super(ThreadClass,self).__init__(parent)

    def run(self): 
        print('Thread start')

class Window(QWidget):
    
    def __init__(self):
        # to hide command console python
        the_program_to_hide = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(the_program_to_hide , win32con.SW_HIDE)
        
        # Thread 사용
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
        grid1.addWidget(self.createCalculateRunoffGroup(), 1, 0, 1, 1)
        grid1.addWidget(self.createExplainGroup(), 0, 1, 3, 2)

        # grid layout list에 grid1 추가: self.grid[0]
        self.grid.append(grid1)

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
    
    def createSearchGroup(self):
        groupbox = QGroupBox('사고지점 검색')

        # 텍스트 입력 받기 위한 QLineEdit 추가
        lineEdit = QLineEdit()
        self.lineEdit.append(lineEdit)    # self.lineEdit list에 추가

        guideText1 = "위 입력창에 사고지점 주소 또는 건물명을 입력하고 \n검색 버튼을 누르세요.\n(예시:  \'세종로 100\' 또는 \'종로구청\')" 
        labelExp1 = QLabel(guideText1, self)

        searchButton = QPushButton('검색', self)         # button
        searchButton.clicked.connect(self.sClickMethod)  # button click event 연결

        guideText2 = "\n안내: \n해당 검색어로 10개 이하의 주소가 검색되면 \nGIS와 기상자료 처리를 위한 새 창으로 이동합니다. \n" + \
                        "새 창에서 사고 주소와 시작년도를 선택하여 \nGIS와 기상 자료 처리를 하시면 됩니다."
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
        # groupbox.setFixedWidth(250)

        return groupbox

    def createCalculateRunoffGroup(self):
        groupbox = QGroupBox('기상자료 처리와 강우 유출량 산정')

        calculateButton = QPushButton('기상자료 처리와 강우 유출량 산정', self)         # button
        calculateButton.clicked.connect(self.sClickMethod2)  # button click event 연결

        # 전체용 progressBar
        pbar0 = QProgressBar()
        pbar0.setGeometry(30, 30, 230, 25)
        self.progressBar.append(pbar0)

        guideText3 = "\n안내: \nQGIS에서 GIS와 기상자료 처리를 완료한 후 \n강우 유출량 산정을 하시기 바랍니다. "
        labelExp3 = QLabel(guideText3, self)

        # 세로형 BoxLayout 생성
        vbox = QVBoxLayout()
        # vbox.addWidget(lineEdit)       # lineEdit을 위젯으로 추가
        # vbox.addWidget(labelExp1)
        vbox.addWidget(calculateButton)    # calculateButton을 위젯으로 추가
        vbox.addWidget(pbar0)
        vbox.addWidget(labelExp3)
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
        groupbox.setFixedWidth(350)
        
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
            self.append_text(' ' + str(len(self.aList)) + '개의 주소가 검색되었습니다.\n\nGIS와 기상자료 처리를 위한 새 창으로 이동합니다.\n')

            #self.grid[0].addWidget(self.createAccidentPlaceGroup(), 1, 0, 1, 1)
            #self.grid[0].addWidget(self.createStartYearGroup(), 2, 0, 1, 1)
            #self.grid[0].addWidget(self.createPushButtonGroup(), 3, 0, 1, 1)
            
            self.win = GISWindow(self.aList)
            r = self.win.showModal

    def sClickMethod2(self):
        self.progressBar[0].setVisible(True)
        self.progressBar[0].setAlignment(Qt.AlignCenter)
        
        # 기상자료 processing
        print('기상 자료 처리를 시작합니다... ')
        self.append_text('기상 자료 처리를 시작합니다... ')
        
        pm.met_data_processing()
        self.progressBar[0].setProperty("value", 5)
        
        
        print('기상 자료 처리를 완료하였습니다... ')
        self.append_text('기상 자료 처리를 완료하였습니다... ')
        
        # 주소 검색 버튼
        print('강우 유출량 산정을 시작합니다. ')
        self.append_text('강우 유출량 산정을 시작합니다.')

        # GIS 자료 처리, 강우 유출방향 산정, 기상자료 처리를 했는지 sqlite db에서 확인
        # simualtion_info, grid_param, meteo_runoff
        # 자료처리를 했으면 다음 단계로 강우 유출량 산정 진행
        # SQLite DB 연결
        conn = sqlite3.connect(r"c:\CAM_test\GIS_DB\db4MMM.db")
        cur = conn.cursor()

        sql = 'SELECT Count() FROM grid_param'
        cur.execute(sql)
        numberOfRows_GIS = cur.fetchone()[0]
        print('grid_param record count: {}'.format(numberOfRows_GIS))

        sql = 'SELECT Count() FROM meteo_runoff'
        cur.execute(sql)
        numberOfRows_Met = cur.fetchone()[0]
        print('meteo_runoff record count: {}'.format(numberOfRows_Met))   
        
        cur.close()
        conn.close()

        if numberOfRows_GIS != 22500:
            # exit function
            self.append_text("화학사고 주소를 입력하여 사고 위치를 정하고, QGIS에서 GIS와 기상자료 처리 후 강우 유출량 산정을 시도하기 바랍니다. ")
            return

        if numberOfRows_Met < 15000:
            self.append_text("화학사고 주소를 입력하여 사고 위치를 정하고, QGIS에서 GIS와 기상자료 처리 후 강우 유출량 산정을 시도하기 바랍니다. ")
            return

        # self.progressBar[0].setProperty("value", 0)
        # self.progressBar[0].setAlignment(Qt.AlignCenter)
        self.calculate_s_runoff()
        self.calculate_w_runoff()
        
        self.progressBar[0].setVisible(False)

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
        n4PBar = 5
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
            
            # if (t % 700) == 0:
            if (t % 350) == 0:
                n4PBar += 1
                self.progressBar[0].setProperty("value", n4PBar)

            if (t % 1000) == 0:
                self.append_text(" >>Solid runoff rate 산정: {} 시간 경과 중...".format(t))

        self.append_text("Solid Runoff rate 산정을 완료하였습니다.")

        # print(u_sro)
        # print("\n>> "+"Structure of solid runoff rate data: {}".format(u_sro.shape))

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

        n4PBar = 50
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
            
             # if (t % 700) == 0:
            if (t % 350) == 0:
                n4PBar += 1
                self.progressBar[0].setProperty("value", n4PBar)

            if (t % 1000) == 0:
                self.append_text(" >>Water runoff rate 산정: {} 시간 경과 중...".format(t))

        self.append_text("Water Runoff rate 산정을 완료하였습니다.")

        # print(u_wro)
        # print("\n"+"Structure of water runoff rate data: {}\n".format(u_wro.shape))

        # numpy array to csv
        csv_header = "ltime, water_runoff_avg, water_runoff_by_param_avg"
        np.savetxt(r"c:\CAM_test\Inputs\db_u_wro_avg.csv", u_wro_avg, delimiter=",", header=csv_header)

        self.append_text("Water runoff rate 산정 결과를 CSV 파일로 저장하였습니다.")

        # sqlite close
        cur.close()
        conn.close()

def main():
    app = QApplication(sys.argv)
    main = Window()
    main.show()
    # s = SecondWindow()
    # main.textChanged.connect(s.text.append)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()