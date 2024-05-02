### 주소 검색 모듈 ###

from urllib.parse import quote_plus, urlencode
from urllib.request import urlopen, Request
import xml.etree.ElementTree as ET
import json
# import sqlite3

def findAddress(keystr):

    #print("\n" + "-"*100)
    #print('\n도로명주소 검색 API 서비스를 이용한 주소 검색 서비스입니다. ')
    #keystr = input('\n검색어를 입력하세요 (예: 세종로 11 또는 건물명) : ')
    resulttype= 'json'

    url = 'http://www.juso.go.kr/addrlink/addrLinkApi.do'
    queryParams = '?' + urlencode({ quote_plus('currentPage') : '1' , quote_plus('countPerPage') : '10', quote_plus('resultType') : resulttype, quote_plus('keyword') : keystr, quote_plus('confmKey') : 'bGk3MHZtMWJ2anNkODIwMTQwOTEyMTg0NDI2' })

    request = Request(url + queryParams)
    request.get_method = lambda: 'GET'
    response_body = urlopen(request).read()

    root_json = json.loads(response_body)

    total_count = int(root_json['results']['common']['totalCount'])

    if total_count > 10:
        print("검색어에 해당하는 주소가 너무 많습니다. 검색어를 상세하게 입력하여 다시 검색하시기 바랍니다. ")
        address = ['9999', '검색어에 해당하는 주소가 너무 많습니다. 검색어를 상세하게 입력하여 다시 검색하시기 바랍니다. ']
        return address
    elif total_count < 1:
        print("검색어에 해당하는 주소가 없습니다. 검색어를 상세하게 입력하여 다시 검색하시기 바랍니다. ")
        address = ['9999', '검색어에 해당하는 주소가 없습니다. 검색어를 상세하게 입력하여 다시 검색하시기 바랍니다. ']
        return address
    else:
        #print("url = " + url)
        print("요청한 검색어 = " + keystr)
        print("="*100)

        print('<< results >>')
        print('totalCount   : ' + root_json['results']['common']['totalCount'])
        print('currentPage  : ' + root_json['results']['common']['currentPage'])
        print('countPerPage : ' + root_json['results']['common']['countPerPage'])
        print('errorCode    : ' + root_json['results']['common']['errorCode'])
        print('errorMessage : ' + root_json['results']['common']['errorMessage'])

        address = []

        for child in root_json['results']['juso']:
            print('-'*100)
            print('[' + child['zipNo'] + '] '      + child['roadAddr'])

            addRoad = child['roadAddrPart1']
            if addRoad.find('지하') < 0:
                address.append(child['roadAddrPart1'])
            
            print('    도로명주소(참고항목 제외) = ' + child['roadAddrPart1'])
            print('    지번주소                 = ' + child['jibunAddr'])
            #print('    도로명코드   = '             + child['rnMgtSn'])
            #print('    건물관리번호 = '             + child['bdMgtSn'])
            #print('    법정동코드   = '             + child['admCd'])
            #print('    상세건물명   = '             + child['detBdNmList'])
            print('')

        return address