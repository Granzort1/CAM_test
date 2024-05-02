### QGIS 프로그램의 Python console에서 호출하여 
# Grid 이동, Raster 파일 자료 추출 작업을 진행함.

import processing
from qgis.core import QgsApplication
from qgis.utils import iface

from osgeo import gdal
from osgeo.gdalconst import *

import os
import shutil
import numpy as np
import sqlite3

import q_calculate_grid_move as gm
import q_flow_direction as fd
# import q_processingMetDB as pm
# import q_calculate_U_sro as sr
# import q_calculate_U_wro as wr

######################################################################
### 100m * 100m grid 이동 변수
# calculate_grid_move.py를 import하여 moving_from_origin function을 사용
# return 되는 list[0]이 x 좌표 이동값, list[1]이 y 좌표 이동값, 
# sample address = "대전광역시 대덕구 상서로 20"

# sqlite에서 데이터 가져오기: 해당 측정소, 해당 연도 set
# SQLite DB 연결
conn = sqlite3.connect(r"c:\CAM_test\GIS_DB\db4MMM.db")

# Connection으로부터 Cursor 생성
cur = conn.cursor()

sql = "SELECT address FROM simulation_info "
cur.execute(sql)
row = cur.fetchone()

# Address를 sqlite3에서 불러오기
address = row[0]

# 주소에 해당하는 만큼 move할 좌표 거리 얻어옴 
grid_move = gm.moving_from_origin(address)

# input polygon과 moved_polygon
infn = 'C:/CAM_test/GIS_DB/MyProject/input/15km_100by100.shp'
moved_vector = 'C:/CAM_test/GIS_DB/QGIS/moved_vector.shp'

### move vector - unit: meter
# x: (-) to west, (+) to east
# y: (-) to south, (+) to north
move_x = grid_move[0]
move_y = grid_move[1]

processing.run("native:translategeometry",\
{'INPUT':infn,\
'DELTA_X':move_x,'DELTA_Y':move_y,\
'DELTA_Z':0,'DELTA_M':0,\
'OUTPUT':moved_vector})

# simulation_info table 중 gis_method를 qgis로 업데이트
# cur.update(f"UPDATE simulation_info SET gis_method = 'qgis' WHERE address = '{address}")
# conn.commit()

# Connection 닫기
cur.close()
conn.close()

print("해당 주소를 중심으로한 모델링 Polygon을 생성하였습니다.")

### get extent of moved vector
layer = iface.addVectorLayer(moved_vector, '', 'ogr')
ext = layer.extent()
xmin = ext.xMinimum()
xmax = ext.xMaximum()
ymin = ext.yMinimum()
ymax = ext.yMaximum()

### set extent_value
extent_value = '{},{},{},{} [EPSG:5186]'.format(xmin, xmax, ymin, ymax)

### convert vector to raster(make moved raster grids)
outfn= 'C:/CAM_test/GIS_DB/QGIS/grid4move.tif'

processing.run("gdal:rasterize",\
{'INPUT':moved_vector,\
'FIELD':'Grid_no','BURN':0,'UNITS':0,\
'WIDTH':1,'HEIGHT':1,\
'EXTENT':extent_value,\
'NODATA':0,'OPTIONS':'','DATA_TYPE':5,'INIT':None,\
'INVERT':False,'EXTRA':'',\
'OUTPUT':outfn})

print("모델링 Grid를 생성하였습니다.")

### cut dem with moved raster grids

in_rasters = ['dem_100', 'lu_100_add_3', 'sll_100', 'slp_100', 'kvalue_100']
out_rasters = ['dem_crop.tif', 'lu_crop.tif', 'sll_crop.tif', 'slp_crop.tif', 'kvalue_crop.tif']

