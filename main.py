import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="생성형 AI 교육 분석", layout="wide")
st.title("📊 생성형 AI 도구의 교육 활용 분석 대시보드")

# 파일 업로드
uploaded_file = st.file_uploader("설문 응답 CSV 파일을 업로드하세요", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("📋 데이터 미리보기")
    st.dataframe(df.head())

    # 필터: 사용 여부 '예'인 경우만 분석
    df_use = df[df["사용 여부"] == "예"].copy()

    # 사용자 유형별 평균 유용성 점수
    fig1 = px.bar(
        df_use.groupby("사용자 유형")["유용성 점수"].mean().reset_index(),
        x="사용자 유형",
        y="유용성 점수",
        title="사용자 유형별 평균 유용성 점수"
    )
    fig1.update_layout(
        xaxis_tickangle=0,
        yaxis=dict(tickfont=dict(size=14)),
        xaxis=dict(tickfont=dict(size=14)),
        margin=dict(l=30, r=30, t=50, b=30)
    )

    # 사용자 유형별 평균 신뢰도 점수
    fig2 = px.bar(
        df_use.groupby("사용자 유형")["신뢰도 점수"].mean().reset_index(),
        x="사용자 유형",
        y="신뢰도 점수",
        title="사용자 유형별 평균 신뢰도 점수"
    )
    fig2.update_layout(
        xaxis_tickangle=0,
        yaxis=dict(tickfont=dict(size=14)),
        xaxis=dict(tickfont=dict(size=14)),
        margin=dict(l=30, r=30, t=50, b=30)
    )

    # 감정 분포 파이차트
    fig3 = px.pie(df_use, names="감정", title="사용자 감정 분포")
    fig3.update_layout(margin=dict(t=40, b=20))

    # 시각화 표시: 두 개씩 나눠서 보기 좋게 배치
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.plotly_chart(fig2, use_container_width=True)

    st.plotly_chart(fig3, use_container_width=True)

    # 워드클라우드
    st.subheader("🗣️ 자유 의견 워드클라우드")
    opinion_text = " ".join(df_use["의견"].dropna().astype(str)).strip()

    if opinion_text:
        try:
            # 폰트 경로 자동 탐색 또는 fallback
            possible_fonts = [
                "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
                "/Library/Fonts/AppleGothic.ttf",
                None  # 기본값 사용 (영문 폰트)
            ]
            font_path = next((fp for fp in possible_fonts if fp and os.path.exists(fp)), None)

            wc = WordCloud(
                font_path=font_path,
                width=800,
                height=400,
                background_color='white'
            ).generate(opinion_text)

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
        except Exception as e:
            st.error(f"워드클라우드 생성 오류: {e}")
    else:
        st.info("의견 텍스트가 없어 워드클라우드를 생성할 수 없습니다.")
else:
    st.info("CSV 파일을 업로드하면 분석이 시작됩니다.")
