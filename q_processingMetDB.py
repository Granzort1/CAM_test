# 측정소 code와 year set(2017-2018, 2018-2019, 2019-2020)에 해당하는 data를 sqlite DB에서 가져옴
# 기상 자료 처리
# date_time: "2020-01-01 1:00" -> year, month, day, hour, ltime 으로 분해하여 insert
# temp: 5 (celcius) -> 5+275 (K) 로 변환하여 insert
# rain: 그대로
# wind_speed (m/s), wind_dir(16방위) -> windX (x 선속도 km/h), windY (y 선속도 km/h)
# rh: 그대로
# doc: 그대로

import numpy as np
import pandas as pd
from math import *
from random import *
import sqlite3

print("\n" + "-"*100)
print("\n" + "### 모델링 입력자료 중 기상자료 처리 ###")

def dayOfYear(date: str) -> int: 
    # 1년 중 몇번째 일인지 리턴
    year, month, day = int(date.split('-')[0]), int(date.split('-')[1]), int(date.split('-')[2]) 

    if year == 2020:  # leap year
        days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] 
    else:   # standard year
        days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] 

    answer = sum(days[:month-1]) + day 
    
    return answer

# dummy func
def new_func():
        x = 0
new_func()

def timeOfYear(julDay: int, time: int) -> int:
    # 1년 중 몇번째 시간인지 리턴
    answer = (julDay - 1) * 24 + time

    return answer

# dummy func
def new_func():
        x = 0
new_func()

# 파이썬에 switch 기능을 지원하지 않아서 function을 이용하여 dictionary와 유사하게 입력값에 대한 리턴값으로 처리
def met_city_st(x): 
    return {'서울': '서울시', '부산': '부산시', '대구': '대구시', '대전': '대전시', '광주': '광주시', '울산': '울산시', '인천': '인천시', '세종': '세종시' }[x]

def local_do_st(x): 
    return {'충청남도': '충남', '충청북도': '충북', '전라북도': '전북', '전라남도': '전남', '경상북도': '경북', '경상남도': '경남' }[x]

#############################################################################################
# Meteological data processing 
def met_data_processing():

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
    print(sql)
    cur.execute(sql)
    row = cur.fetchone()
    sido1 = row[0]; sigungu = row[1]; sYear = int(row[3])

    if len(sido1) == 4:
        sido = local_do_st(sido1)
    else:
        sido = sido1[:2]
    
    if sido == '서울' or sido == '부산' or sido == '대구' or sido == '대전' or sido == '광주' or sido == '인천' or sido == '울산' or sido == '세종':
        sigungu = met_city_st(sido)
    

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

        # 기상 data Table 할당
        dTable = "meteo_full" + str(iYear)
        
        if sido =='세종':
            sido = '대전'
            sigungu = '대전시' 
        
        # 세종시 오류나는 원 소스 시작
        # 2020년을 제외하고 그 이전 연도의 경우, 세종은 '대전시' 측정소로 설정
        # if sido =='세종':
        #    sigungu = '대전시' if iYear < 2020 else '세종시'
        # 세종시 오류나는 원 소스 끝
        
        # 연도에 맞는 
        sql = f"SELECT code1 FROM station WHERE sido = '{sido}' AND sigungu = '{sigungu}'"
        print(sql)
        
        cur.execute(sql)
        row = cur.fetchone()
        stNo = int(row[0])  # station code

        sql = f'SELECT date_time, temp, rain, wind_speed, wind_dir, rh, doc FROM {dTable} WHERE st_no = {stNo};'
        cur.execute(sql)
        rows = cur.fetchall()

        data = []

        for row in rows:
            data.append(row)

        # numpy 변수에 할당
        metData = np.array(data)

        # print("장소: #{} 의 {}년,   is {}.".format(iYear, stNo, metData.shape))

        print("#{} 기상 측정소 {}년 자료를 가져왔습니다.".format(stNo, iYear))

        # 새로운 numpy 변수에 할당
        # metData2 = np.zeros(8760, 11)

        # year, month, day, hour, ltime, temp, rain, windX, windY, rh, doc 용 list 변수
        # SELECT date_time, temp, rain, wind_speed, wind_dir, rh, doc FROM 
        data2 = []  

        # met. data 변환
        print("{}년 기상자료 처리 중...".format(iYear))

        cum_5d_list = np.zeros(120)
        for rec in metData:
            # 비어 있는 리스트 만들기
            list1 = list()
            
            # 1. date_time >> year, month, day, hour, ltime 변환
            date, time = rec[0].split(" ")[0], rec[0].split(" ")[1]

            year, month, day = int(date.split('-')[0]), int(date.split('-')[1]), int(date.split('-')[2]) 

            hour = int(time.split(":")[0])

            lDate = dayOfYear(date)
            lTime = timeOfYear(lDate, hour)
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


        # print("\n>> "+"Data structure of {} year is {}.".format(iYear, met_runoff.shape))
        # print("\n>> "+"Meteological data is assigned to numpy array.")

        # numpy array 변수를 SQLite table에 insert
        # table name: meteo_runoff
        # print("\n"+"Inserting numpy array data to DB...")

        query = "insert into meteo_runoff values (:year, :month, :day, :hour, :ltime, :temp, :rain, :cum_5d_rain, :windX, :windY, :rh, :doc, :R)"

        cur.executemany(query, met_runoff)
        conn.commit()

    print("기상자료를 처리하여 DB에 저장하였습니다.")

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

    #print("\n" + "-"*60)
    print("기상자료를 csv file 형태의 입력자료로 저장하였습니다.")

    # Connection 닫기
    cur.close()
    conn.close()

    print("\n" + "-"*100)

if __name__ == '__main__':
    met_data_processing()
