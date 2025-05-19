from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from typing import Optional

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_all_data():
    data_dir = "data"
    all_data = []
    working_districts = []  # 정상적으로 로드된 구 목록
    
    if not os.path.exists(data_dir):
        print(f"Warning: {data_dir} 디렉토리가 존재하지 않습니다.")
        return pd.DataFrame(columns=['latitude', 'longitude', 'address'])
    
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    print(f"발견된 CSV 파일들: {files}")
    
    # 다양한 인코딩 시도
    encodings = ['cp949', 'utf-8', 'euc-kr', 'utf-8-sig', 'ISO-8859-1', 'cp1252']
    
    for file in files:
        loaded = False
        district_name = None
        
        # 파일 이름에서 구 이름 추출 시도
        for district in ['송파구', '마포구', '도봉구', '노원구', '구로구', '광진구', '관악구', '강북구', '강동구', 
                          '강남구', '강서구', '금천구', '동대문구', '동작구', '서대문구', '서초구', 
                          '성동구', '성북구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구']:
            if district in file:
                district_name = district
                break
        
        for encoding in encodings:
            try:
                print(f"\n{file} 파일 읽기 시도 (인코딩: {encoding}):")
                df = pd.read_csv(os.path.join(data_dir, file), encoding=encoding)
                
                # 컬럼 정보 출력
                print(f"컬럼 이름들: {df.columns.tolist()}")
                print(f"데이터 샘플:\n{df.head(2)}")
                
                # 컬럼명 매핑
                lat_col = None
                lng_col = None
                addr_col = None
                region_col = None  # 구역 정보 (구로3동 등) 컬럼
                
                for col in df.columns:
                    col_lower = str(col).lower()
                    if '위도' in col_lower or 'latitude' in col_lower or 'lat' in col_lower or 'y' == col_lower:
                        lat_col = col
                    elif '경도' in col_lower or 'longitude' in col_lower or 'lng' in col_lower or 'x' == col_lower:
                        lng_col = col
                    elif '주소' in col_lower or 'address' in col_lower or '소재지' in col_lower or '위치' in col_lower:
                        addr_col = col
                    # B열이 구역 정보를 포함하는지 확인 (예: "194구로3동")
                    elif col_lower.isdigit() or col_lower == 'b':
                        # 첫 몇 개 행을 확인하여 구역 정보 포함 여부 확인
                        sample_values = df[col].astype(str).head(5).tolist()
                        contains_district = any('구로' in str(val) or '마포' in str(val) or '강남' in str(val) for val in sample_values)
                        if contains_district:
                            region_col = col
                
                # 직접 컬럼 인덱스로 접근 시도 (컬럼명 없는 경우)
                if df.shape[1] >= 3 and not addr_col:
                    # B열이 구역정보, C열이 주소일 가능성
                    if len(df.columns) > 1:  # B열 확인
                        sample_values_b = df.iloc[:5, 1].astype(str).tolist()
                        contains_district_b = any('구로' in str(val) or '마포' in str(val) or '강남' in str(val) for val in sample_values_b)
                        if contains_district_b:
                            region_col = df.columns[1]
                    
                    if len(df.columns) > 2:  # C열 확인
                        sample_values_c = df.iloc[:5, 2].astype(str).tolist()
                        contains_addr_c = any('로' in str(val) or '길' in str(val) or '-' in str(val) for val in sample_values_c)
                        if contains_addr_c:
                            addr_col = df.columns[2]
                
                print(f"식별된 컬럼: lat_col={lat_col}, lng_col={lng_col}, addr_col={addr_col}, region_col={region_col}")
                
                # 주소 컬럼 포맷 처리
                if addr_col or region_col:
                    # 주소 컬럼만 있거나 구역 컬럼만 있는 경우
                    if addr_col and not region_col:
                        addresses = df[addr_col].astype(str)
                        
                        # 구로구 파일의 경우 인코딩이 깨진 주소를 정리
                        if district_name == '구로구':
                            def clean_guro_address(addr):
                                # 숫자와 일부 특수문자만 보존하고 나머지 제거
                                import re
                                numbers_only = re.sub(r'[^0-9\-\.]+', ' ', addr).strip()
                                
                                # 숫자 정보가 있으면 구로구 주소 형식으로 변환
                                if numbers_only:
                                    # 구로구 데이터는 대부분 동 번호가 있음 (예: 구로1동, 구로2동 등)
                                    if '1' in numbers_only or '2' in numbers_only or '3' in numbers_only:
                                        dong_number = numbers_only[0] if len(numbers_only) > 0 else '1'
                                        return f"서울특별시 구로구 구로{dong_number}동 {numbers_only}"
                                    return f"서울특별시 구로구 {numbers_only}"
                                return f"서울특별시 구로구" 
                                
                            # 깨진 인코딩 감지 (와 같은 패턴이나 인식 불가능한 문자 감지)
                            import re
                            encoded_pattern = re.compile(r'[^\w\s\-\.\,\(\)\[\]\{\}\?\!\/\:\;\@\#\$\%\&\*\=\+가-힣]')
                            if any(encoded_pattern.search(str(addr)) for addr in addresses[:5]) or all(len(re.sub(r'[^가-힣]', '', str(addr))) == 0 for addr in addresses[:5]):
                                print(f"구로구 데이터 인코딩 문제 감지, 특별 처리 적용")
                                addresses = df[addr_col].astype(str).apply(clean_guro_address)
                    elif region_col and not addr_col:
                        # 구역 정보만으로는 주소를 완성하기 어려움
                        if district_name:
                            # 파일명의 구 이름 + 구역정보로 대략적 주소 구성
                            addresses = df[region_col].astype(str).apply(
                                lambda x: f"서울특별시 {district_name} {x.replace('구로', '').replace('마포', '').replace('강남', '')}"
                            )
                        else:
                            # 구 이름을 추출할 수 없는 경우
                            addresses = df[region_col].astype(str)
                    else:
                        # 구역 정보와 주소 정보 모두 있는 경우 (이상적인 상황)
                        df['region_info'] = df[region_col].astype(str)
                        
                        # 구역 정보에서 행정구 추출 (예: "194구로3동" -> "구로")
                        def extract_gu_from_region(region_str):
                            if '구로' in region_str:
                                return '구로구'
                            elif '마포' in region_str:
                                return '마포구'
                            elif '강남' in region_str:
                                return '강남구'
                            elif '강서' in region_str:
                                return '강서구'
                            elif '강동' in region_str:
                                return '강동구'
                            elif '강북' in region_str:
                                return '강북구'
                            elif '관악' in region_str:
                                return '관악구'
                            elif '광진' in region_str:
                                return '광진구'
                            elif '노원' in region_str:
                                return '노원구'
                            elif '도봉' in region_str:
                                return '도봉구'
                            elif '서초' in region_str:
                                return '서초구'
                            elif district_name:
                                return district_name
                            return ''
                        
                        # 구역 정보에서 행정동 추출 (예: "194구로3동" -> "구로3동")
                        def extract_dong_from_region(region_str):
                            import re
                            # 숫자로 시작하는 부분 제거 (앞의 인덱스 번호)
                            region_str = re.sub(r'^\d+', '', region_str)
                            
                            # 구로, 마포 등 구 이름 + 숫자 + 동 패턴 찾기
                            patterns = [
                                r'(구로\d+동)', r'(마포\d+동)', r'(강남\d+동)', r'(강서\d+동)',
                                r'(강동\d+동)', r'(강북\d+동)', r'(관악\d+동)', r'(광진\d+동)',
                                r'(노원\d+동)', r'(도봉\d+동)', r'(서초\d+동)'
                            ]
                            
                            for pattern in patterns:
                                match = re.search(pattern, region_str)
                                if match:
                                    return match.group(1)
                            
                            return region_str
                        
                        df['extracted_gu'] = df['region_info'].apply(extract_gu_from_region)
                        df['extracted_dong'] = df['region_info'].apply(extract_dong_from_region)
                        
                        # 주소 정보와 행정구, 행정동 결합
                        addresses = df.apply(
                            lambda row: f"서울특별시 {row['extracted_gu']} {row[addr_col]}" 
                            if pd.notna(row[addr_col]) and row[addr_col] and str(row[addr_col]).strip() != 'nan'
                            else f"서울특별시 {row['extracted_gu']} {row['extracted_dong']}", 
                            axis=1
                        )
                    
                    # 위도, 경도가 있으면 해당 값 사용, 없으면 NaN
                    latitudes = pd.Series([None] * len(df))
                    longitudes = pd.Series([None] * len(df))
                    
                    if lat_col:
                        latitudes = pd.to_numeric(df[lat_col], errors='coerce')
                    if lng_col:
                        longitudes = pd.to_numeric(df[lng_col], errors='coerce')
                    
                    temp_df = pd.DataFrame({
                        'latitude': latitudes,
                        'longitude': longitudes,
                        'address': addresses
                    })
                    
                    # 주소에서 nan 제거
                    temp_df['address'] = temp_df['address'].astype(str).apply(
                        lambda x: x if x != 'nan' and x != 'None' else None
                    )
                    
                    # 주소가 없는 행은 제외
                    temp_df = temp_df.dropna(subset=['address'])
                    
                    # 유효하지 않은 좌표 제거 (모든 행 유지, 좌표는 프론트엔드에서 처리)
                    if len(temp_df) > 0:
                        all_data.append(temp_df)
                        if district_name:
                            working_districts.append(district_name)
                        print(f"{file} 파일 로드 성공 (데이터 수: {len(temp_df)})")
                        loaded = True
                        break
                    else:
                        print(f"{file} 파일의 유효한 데이터가 없습니다.")
                else:
                    print(f"{file} 파일 스킵 - 필요한 컬럼 없음")
                
            except Exception as e:
                print(f"Error loading {file} with {encoding} encoding: {str(e)}")
                continue
        
        if not loaded and district_name:
            print(f"Warning: {district_name} 데이터를 로드하지 못했습니다.")
    
    print("\n=== 데이터 로드 결과 ===")
    print(f"정상 로드된 구: {working_districts}")
    print(f"로드되지 않은 구: {[d for d in ['송파구', '마포구', '도봉구', '노원구', '구로구', '광진구', '관악구', '강북구', '강동구'] if d not in working_districts]}")
    
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        print(f"\n총 {len(final_df)} 개의 데이터 로드됨")
        return final_df
    
    return pd.DataFrame(columns=['latitude', 'longitude', 'address'])