for ii in range(5):
    in_ras = 'C:/CAM_test/GIS_DB/Korea/' + in_rasters[ii]
    out_ras = 'C:/CAM_test/GIS_DB/QGIS/' + out_rasters[ii]
    processing.run("gdal:cliprasterbyextent",\
    {'INPUT':in_ras,\
    'PROJWIN':extent_value,\
    'NODATA':None,'OPTIONS':'','DATA_TYPE':0,'EXTRA':'',\
    'OUTPUT':out_ras})
    
    gdal.AllRegister()  # 뒤에 raster data를 가져오기 위한 선언
    inDs = gdal.Open(out_ras)
    band1 = inDs.GetRasterBand(1)
    rows = inDs.RasterYSize
    cols = inDs.RasterXSize

    cropData = band1.ReadAsArray(0,0,cols,rows)
    outData = np.zeros((rows,cols), np.float64)

    for i in range(0,rows):
        for j in range(0, cols):
            outData[i,j] = cropData[i,j]
    
    if ii == 0:
        el_np1 = outData.ravel()      # 한 줄 array로 변환
        el_np = np.around(el_np1, 2)  # 소수점 둘째자리로 반올림
        print("수치고도자료 Grid Data를 추출하였습니다.")

    elif ii == 1:
        lu_np = outData.ravel()      # 한 줄 array로 변환
        print("토지피복도 Grid Data를 추출하였습니다.")
    elif ii == 2:
        sl_np = np.around(outData.ravel(), 3) # 소수점 세째자리로 반올림
        print("사면길이 Grid Data를 추출하였습니다.")
    elif ii == 3:
        sp_np2 = outData.ravel()
        sp_np1 = np.where(sp_np2 <= 0.0, 0.0000000001, sp_np2)
        sp_np = np.around(sp_np1, 3) # 소수점 세째자리로 반올림
        print("사면경사 Grid Data를 추출하였습니다.")
    elif ii == 4:
        k_np = np.around(outData.ravel(), 2) # 소수점 둘둘째자리로 반올림
        print("K value Grid Data를 추출하였습니다.")

# grid no.
grid_np = np.arange(0, 22500)

######################################################################
# lu_np * [landuse 대분류] 1: 시가화 건조지역, 2: 농지, 3: 산림지역, 4: 초지, 5: 습지, 6: 나지, 7: 수역
# lu_np2 * [landuse 대분류 조정] 1: 시가화 건조지역, 2: 농지, 3: 산림지역, 4: 초지, 5->6: 습지, 6: 나지, 7->6: 수역
lu_np2 = np.where(lu_np == 7, 6, np.where(lu_np == 5, 6, np.where(lu_np == 6, 6, np.where(lu_np == 4, 4, np.where(lu_np == 3, 3, np.where(lu_np == 2, 2, 1))))))   

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

print("모델링 지역에 대한 DR과 C, P, CN data를 산출하였습니다.")

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
#print("grid_param_0 structure: {}".format(grid_param_0_np.shape))

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
#print("grid_param structure: {}".format(grid_param_np.shape))

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

cur.executemany(query, grid_param_np)
conn.commit()

print("모델링 지역에 대한 runoff parameter data를 DB에 저장하였습니다.")

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

print("모델링 지역에 대한 Runoff parameter data를 csv file에 저장하였습니다.")
  
# delete vector layer
project = QgsProject.instance()
#print(project.mapLayers())
to_be_deleted = project.mapLayersByName('moved_vector')[0]
project.removeMapLayer(to_be_deleted.id())
#print('삭제 후')
#print(project.mapLayers())

# 강우 흐름 방향 산정
fd.makeFlowDirection()
print('\nGrid별 강우흐름 방향 산정을 완료하였습니다.')

# 기상자료 처리
# pm.met_data_processing()
# print('\n기상자료 처리를 완료하였습니다.')

# Solid runoff rate 계산
# sr.calculate_s_runoff()

# Water runoff rate 계산
# wr.calculate_w_runoff()

print('\n모델링을 위한 자료 처리를 완료하였습니다.')