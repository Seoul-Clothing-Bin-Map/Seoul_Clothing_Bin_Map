# 서울시 의류수거함 지도제작 프로젝트

서울시에 설치되어있는 의류수거함의 위치를 알려주는 지도를 제작하는 프로젝트입니다.

# FrontEnd 주요 의존성
  - React 18.2.0
  - Axios (API 통신)
  - TailwindCSS + DaisyUI (UI 프레임워크)

#  주요 파일들:
  - App.js: 메인 애플리케이션 로직
  - index.js: React 앱의 진입점
  - index.css: Tailwind CSS 스타일

# 사용 데이터
  - 카카오맵 API
  - 네이버 지도 연동
  - 공공 데이터 포털, 서울시 구청별 의류수거함 CSV

#BackEnd 주요 의존성
  
  - FastAPI
  - pandas
  - uvicorn  
  - chardet

# 주요 기능

  - CSV 파일에서 의류 수거함 데이터 로드
  - 위치 데이터 정제 및 표준화
  - REST API 엔드포인트 제공

# 주요 기능 설명

○ FastAPI
  - Python에서 HTTP 기반 서비스 API를 구축하기 위한 웹 프레임워크

○ 데이터 로드 및 정제:
  - 다양한 인코딩 지원 (cp949, utf-8, euc-kr 등)
  - 주소 데이터 표준화
  - 위도/경도 데이터 검증
  - 구별 데이터 관리

○ API 엔드포인트
  - /api/bins: 의류 수거함 위치 데이터 조회
  - 검색 및 필터링 기능 지원

# 실행 방법

 ○ 백엔드 실행

 1. 의존성 설치
    cd backend
    pip install -r requirements.txt
 2. 서버 실행
    uvicorn main:app --reload

 ○ 프론트엔드 실행

  1. 의존성 설치
    cd frontend
    npm install

  2. 개발 서버 실행
    npm start

# 지도 사용방법
  - 서울시 각 행정구별 필터를 이용하거나 검색창에 행정구를 검색, 또는 자신이 원하는 위치에 있는 의류수거함 정보를 얻고 싶을시 주소명으로 검색 [ex) 가마산로54길]

# 데이터 출처
  - 공공데이터포털
  - 서울시 각 구청


