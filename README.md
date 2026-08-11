# 서울 도시 열돔 현상 분석 앱

## 실행 방법
```
pip install -r requirements.txt
streamlit run app.py
```

## 데이터
- `data/seoul_gu_temperature.csv`: 서울 25개 구, 7·8월 평균/최고/최저기온 + 지역유형(한강변/산근처/강남도심/일반주거)
- `data/heat_dome_mechanism.csv`: 7/1~8/31 일별 기온·해면기압·일사량·상대습도·풍속·오존농도·열지수

현재 CSV는 실제 관측 경향을 반영해 만든 **샘플 데이터**입니다.
기상자료개방포털(data.kma.go.kr)의 실제 관측값으로 교체하려면,
같은 컬럼명(위 목록)만 유지한 CSV를 사이드바에서 업로드하면 됩니다.
샘플을 다시 생성하려면 `python data/generate_sample_data.py` 실행.
