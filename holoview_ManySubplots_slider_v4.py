################################################################################
# holoview, panel, bokeh server: hv.Image 여러개 동시 출력, slider 적용
# Simulation Results를 6개씩 그래프로 보기 가능
# Numpy file .npy를 읽어서 그래프 보여주기 기능
################################################################################

# from holoviews.operation.element import interpolate_curve
import numpy as np
# import pandas as pd
import holoviews as hv
# from holoviews.operation.datashader import regrid
# import hvplot.pandas
import panel as pn
import sys

hv.extension('bokeh')
# pn.config.sizing_mode="stretch_width"

# 한글 폰트 사용을 위해서 세팅
import matplotlib.font_manager as fm
from matplotlib import rc

font_path = "C:/Windows/Fonts/malgun.ttf"
font = fm.FontProperties(fname=font_path).get_name()
rc('font', family=font)

WIDTH, HEIGHT = 400, 300
#WIDTH, HEIGHT = 650, 500

def viewResults(media, interval):

    npy_filename = f'c:/CAM_test/OutFile/{media}_{interval}.npy'

    media_k = '대기' if media == 'Air' else '토양'
    if interval == '1hour_interval': time_u = '시간 단위' 
    else: time_u = '분 단위'

    print(f'{media_k} 매체 시뮬레이션 {time_u} 결과 자료를 읽어들이고 있습니다...')
    zarray = np.load(npy_filename)
    print(f'{media_k} 매체 시뮬레이션 {time_u} 결과 자료를 성공적으로 읽어서 변수에 할당하였습니다.')
    
    time_frames = zarray.shape[2]
    print(f'time_frames: {time_frames}')

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
        text4title = "시간"  # text4title = "Hourly"
    else: 
        time_type = 'minute'
        text4title = "분"   # text4title = "Minutely"

    # x, y ticks
    xticks = [1, 30, 60, 90, 120, 150]
    yticks = [1, 30, 60, 90, 120, 150]

    # holoviews Image ploting
    def get_image(frame):

        data = get_data(frame)
        
        if frame == 1: time_unit = time_type
        else: time_unit = time_type + 's'

        if media == 'Air': clabel = 'Conc.(ug/m3)'
        else: clabel = 'Conc.(ug/kg)'
            
        title = '{} {} 경과 후 농도 - 최대 농도: {}'.format(frame, text4title, conc_max[frame-1])
        # title = 'Results after {} {} - 최대 농도: {}'.format(frame, time_unit, conc_max[frame-1])
        
        img = hv.Image(data, bounds=bounds).opts(height=HEIGHT, width=WIDTH, 
                                    clim=(cmin, cmax),
                                    logz=True,
                                    colorbar=True, clabel=clabel,
                                    cmap='Plasma',   # 'RdBu_r'
                                    title=title,
                                    xticks=xticks, yticks=yticks,
                                    xlabel='Grid x', ylabel='Grid y', 
                                    tools=['hover'],
                                    toolbar='above',
                                    responsive=True
                                )
        """
        #inter_img = regrid(img, upsample=True, interpolation='bilinear')
        contour_img = hv.operation.contours(img, levels=10).opts(height=HEIGHT, width=WIDTH, 
                                    clim=(cmin, cmax),
                                    logz=True,
                                    colorbar=True, clabel='Conc.(ug/ml)',
                                    cmap='Plasma',   # 'RdBu_r'
                                    title=title,
                                    xticks=xticks, yticks=yticks,
                                    xlabel='Grid x', ylabel='Grid y', 
                                    tools=['hover'],
                                    toolbar='above',
                                    responsive=True
                                )
        img_box = (img + contour_img)
        """
        
        return img

    ### Time slider
    if time_frames > 6: 
        GRAPHs_in_COLUMN = 6   # slider step: slider step 갯수만큼 graph 생성. 결과 파일이 6개를 초과하면 6개씩 다중차트가 반복되도록 6으로 설정
    else:
        GRAPHs_in_COLUMN = time_frames  # 6보다 작으면 해당 숫자만큼 한줄에 표시되도록 설정
        
    slide_end = (time_frames // GRAPHs_in_COLUMN) * GRAPHs_in_COLUMN + 1
    frame_slider = pn.widgets.IntSlider(name="Time", value=1, start=1, end=slide_end, step=GRAPHs_in_COLUMN)

    G_COLUMN = 3  # Layout param.: 한 줄에 표시하는 Graph 수

    # Intslider의 value가 변하면 그에 해당하는 새로운 plot 생성
    @pn.depends(frame=frame_slider)
    def image(frame):
        diff = time_frames - frame
        if diff <= (GRAPHs_in_COLUMN-1): 
            frame_start = time_frames - GRAPHs_in_COLUMN + 1
            frame_end = time_frames + 1
        else: 
            frame_start = frame
            frame_end = frame + GRAPHs_in_COLUMN
        
        # print('start: {}, end: {}'.format(frame_start, frame_end))

        images = get_image(frame_start)
        for i in range(frame_start+1, frame_end):
            images += get_image(i)
        layout = (images).cols(G_COLUMN)
        return layout

    # slider 적용된 DynamicMap을 image에 적용
    img_dmap = hv.DynamicMap(image)

    # html head: app_bar
    app_bar = pn.Row(
        pn.pane.Markdown("## {} 매체 - {} 단위 모형 결과".format(media, text4title), style={"color": "white"}, 
                        width=1000, height=40, sizing_mode="fixed", margin=(5,5,5,5)), 
        # pn.pane.Markdown("## {} Simulation Results - {}".format(text4title, media), style={"color": "white"}, 
        #                width=1000, height=40, sizing_mode="fixed", margin=(5,5,5,5)), 
        # pn.Spacer(),
        background="black",
    )

    # stopping server button event
    def ss_event(event):
        sys.exit()  # Stop the server
    # button 생성, button click시 event 할당
    btn_close = pn.widgets.Button(name='Close', width=150)
    btn_close.on_click(ss_event)
    widgets_ss = pn.Column(pn.Spacer(height=1), btn_close)
    # widgets_ss = pn.Column(pn.Spacer(height=15), btn_close)

    # dashboard setting    
    app = pn.Column(
        pn.Row(app_bar, widgets_ss),
        frame_slider,
        #pn.Row(plot_image1, pn.Spacer(height=10)),
        img_dmap,
    )

    # view dashboard in webbrowser
    app.show()

if __name__ == '__main__':
    
    argument = sys.argv
    del argument[0]			# 첫번째 인자는 script.py 즉 실행시킨 파일명이 되기 때문에 지운다
    # print('Argument : {}'.format(argument))
    print('모형 결과를 읽어들이는 시간이 오래 걸립니다. 잠시만 기다려 주세요...')

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