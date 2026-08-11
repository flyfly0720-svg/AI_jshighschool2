
# -*- coding: utf-8 -*-
"""
서울 도시 열돔(Urban Heat Dome) 현상 데이터 분석 웹앱
------------------------------------------------------------
1. 서울 25개 구 7·8월 평균/최고/최저 기온 비교
2. 지역 유형(한강변 / 산 근처 / 강남 도심 / 일반주거) 비교 분석
3. 열돔 현상 메커니즘 설명을 위한 기후 데이터(기압·일사량·풍속·오존 등) 분석
------------------------------------------------------------
실행:
    pip install -r requirements.txt
    streamlit run app.py
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ------------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------------
st.set_page_config(
    page_title="서울 도시 열돔 현상 분석",
    page_icon="🌡️",
    layout="wide",
)

GU_CSV_PATH = "data/seoul_gu_temperature.csv"
CLIMATE_CSV_PATH = "data/heat_dome_mechanism.csv"

REGION_TYPE_ORDER = ["한강변", "일반주거", "산근처", "강남도심"]
REGION_COLOR_MAP = {
    "강남도심": "#e45756",
    "한강변": "#4c78a8",
    "산근처": "#54a24b",
    "일반주거": "#b0b0b0",
}


# ------------------------------------------------------------------
# 데이터 로딩
# ------------------------------------------------------------------
@st.cache_data
def load_gu_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    required_cols = {"구", "지역유형", "월", "평균기온", "최고기온", "최저기온"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"구별 데이터에 필수 컬럼이 없습니다: {missing}")
    return df


@st.cache_data
def load_climate_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    required_cols = {"날짜", "기온", "해면기압", "일사량", "상대습도", "풍속", "오존농도"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"기후 데이터에 필수 컬럼이 없습니다: {missing}")
    df["날짜"] = pd.to_datetime(df["날짜"])
    return df


def get_uploaded_or_default(label: str, default_path: str, loader):
    uploaded = st.sidebar.file_uploader(label, type=["csv"], key=default_path)
    try:
        if uploaded is not None:
            if "gu" in default_path:
                df = pd.read_csv(uploaded, encoding="utf-8-sig")
            else:
                df = pd.read_csv(uploaded, encoding="utf-8-sig")
                df["날짜"] = pd.to_datetime(df["날짜"])
            return df
        return loader(default_path)
    except Exception as e:
        st.sidebar.error(f"파일을 불러오는 중 오류가 발생했습니다: {e}")
        return loader(default_path)


st.sidebar.title("📁 데이터 설정")
st.sidebar.caption("직접 CSV를 업로드하면 샘플 데이터 대신 사용됩니다. (컬럼 구조는 샘플과 동일해야 합니다)")

gu_df = get_uploaded_or_default("구별 기온 CSV 업로드", GU_CSV_PATH, load_gu_data)
climate_df = get_uploaded_or_default("열돔 기후 CSV 업로드", CLIMATE_CSV_PATH, load_climate_data)

# ------------------------------------------------------------------
# 사이드바 필터
# ------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.title("🔎 필터")

month_options = sorted(gu_df["월"].unique().tolist())
month_labels = {m: f"{m}월" for m in month_options}
selected_months = st.sidebar.multiselect(
    "월 선택",
    options=month_options,
    default=month_options,
    format_func=lambda m: month_labels[m],
)

region_types_available = [r for r in REGION_TYPE_ORDER if r in gu_df["지역유형"].unique()]
selected_types = st.sidebar.multiselect(
    "지역 유형 선택",
    options=region_types_available,
    default=region_types_available,
)

if not selected_months:
    st.sidebar.warning("최소 한 개 이상의 월을 선택해주세요.")
    st.stop()
if not selected_types:
    st.sidebar.warning("최소 한 개 이상의 지역 유형을 선택해주세요.")
    st.stop()

filtered_gu = gu_df[gu_df["월"].isin(selected_months) & gu_df["지역유형"].isin(selected_types)].copy()
filtered_gu["월_label"] = filtered_gu["월"].map(month_labels)

# ------------------------------------------------------------------
# 헤더
# ------------------------------------------------------------------
st.title("🌡️ 서울 도시 열돔(Urban Heat Dome) 현상 데이터 분석")
st.markdown(
    "서울 25개 자치구의 여름철(7·8월) 기온 데이터를 기반으로 **도심 열섬 효과**와 "
    "**열돔 현상의 형성 메커니즘**을 데이터로 살펴봅니다."
)

tab1, tab2, tab3 = st.tabs([
    "① 구별 기온 비교",
    "② 지역 유형별 비교 (한강변·산·강남도심)",
    "③ 열돔 현상 메커니즘 분석",
])

# ==================================================================
# TAB 1. 구별 기온 비교
# ==================================================================
with tab1:
    st.subheader("서울 25개 구 평균·최고·최저 기온")

    col1, col2 = st.columns([1, 1])
    with col1:
        metric = st.radio(
            "표시할 지표",
            options=["평균기온", "최고기온", "최저기온"],
            horizontal=True,
        )
    with col2:
        sort_desc = st.checkbox("높은 순으로 정렬", value=True)

    agg_gu = (
        filtered_gu.groupby("구", as_index=False)
        .agg(
            평균기온=("평균기온", "mean"),
            최고기온=("최고기온", "max"),
            최저기온=("최저기온", "min"),
            지역유형=("지역유형", "first"),
        )
    )
    agg_gu = agg_gu.sort_values(metric, ascending=not sort_desc)

    fig_bar = px.bar(
        agg_gu,
        x="구",
        y=metric,
        color="지역유형",
        color_discrete_map=REGION_COLOR_MAP,
        category_orders={"구": agg_gu["구"].tolist()},
        text=metric,
        title=f"구별 {metric} (선택한 월 기준)",
    )
    fig_bar.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_bar.update_layout(xaxis_tickangle=-45, yaxis_title="온도 (℃)", height=520)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("#### 월별 · 구별 평균·최고·최저 기온 비교 (그룹 막대)")
    melt_gu = filtered_gu.melt(
        id_vars=["구", "지역유형", "월_label"],
        value_vars=["평균기온", "최고기온", "최저기온"],
        var_name="구분",
        value_name="온도",
    )
    fig_grouped = px.bar(
        melt_gu,
        x="구",
        y="온도",
        color="구분",
        barmode="group",
        facet_row="월_label" if len(selected_months) > 1 else None,
        title="구별 평균/최고/최저 기온",
        height=460 if len(selected_months) == 1 else 780,
    )
    fig_grouped.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_grouped, use_container_width=True)

    st.markdown("#### 구 × 월 히트맵 (평균기온)")
    heat_pivot = filtered_gu.pivot_table(index="구", columns="월_label", values="평균기온", aggfunc="mean")
    heat_pivot = heat_pivot.reindex(agg_gu["구"])
    fig_heat = px.imshow(
        heat_pivot,
        color_continuous_scale="YlOrRd",
        aspect="auto",
        labels=dict(color="평균기온(℃)"),
        title="구별 · 월별 평균기온 히트맵",
    )
    fig_heat.update_layout(height=650)
    st.plotly_chart(fig_heat, use_container_width=True)

# ==================================================================
# TAB 2. 지역 유형별 비교
# ==================================================================
with tab2:
    st.subheader("한강변 · 산 근처 · 강남 도심 · 일반주거 지역 비교")
    st.caption(
        "동일한 '도심 열섬'이라도 수변(한강)·녹지(산)·고밀도 도심(강남권)의 "
        "미기후(microclimate) 차이가 어떻게 나타나는지 비교합니다."
    )

    col1, col2 = st.columns(2)
    with col1:
        fig_box = px.box(
            filtered_gu,
            x="지역유형",
            y="평균기온",
            color="지역유형",
            color_discrete_map=REGION_COLOR_MAP,
            category_orders={"지역유형": [t for t in REGION_TYPE_ORDER if t in selected_types]},
            points="all",
            title="지역 유형별 평균기온 분포",
        )
        fig_box.update_layout(yaxis_title="평균기온 (℃)", showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

    with col2:
        type_summary = (
            filtered_gu.groupby("지역유형", as_index=False)
            .agg(평균기온=("평균기온", "mean"), 최고기온=("최고기온", "mean"), 최저기온=("최저기온", "mean"))
        )
        type_summary["지역유형"] = pd.Categorical(
            type_summary["지역유형"], categories=[t for t in REGION_TYPE_ORDER if t in selected_types], ordered=True
        )
        type_summary = type_summary.sort_values("지역유형")
        melt_type = type_summary.melt(id_vars="지역유형", var_name="구분", value_name="온도")
        fig_type_bar = px.bar(
            melt_type,
            x="지역유형",
            y="온도",
            color="구분",
            barmode="group",
            title="지역 유형별 평균/최고/최저 기온",
        )
        fig_type_bar.update_layout(yaxis_title="온도 (℃)")
        st.plotly_chart(fig_type_bar, use_container_width=True)

    st.markdown("#### 도심 열섬 강도(Heat Island Intensity) — 강남도심 대비 온도 차")
    if "강남도심" in filtered_gu["지역유형"].unique():
        gangnam_mean = filtered_gu[filtered_gu["지역유형"] == "강남도심"]["평균기온"].mean()
        diff_df = (
            filtered_gu.groupby("지역유형", as_index=False)["평균기온"].mean()
        )
        diff_df["강남도심과의_차이"] = diff_df["평균기온"] - gangnam_mean
        diff_df["지역유형"] = pd.Categorical(
            diff_df["지역유형"], categories=[t for t in REGION_TYPE_ORDER if t in selected_types], ordered=True
        )
        diff_df = diff_df.sort_values("지역유형")
        fig_diff = px.bar(
            diff_df,
            x="지역유형",
            y="강남도심과의_차이",
            color="강남도심과의_차이",
            color_continuous_scale="RdBu_r",
            title="강남 도심 대비 평균기온 편차 (음수 = 강남 도심보다 시원함)",
            text_auto=".2f",
        )
        fig_diff.update_layout(yaxis_title="온도 차 (℃)", coloraxis_showscale=False)
        st.plotly_chart(fig_diff, use_container_width=True)
    else:
        st.info("강남도심 유형을 선택해야 편차 비교가 표시됩니다.")

    st.markdown("#### 지역 유형별 구 목록")
    st.dataframe(
        filtered_gu[["구", "지역유형", "월_label", "평균기온", "최고기온", "최저기온"]]
        .sort_values(["지역유형", "구", "월_label"])
        .reset_index(drop=True),
        use_container_width=True,
    )

# ==================================================================
# TAB 3. 열돔 현상 메커니즘 분석
# ==================================================================
with tab3:
    st.subheader("열돔(Heat Dome) 현상을 설명하는 기후 데이터 분석")
    st.markdown(
        """
        열돔 현상은 **상층 고기압이 정체**하면서 공기가 하강할 때 단열 압축으로 데워지고,
        이 하강기류가 뚜껑처럼 지표의 열을 가둬 기온이 지속적으로 상승하는 현상입니다.
        아래 데이터로 **기압 · 일사량 · 풍속 · 습도 · 오존농도**와 기온의 관계를 확인합니다.
        """
    )

    date_range = st.slider(
        "기간 선택",
        min_value=climate_df["날짜"].min().to_pydatetime(),
        max_value=climate_df["날짜"].max().to_pydatetime(),
        value=(climate_df["날짜"].min().to_pydatetime(), climate_df["날짜"].max().to_pydatetime()),
        format="MM/DD",
    )
    mask = (climate_df["날짜"] >= date_range[0]) & (climate_df["날짜"] <= date_range[1])
    cdf = climate_df.loc[mask].copy()

    fig_multi = make_subplots(specs=[[{"secondary_y": True}]])
    fig_multi.add_trace(
        go.Scatter(x=cdf["날짜"], y=cdf["기온"], name="기온(℃)", line=dict(color="#e45756", width=2)),
        secondary_y=False,
    )
    fig_multi.add_trace(
        go.Scatter(x=cdf["날짜"], y=cdf["해면기압"], name="해면기압(hPa)", line=dict(color="#4c78a8", width=2, dash="dot")),
        secondary_y=True,
    )
    fig_multi.update_layout(title="일별 기온 vs 해면기압 추이", height=430, hovermode="x unified")
    fig_multi.update_yaxes(title_text="기온 (℃)", secondary_y=False)
    fig_multi.update_yaxes(title_text="해면기압 (hPa)", secondary_y=True)
    st.plotly_chart(fig_multi, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig_solar = px.scatter(
            cdf, x="일사량", y="기온", color="오존농도",
            color_continuous_scale="OrRd",
            trendline="ols",
            title="일사량 vs 기온 (색상=오존농도)",
            labels={"일사량": "일사량 (MJ/m²/day)", "기온": "기온 (℃)"},
        )
        st.plotly_chart(fig_solar, use_container_width=True)
    with col2:
        fig_wind = px.scatter(
            cdf, x="풍속", y="기온", color="상대습도",
            color_continuous_scale="Blues_r",
            trendline="ols",
            title="풍속 vs 기온 (색상=상대습도)",
            labels={"풍속": "풍속 (m/s)", "기온": "기온 (℃)"},
        )
        st.plotly_chart(fig_wind, use_container_width=True)

    st.markdown("#### 변수 간 상관관계 히트맵")
    corr_cols = ["기온", "해면기압", "일사량", "상대습도", "풍속", "오존농도"]
    if "열지수" in cdf.columns:
        corr_cols.append("열지수")
    corr = cdf[corr_cols].corr()
    fig_corr = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        title="기후 변수 간 상관계수",
    )
    fig_corr.update_layout(height=520)
    st.plotly_chart(fig_corr, use_container_width=True)

    with st.expander("📌 상관관계로 읽는 열돔 형성 메커니즘 해석 가이드"):
        st.markdown(
            """
            - **기온 ↔ 해면기압 (양의 상관)**: 상층 고기압이 강해질수록 하강기류에 의한
              단열승온으로 지표 기온이 함께 오르는 경향을 시사합니다.
            - **기온 ↔ 일사량 (양의 상관)**: 고기압권 내 맑은 날씨가 지속되며 일사량이
              늘어 지표 가열이 가중됩니다.
            - **기온 ↔ 풍속 (음의 상관)**: 고기압이 정체하면 대기 순환이 약해져 풍속이
              낮아지고, 데워진 공기가 확산되지 못한 채 정체됩니다.
            - **기온 ↔ 오존농도 (양의 상관)**: 강한 일사와 고온은 광화학 반응을 촉진해
              지표 오존 농도를 높이는 2차 오염을 유발합니다.
            """
        )

st.markdown("---")
st.caption(
    "⚠️ 기본 데이터는 실제 관측값의 경향을 반영해 생성한 샘플 데이터입니다. "
    "실제 세부 탐구에는 기상자료개방포털(data.kma.go.kr) 등의 관측 자료로 교체해 사용하세요. "
    "(사이드바에서 동일한 컬럼 구조의 CSV를 업로드하면 자동으로 대체됩니다.)"
)
