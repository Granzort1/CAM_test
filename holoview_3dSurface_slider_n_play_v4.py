################################################################################
# holoview, panel, plotly: (hv.Surface(3d)) Slider
# Simulation Results 적용. 660개 파일 보기 가능
# Slider 자동 실행 기능 추가: play, pause 버튼
# Slider는 마우스 또는 키보드로 이동
# Numpy file .npy를 읽어서 그래프 보여주기 기능
# Good~
################################################################################

import numpy as np
import holoviews as hv
import panel as pn
import sys

hv.extension('plotly')
# pn.config.sizing_mode="stretch_width"

# 한글 폰트 사용을 위해서 세팅
import matplotlib.font_manager as fm
from matplotlib import rc

font_path = "C:/Windows/Fonts/malgun.ttf"
font = fm.FontProperties(fname=font_path).get_name()
rc('font', family=font)

WIDTH, HEIGHT = 650, 550

def viewResults(media, interval):

    npy_filename = f'c:/CAM_test/OutFile/{media}_{interval}.npy'

    media_k = '대기' if media == 'Air' else '토양'
    if interval == '1hour_interval': time_u = '시간 단위' 
    else: time_u = '분 단위'

    print(f'{media_k} 매체 시뮬레이션 {time_u} 결과 자료를 읽어들이고 있습니다...')
    zarray = np.load(npy_filename)
    print(f'{media_k} 매체 시뮬레이션 {time_u} 결과 자료를 성공적으로 읽어서 변수에 할당하였습니다.')
    
    time_frames = zarray.shape[2]

    # result conc.를 저장하기 위한 numpy 변수 생성
    conc = np.zeros((22500, time_frames))

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

    # 전체 결과 농도의 최소, 최대값 할당
    vmin = np.min(np.array([conc]))
    vmax = np.max(np.array([conc]))

    # data 생성
    def get_data(frame):
        return zarray[:,:,frame-1]

    # bounds
    bounds = (1, 1, 150, 150)

    # opts
    cmin = 0.000000001
    cmax = 0.1

    # time unit 선택
    if interval == '1hour_interval': 
        time_type = 'hour'
        time_unit = '시간'
        text4title = "시간 단위"
        # text4title = "Hourly"
        callback_period = 750
    else: 
        time_type = 'minute'
        time_unit = '분'
        text4title = "분 단위"
        # text4title = "Minutely"
        callback_period = 200

    # x, y ticks
    xticks = [1, 30, 60, 90, 120, 150]
    yticks = [1, 30, 60, 90, 120, 150]

    # holoviews Image ploting
    def get_image(frame):

        data = get_data(frame)
        
        # if frame == 1: time_unit = time_type
        # else: time_unit = time_type + 's'
            
        title = '{} {} 경과 후 농도 - 최대 농도: {}'.format(frame, time_unit, conc_max[frame-1])
        # title = 'Results after {} {} - Max Conc.: {}'.format(frame, time_unit, conc_max[frame-1])
        
        surface = hv.Surface(data, bounds=bounds)

        surface.opts(
                title=title, 
                xlim=(1,150),
                ylim=(1,150),
                invert_xaxis=True,
                clim=(cmin, cmax),
                colorbar=True, cmap='RdBu_r', 
                height=HEIGHT, width=WIDTH, 
                )
        #surface.opts(colorbar=True, cmap='RdBu_r', height=HEIGHT, width=WIDTH)

        return surface

    get_image(1)

    # html head: app_bar
    app_bar = pn.Row(
        pn.pane.Markdown("## {} Simulation Results - {}".format(text4title, media), style={"color": "white"}, 
                        width=1000, height=40, sizing_mode="fixed", margin=(5,5,5,5)), 
        # pn.Spacer(),
        background="black",
    )
    app_bar

    # Define custom widgets
    # animation update용 slider value 증가. end에 도달하면 start로 이동하여 다시 animation 시작
    start, end = 1, time_frames
    def animate_update():
        time = frame_slider.value + 1
        if time > end:
            time = int(start)
        frame_slider.value = time

    def animate(event):
        if button.name == '► Play':
            button.name = '❚❚ Pause'
            callback.start()
        else:
            button.name = '► Play'
            callback.stop()

    # Time slider
    frame_slider = pn.widgets.IntSlider(name="Time", 
                                value=1, start=start, end=end, 
                                width=900)

    button = pn.widgets.Button(name='► Play', width=150, align='end')
    button.on_click(animate)
    callback = pn.state.add_periodic_callback(animate_update, callback_period, start=False)

    # stopping server button event
    def ss_event(event):
        sys.exit()  # Stop the server
    # button 생성, button click시 event 할당
    btn_close = pn.widgets.Button(name='Close', width=150)
    btn_close.on_click(ss_event)
    widgets_ss = pn.Column(pn.Spacer(height=1), btn_close)
    # widgets_ss = pn.Column(pn.Spacer(height=15), btn_close)


    # Intslider의 value가 변하면 그에 해당하는 새로운 plot 생성
    @pn.depends(frame=frame_slider)
    def image(frame):
        return get_image(frame)

    # slider 적용된 DynamicMap을 image에 적용
    img_dmap = hv.DynamicMap(image)
    
    # dashboard setting    
    app = pn.Column(
        pn.Row(app_bar, widgets_ss),
        pn.Spacer(height=5),
        pn.Row(
            pn.Column(
                # pn.Spacer(height=5),
                img_dmap,
                pn.Spacer(height=15),
            ),
        ),
        pn.Row(
            frame_slider, 
            button, 
        ),
    )

    app.show()

if __name__ == '__main__':
    
    argument = sys.argv
    del argument[0]			# 첫번째 인자는 script.py 즉 실행시킨 파일명이 되기 때문에 지운다
    print('모형 결과를 읽어들이는 시간이 오래 걸립니다. 잠시만 기다려 주세요...')
    # print('It takes time to load simulation results. Please wait a moment...')

    if len(argument) == 2:
        viewResults(argument[0], argument[1])
    else:
        print('입력인자가 올바르지 않습니다. c:/ArcGISpro/bin/Python/envs/arcgispro-py3/python.exe c:/CAM_test/pyWin4MMM/viewModelResults.py Air 1hour_interval 양식으로 입력하세요.')
    
    """
    viewResults('Air', '1hour_interval')
    # viewResults('Soil', '1hour_interval')
    # viewResults('Air', '1minute_interval')
    # viewResults('Soil', '1minute_interval')
    """