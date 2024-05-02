import numpy as np
import pandas as pd
from random import *
import sqlite3

def sqlite2csv():
    # SQLite DB 연결, pandas parameter에 sqlite를 연결하여 query하고, 이를 CSV file로 저장

    conn = sqlite3.connect(r"c:\CAM_test\GIS_DB\db4MMM.db")
    
    sql = 'SELECT id, toGrid, fromGrid FROM flow ORDER BY id '

    db_df = pd.read_sql_query(sql, conn)

    db_df.to_csv(r'c:\CAM_test\Inputs\db_flowToGrid.csv', index=False)

    conn.close()

def makeFlowDirection():
    # 한 변의 Grid 격자 수
    nGridSize = 150 

    nGridNo = []
    nElevation = []
    nFlowTo = []
    sFlowArrow = []
    
    nSetDirection = [0,0,0,0,0,0,0,0,0]
    nSetElevation = [0,0,0,0,0,0,0,0,0]

    def nearGrids(nGrid):    
        nLot, nRest = divmod(nGrid, nGridSize)
        #nDirection = [0,0,0,0,nGrid,0,0,0,0]

        if nRest == 0:  # 왼쪽 끝줄
            if nLot == 0:                 # 제일 위
                nDirection = [-1, nGrid + nGridSize, nGrid + nGridSize + 1, -1, nGrid, nGrid + 1, -1, -1, -1]
            elif nLot == nGridSize - 1:   # 제일 아래
                nDirection = [-1, -1, -1, -1, nGrid, nGrid + 1, -1, nGrid - nGridSize, nGrid - nGridSize + 1]
            else:                         # 가운데
                nDirection = [-1, nGrid + nGridSize, nGrid + nGridSize + 1, -1, nGrid, nGrid + 1, -1, nGrid - nGridSize, nGrid - nGridSize + 1]
        elif nRest == nGridSize - 1:  # 오른쪽 끝줄
            if nLot == 0:                 # 제일 위
                nDirection = [nGrid + nGridSize - 1, nGrid + nGridSize, -1, nGrid - 1, nGrid, -1, -1, -1, -1]
            elif nLot == nGridSize - 1:   # 제일 아래
                nDirection = [-1, -1, -1, nGrid - 1, nGrid, -1, nGrid - nGridSize - 1, nGrid - nGridSize, -1]
            else:                         # 가운데
                nDirection = [nGrid + nGridSize - 1, nGrid + nGridSize, -1, nGrid - 1, nGrid, -1, nGrid - nGridSize - 1, nGrid - nGridSize, -1]
        else:  # 가운데 줄
            if nLot == 0:                 # 제일 위
                nDirection = [nGrid + nGridSize - 1, nGrid + nGridSize, nGrid + nGridSize + 1, nGrid - 1, nGrid, nGrid + 1, -1, -1, -1]
            elif nLot == nGridSize - 1:   # 제일 아래
                nDirection = [-1, -1, -1, nGrid - 1, nGrid, nGrid + 1, nGrid - nGridSize - 1, nGrid - nGridSize, nGrid - nGridSize + 1]
            else:                         # 가운데
                nDirection = [nGrid + nGridSize - 1, nGrid + nGridSize, nGrid + nGridSize + 1, nGrid - 1, nGrid, nGrid + 1, nGrid - nGridSize - 1, nGrid - nGridSize, nGrid - nGridSize + 1]
        return nDirection

    def decideFlow(nNearGridNo, nElevation):
        nFlowTogrid = 0
        nMin = 9999

        #print(str(nNearGridNo))
        #print(str(nElevation))

        for i in range(0, 9):
            if nElevation[i] < nMin:
                nMin = nElevation[i]
                nFlowToGrid = nNearGridNo[i]
        #print("{} Grid. Elevation: {}".format(nFlowToGrid, nMin))
        return nFlowTogrid

    def flowArrow(nN):
        if nN == 0:
            sArrow = "↙"
        elif nN == 1:
            sArrow = "↓"
        elif nN == 2:
            sArrow = "↘"
        elif nN == 3:
            sArrow = "←"
        elif nN == 4:
            sArrow = "-"
        elif nN == 5:
            sArrow = "→"
        elif nN == 6:
            sArrow = "↖"
        elif nN == 7:
            sArrow = "↑"
        elif nN == 8:
            sArrow = "↗"
        return sArrow

    ##random elevation 생성
    #for i in range(0, (nGridSize * nGridSize)):
    #    nGridNo.append(i)
    #    nElevation.append(randint(10,100))

    #SQLite Data 불러와서 배열에 할당
    # SQLite DB 연결
    conn = sqlite3.connect(r"c:\CAM_test\GIS_DB\db4MMM.db")
    
    # Connection 으로부터 Cursor 생성
    cur = conn.cursor()

    sqlCom = 'SELECT grid_no, elevation FROM grid_param ORDER BY grid_no '

    # SQL 쿼리 실행
    cur.execute(sqlCom)
    
    # 데이타 Fetch
    rows = cur.fetchall()
    for row in rows:
        nGridNo.append(int(row[0]))
        nElevation.append(float(row[1]))
    
    #print("nGridNo Count: {}".format(len(nGridNo)))

    print("\n" + "-" * 100)
    print("### 모델링 Grid간 강우 흐름 방향 산정 ###\n")
    for i in range(0, (nGridSize * nGridSize)):
        # Grid 주변 Grid 번호를 가져옴. outside는 0으로 할당
        nSetDirection = nearGrids(nGridNo[i])    

        for j in range(0, 9):
            if nSetDirection[j] >= 0:
                nSetElevation[j] = nElevation[nSetDirection[j]]
            else:
                nSetElevation[j] = 9999.0

        #Flow 결정
        nFlowTogrid = 0
        nMin = 9999

        #print(str(nSetDirection))
        #print(str(nSetElevation))
        nFFlow_j = 4
        for j in range(0, 9):
            if nSetElevation[j] < nMin:
                nMin = nSetElevation[j]
                nFlowToGrid = nSetDirection[j]
                nFFlow_j = j

        sFlowArrow.append(flowArrow(nFFlow_j))
        # print("{} Grid에서 {} Grid로 Flowing. {}".format(i, nFlowToGrid, flowArrow(nFFlow_j)))
        nFlowTo.append(nFlowToGrid)

    cur.execute('DELETE FROM flow;')
    
    flow_list = []
    flow_data = []
    
    for i in range(0, (nGridSize * nGridSize)):
        sql ="INSERT INTO flow (ID, toGrid, fromGrid) VALUES(?, ?, ?);"
        cur.execute(sql, (i, nFlowTo[i], i))
        
        #to_grid = int(nFlowTo[i])
        #flow_list.append(i); flow_list.append(to_grid); flow_list.append(i)
        #flow_data.append(flow_list)

    #flow_np = np.array(flow_data)
    #query = "insert into flow (:id, :toGrid, :fromGrid)"
    #cur.executemany(query, flow_np)
    
    conn.commit()

    # Connection 닫기
    cur.close()
    conn.close()

    sqlite2csv()

    print("모델링 Grid의 강우 흐름 방향을 산정하고, DB에 저장하였습니다.\n")
    
    """
    nRow = 0
    for i in range(0, nGridSize):
        printLine = ""
        for j in range(0, nGridSize):
            if j < nGridSize:
                printLine += str(nGridNo[nGridSize * nRow + j ]) + ", "
            else:
                printLine += str(nGridNo[nGridSize * nRow + j ]) + "\n "
        #print(printLine)
        nRow += 1

    nRow = 0
    for i in range(0, nGridSize):
        printLine = ""
        for j in range(0, nGridSize):
            if j < nGridSize:
                printLine += str(nElevation[nGridSize * nRow + j ]) + ", "
            else:
                printLine += str(nElevation[nGridSize * nRow + j ]) + "\n "
        #print(printLine)
        nRow += 1

    nRow = 0
    for i in range(0, nGridSize):
        printLine = ""
        for j in range(0, nGridSize):
            if j < nGridSize:
                printLine += str(nFlowTo[nGridSize * nRow + j ]) + ", "
            else:
                printLine += str(nFlowTo[nGridSize * nRow + j ]) + "\n "
        #print(printLine)
        nRow += 1

    nRow = 0
    for i in range(0, nGridSize):
        printLine = ""
        for j in range(0, nGridSize):
            if j < nGridSize:
                printLine += str(sFlowArrow[nGridSize * nRow + j ]) + ", "
            else:
                printLine += str(sFlowArrow[nGridSize * nRow + j ]) + "\n "
        #print(printLine)
        nRow += 1
    """

if __name__ == "__main__":
    makeFlowDirection()