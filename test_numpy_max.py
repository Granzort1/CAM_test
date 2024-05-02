import numpy as np 

# 2차원 array 예시
# b = np.array([[4, 3, 2], [8, 5, 9], [7, 6, 1]])

CELL_NUM = 22500
TIME_NUM = 6
b = np.random.rand(CELL_NUM, TIME_NUM)
print(b)

m1 = np.argmax(b) # 5
m2 = np.argmax(b, axis = 0) # array([1, 2, 1])
m3 = np.argmax(b, axis = 1) # array([0, 2, 0])

print(f'전체 max: {m1}')
print(f'가로 중 max: {m2}')
print(f'세로 중 max: {m3}')

r = np.zeros((CELL_NUM, 2))

i = 0
for time in m3:
    r[i][0] = b[i][time]
    r[i][1] = time + 1
    
    i += 1

print(r)