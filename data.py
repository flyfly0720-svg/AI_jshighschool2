# -*- coding: utf-8 -*-
"""
샘플 데이터 생성 스크립트
------------------------------------------------------------
실제 관측 데이터(기상자료개방포털 data.kma.go.kr 등)를 구하기 전까지
앱을 바로 실행하고 구조를 확인할 수 있도록, 실제 서울 열섬 현상의
경향(강남 도심부 고온, 한강변 완화, 산 근접지역 저온)을 반영한
합성(synthetic) 데이터를 생성한다.

나중에 실제 데이터로 교체할 때는 아래 두 파일과 동일한 컬럼 구조를
유지하면 app.py 수정 없이 그대로 사용할 수 있다.
    - seoul_gu_temperature.csv
    - heat_dome_mechanism.csv
"""

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

# ------------------------------------------------------------------
# 1) 서울 25개 구 + 지역 유형 매핑
# ------------------------------------------------------------------
GU_REGION_TYPE = {
    # 강남 도심(열섬 핵심부)
    "강남구": "강남도심", "서초구": "강남도심", "중구": "강남도심",
    # 한강변
    "마포구": "한강변", "용산구": "한강변", "영등포구": "한강변",
    "광진구": "한강변", "강동구": "한강변", "송파구": "한강변",
    "성동구": "한강변", "강서구": "한강변",
    # 산 인접
    "은평구": "산근처", "종로구": "산근처", "성북구": "산근처",
    "도봉구": "산근처", "노원구": "산근처", "관악구": "산근처",
    "강북구": "산근처", "서대문구": "산근처",
    # 일반 주거지역(비교군)
    "구로구": "일반주거", "금천구": "일반주거", "동대문구": "일반주거",
    "동작구": "일반주거", "양천구": "일반주거", "중랑구": "일반주거",
}

# 구 중심 대략 위경도 (folium/plotly 지도 확장 대비)
GU_COORD = {
    "강남구": (37.5172, 127.0473), "강동구": (37.5301, 127.1238),
    "강북구": (37.6396, 127.0257), "강서구": (37.5509, 126.8495),
    "관악구": (37.4784, 126.9516), "광진구": (37.5384, 127.0822),
    "구로구": (37.4954, 126.8874), "금천구": (37.4569, 126.8956),
    "노원구": (37.6542, 127.0568), "도봉구": (37.6688, 127.0471),
    "동대문구": (37.5744, 127.0396), "동작구": (37.5124, 126.9393),
    "마포구": (37.5663, 126.9019), "서대문구": (37.5791, 126.9368),
    "서초구": (37.4837, 127.0324), "성동구": (37.5633, 127.0364),
    "성북구": (37.5894, 127.0167), "송파구": (37.5145, 127.1059),
    "양천구": (37.5169, 126.8664), "영등포구": (37.5264, 126.8963),
    "용산구": (37.5326, 126.9905), "은평구": (37.6027, 126.9291),
    "종로구": (37.5735, 126.9790), "중구": (37.5641, 126.9979),
    "중랑구": (37.6063, 127.0925),
}

# 지역 유형별 기준 편차(도심 대비, ℃). 실제 서울 열섬 연구의 경향을 참고한 근사치.
TYPE_OFFSET = {
    "강남도심": {"mean": 1.4, "max": 1.8, "min": 1.6},   # 열섬 심화: 낮·밤 모두 고온
    "한강변":   {"mean": -0.5, "max": -0.3, "min": -0.9},  # 수변 냉각 + 야간 바람길
    "산근처":   {"mean": -1.1, "max": -1.4, "min": -1.0},  # 식생·고도 효과
    "일반주거": {"mean": 0.0, "max": 0.0, "min": 0.0},
}

# 월별 서울 평년 기준값(기상청 평년값 근사, ℃)
MONTH_BASE = {
    7: {"mean": 25.9, "max": 29.6, "min": 22.9},
    8: {"mean": 26.8, "max": 30.6, "min": 24.0},
}

