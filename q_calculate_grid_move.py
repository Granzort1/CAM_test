import subprocess
from glob import glob
import numpy as np
import pandas as pd
# from pyproj import Proj, Transformer
import requests
import sys

# 이동 전 Grid CenterX: 423979.692659  CenterY: 334581.766996
# 2021. 4. 15. 중심점 보정 centerX, centerY = 409179.6927, 334623.767
centerX, centerY = 409179.6927, 334623.767

#address = "울산시 중구 우정2길 45"
#address = "대전광역시 대덕구 상서로 20"
#address = input("도로명 주소를 입력하세요: ")

def moving_from_origin(address):
    """
    # 중부원점 TM좌표(EPSG:5186) 가져오기
    # Vworld 인증 키: key=EB343B36-77B1-3B8C-8A90-C3B6CA3A2A4E
    # 만료일: 2022-04-18  [ 인증키 연장 횟수 : 총 3회 중 0회 진행 ]
    """
    key='E7842024-CC6C-3002-9616-BB7C86BEDA9A'

    r = requests.get(f'http://api.vworld.kr/req/search?service=search&request=search&version=2.0&crs=EPSG:5186&size=10&page=1&query={address}&type=address&category=road&format=json&errorformat=json&key={key}')
    #r = requests.get('http://api.vworld.kr/req/search?service=search&request=search&version=2.0&crs=EPSG:900913&bbox=14140071.146077,4494339.6527027,14160071.146077,4496339.6527027&size=10&page=1&query=성남시 분당구 판교로 242&type=address&category=road&format=json&errorformat=json&key=03CE766E-4AF6-3AD5-836F-80C2C3D0A718')
    #r = requests.get('http://api.vworld.kr/req/search?service=search&request=search&version=2.0&crs=EPSG:5186&bbox=14140071.146077,4494339.6527027,14160071.146077,4496339.6527027&size=10&page=1&query=서울특별시 중구 다산로 지하 115&type=address&category=road&format=json&errorformat=json&key=03CE766E-4AF6-3AD5-836F-80C2C3D0A718')

    data = r.json()

    #for item in data['response']['result']['items']:
    #    xy_cord = item['point']
    items = data['response']['result']['items']
    x_cord = items[0]['point']['x']
    y_cord = items[0]['point']['y']

    print(f"화학사고 발생지 주소: {address}, TM 좌표: (x, y): ({x_cord}, {y_cord})\n")

    move_x_axis1 = float(x_cord) - centerX  # x_cord 값이 centerX보다 작으면 move_x_axis는 음수값으로 왼쪽으로 이동하고, x_cord 값이 centerX보다 크면 양수값으로 오른쪽으로 이동
    move_y_axis1 = float(y_cord) - centerY 

    # 100 미만 버림. 100 m 격자에 맞추기 위함
    move_x_axis = round(move_x_axis1, -2)
    move_y_axis = round(move_y_axis1, -2)

    clist = []
    clist.append(move_x_axis); clist.append(move_y_axis)

    # print("----------------------------------------------------------------")
    # print("[Modeling Grid Movement]")
    
    # print("[X cordinate] From {} to {}: {}".format(centerX, x_cord, move_x_axis))
    # print("[Y cordinate] From {} to {}: {}\n".format(centerY, y_cord, move_y_axis))

    return clist

def main():

    address = "세종특별자치시 나리1로 16"

    # 매개변수가 몇 개인지 확인하여 한 줄의 주소 텍스트로 만듬.
    nArgv = len(sys.argv)
    for i in range(1, nArgv):
        address += sys.argv[i] + " "
    
    address = "세종특별자치시 나리1로 16"

    moving_cord = moving_from_origin(address)
    print(f'moved to (x, y): ({moving_cord[0]}, {moving_cord[1]})')
    
if __name__ == '__main__':
    main()


"""
proj_UTMK = Proj(init='epsg:5186')
#proj_UTMK = Proj(init='epsg:3857')

proj_WGS84 = Proj(init='epsg:4326')

# UTM-K -> WGS84 샘플
x1, y1 = 961114.519726,1727112.269174
#x2, y2 = transform(proj_UTMK,proj_WGS84,x1,y1)
transformer = Transformer.from_crs("epsg:5186", "epsg:4019")
x2, y2 = transformer.transform(x_cord, y_cord)

print(x2,y2)

# WGS84 -> UTM-K 샘플
x1, y1 = 127.07098392510115, 35.53895289091983
# x2, y2 = transform(proj_WGS84, proj_UTMK, x1, y1)
transformer = Transformer.from_crs("epsg:4019", "epsg:5186")
x3, y3 = transformer.transform(x2, y2)
print(x3,y3)

# x, y 컬럼을 이용하여 UTM-K좌표를 WGS84로 변환한 Series데이터 반환
def transform_utmk_to_w84(df):
    transformer = Transformer.from_crs("epsg:5186", "epsg:4326")
    return pd.Series(transformer.transform( df['x'], df['y']), index=['x', 'y'])

df_xy = pd.DataFrame([
                        ['A', 961114.519726,1727112.269174],
                        ['B', 940934.895125,1685175.196487],
                        ['C', 1087922.228298,1761958.688262]
                    ], columns=['id', 'x', 'y'])

df_xy[['x_w84', 'y_w84']] = df_xy.apply(transform_utmk_to_w84, axis=1)

print(df_xy)
"""

"""
# 여러 python file을 순차적으로 실행
파일리스트 = glob("day_*.py")

for 파일 in 파일리스트:
    print("호출된 파일은 {}".format(파일))
    
    subprocess.call(['python', 파일])
    
"""
"""
a1 = np.arange(0, 22500) 
#a = a1.transpose()
b1 = np.random.rand(22500)
#b = b1.transpose()
c1 = a1 * a1
#c = c1.transpose()

t1 = np.concatenate((a1, b1), axis=0)
t2 = np.concatenate((t1, c1), axis=0)
t3 = t2.reshape(3, 22500)
t = t3.transpose()

print(a1.shape)

print(t.shape)
print(t)
"""