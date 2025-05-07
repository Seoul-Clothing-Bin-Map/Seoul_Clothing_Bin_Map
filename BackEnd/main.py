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
    encodings = ['cp949', 'utf-8', 'euc-kr']
    
    for file in files:
        loaded = False
        district_name = None
        
        # 파일 이름에서 구 이름 추출 시도
        for district in ['송파구', '마포구', '도봉구', '노원구', '구로구', '광진구', '관악구', '강북구', '강동구']:
            if district in file:
                district_name = district
                break
        
        for encoding in encodings:
            try:
                print(f"\n{file} 파일 읽기 시도 (인코딩: {encoding}):")
                df = pd.read_csv(os.path.join(data_dir, file), encoding=encoding)
                
                # 컬럼명 매핑
                lat_col = None
                lng_col = None
                addr_col = None
                
                for col in df.columns:
                    col_lower = str(col).lower()
                    if '위도' in col_lower or 'latitude' in col_lower or 'lat' in col_lower or 'y' == col_lower:
                        lat_col = col
                    elif '경도' in col_lower or 'longitude' in col_lower or 'lng' in col_lower or 'x' == col_lower:
                        lng_col = col
                    elif '주소' in col_lower or 'address' in col_lower or '소재지' in col_lower or '위치' in col_lower:
                        addr_col = col
                
                if lat_col and lng_col and addr_col:
                    print(f"필요한 컬럼 발견: 위도={lat_col}, 경도={lng_col}, 주소={addr_col}")
                    
                    temp_df = pd.DataFrame({
                        'latitude': pd.to_numeric(df[lat_col], errors='coerce'),
                        'longitude': pd.to_numeric(df[lng_col], errors='coerce'),
                        'address': df[addr_col]
                    })
                    
                    # 유효하지 않은 좌표 제거
                    temp_df = temp_df.dropna(subset=['latitude', 'longitude'])
                    
                    # 좌표 범위 확인 (서울시 범위)
                    temp_df = temp_df[
                        (temp_df['latitude'] >= 37.4) & 
                        (temp_df['latitude'] <= 37.7) & 
                        (temp_df['longitude'] >= 126.8) & 
                        (temp_df['longitude'] <= 127.2)
                    ]
                    
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
        
        if query:
            print(f"검색어 필터링: {query}")
            result_df = result_df[result_df['address'].str.contains(query, case=False, na=False)]
        
        print(f"필터링 후 데이터 수: {len(result_df)}")
        
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