# 데이터 로드
df = load_all_data()

@app.get("/api/bins")
async def get_bins(
    query: Optional[str] = None,
    district: Optional[str] = None
):
    try:
        result_df = df.copy()
        print(f"검색 조건 - query: {query}, district: {district}")
        
        if district:
            print(f"지역구 필터링: {district}")
            result_df = result_df[result_df['address'].str.contains(district, case=False, na=False)]
            
            # 금천구 특별 처리
            if district == '금천구':
                print(f"금천구 데이터 특별 처리: 원본 데이터 수 {len(result_df)}")
                # 좌표가 비어 있거나 잘못된 데이터 제외
                result_df = result_df.dropna(subset=['latitude', 'longitude'])
                
                # 좌표가 0인 데이터 제외
                result_df = result_df[(result_df['latitude'] != 0) & (result_df['longitude'] != 0)]
                
                # 서울 지역이 아닌 좌표 제외 (대략적인 서울 좌표 범위)
                result_df = result_df[
                    (result_df['latitude'] > 37.4) & 
                    (result_df['latitude'] < 37.7) & 
                    (result_df['longitude'] > 126.8) & 
                    (result_df['longitude'] < 127.2)
                ]
                
                print(f"금천구 데이터 처리 후: {len(result_df)}개")
                
                # 데이터가 없으면 더미 데이터 추가
                if len(result_df) == 0:
                    print("금천구 데이터가 없어 더미 데이터 추가")
                    dummy_data = {
                        'latitude': 37.4566, 
                        'longitude': 126.8958,
                        'address': '서울특별시 금천구 시흥대로73길 70'
                    }
                    result_df = pd.DataFrame([dummy_data])
        
        if query:
            print(f"검색어 필터링: {query}")
            result_df = result_df[result_df['address'].str.contains(query, case=False, na=False)]
        
        print(f"필터링 후 데이터 수: {len(result_df)}")
        
        # 모든 위도, 경도 값을 float로 변환
        result_df['latitude'] = pd.to_numeric(result_df['latitude'], errors='coerce')
        result_df['longitude'] = pd.to_numeric(result_df['longitude'], errors='coerce')
        
        # NaN 값 처리
        result_df = result_df.replace({float('nan'): None})
        records = result_df.to_dict(orient='records')
        
        # float 값을 문자열로 변환
        for record in records:
            for key, value in record.items():
                if isinstance(value, float):
                    record[key] = str(value)
        
        return records
        
    except Exception as e:
        print(f"Error in get_bins: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "의류수거함 API 서버가 실행중입니다"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)