rows = []
for gu, rtype in GU_REGION_TYPE.items():
    lat, lon = GU_COORD[gu]
    off = TYPE_OFFSET[rtype]
    for month, base in MONTH_BASE.items():
        noise = rng.normal(0, 0.35)
        mean_t = base["mean"] + off["mean"] + noise
        max_t = base["max"] + off["max"] + noise + rng.normal(0, 0.4)
        min_t = base["min"] + off["min"] + noise + rng.normal(0, 0.3)
        # 최고>=평균>=최저 물리적 정합성 보정
        max_t = max(max_t, mean_t + 1.5)
        min_t = min(min_t, mean_t - 1.5)
        rows.append({
            "구": gu,
            "지역유형": rtype,
            "월": month,
            "평균기온": round(mean_t, 1),
            "최고기온": round(max_t, 1),
            "최저기온": round(min_t, 1),
            "위도": lat,
            "경도": lon,
        })

df_gu = pd.DataFrame(rows)
df_gu.to_csv("seoul_gu_temperature.csv", index=False, encoding="utf-8-sig")
print("seoul_gu_temperature.csv 생성 완료:", df_gu.shape)

# ------------------------------------------------------------------
# 2) 열돔 현상 설명용 일별 기후 데이터 (7/1 ~ 8/31)
#    메커니즘: 상층 고기압 정체 → 하강기류(단열압축승온) → 맑고 강한 일사
#    → 지표 가열 → 낮은 풍속으로 열 정체 → 오존 등 광화학 스모그 심화
# ------------------------------------------------------------------
dates = pd.date_range("2025-07-01", "2025-08-31", freq="D")
n = len(dates)

t = np.arange(n)
# 폭염(열돔) 구간을 하나 만들어 상관관계가 뚜렷하게 보이도록 함 (7/20~8/10 경)
heat_dome_intensity = np.clip(
    np.exp(-0.5 * ((t - 35) / 10) ** 2) * 1.0, 0, 1
)  # 0~1, 폭염 절정 구간에서 1에 가까움

sea_level_pressure = 1006 + 6 * heat_dome_intensity + rng.normal(0, 1.5, n)  # hPa, 고기압 강화
solar_radiation = 18 + 8 * heat_dome_intensity + rng.normal(0, 1.8, n)       # MJ/m^2/day
wind_speed = 2.6 - 1.4 * heat_dome_intensity + rng.normal(0, 0.3, n)         # m/s, 정체
wind_speed = np.clip(wind_speed, 0.3, None)
humidity = 72 - 12 * heat_dome_intensity + rng.normal(0, 4, n)              # %, 하강기류로 건조
humidity = np.clip(humidity, 35, 95)
ozone = 30 + 25 * heat_dome_intensity + rng.normal(0, 3, n)                 # ppb, 광화학 반응 심화
ozone = np.clip(ozone, 10, None)

temperature = 26.2 + 6.5 * heat_dome_intensity + rng.normal(0, 0.8, n)      # 일평균기온

# 열지수(체감온도) 근사식 (섭씨, 단순화된 근사)
heat_index = temperature + 0.05 * (humidity - 50) + 0.3 * heat_dome_intensity * 10

df_climate = pd.DataFrame({
    "날짜": dates,
    "기온": np.round(temperature, 1),
    "해면기압": np.round(sea_level_pressure, 1),
    "일사량": np.round(solar_radiation, 2),
    "상대습도": np.round(humidity, 1),
    "풍속": np.round(wind_speed, 2),
    "오존농도": np.round(ozone, 1),
    "열지수": np.round(heat_index, 1),
})
df_climate.to_csv("heat_dome_mechanism.csv", index=False, encoding="utf-8-sig")
print("heat_dome_mechanism.csv 생성 완료:", df_climate.shape)
