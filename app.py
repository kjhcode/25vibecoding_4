import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
import urllib.request
from datetime import datetime
from fpdf import FPDF
import io
import plotly.io as pio

st.set_page_config(page_title="생성형 AI 교육 분석", layout="wide")
st.title("📊 생성형 AI 도구의 교육 활용 분석 대시보드")

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
FONT_DIR = "./fonts"
FONT_PATH = os.path.join(FONT_DIR, "NanumGothic-Regular.ttf")

if not os.path.exists(FONT_PATH):
    os.makedirs(FONT_DIR, exist_ok=True)
    try:
        urllib.request.urlretrieve(FONT_URL, FONT_PATH)
    except Exception as e:
        st.warning(f"폰트 다운로드 실패: {e}")
        FONT_PATH = None

uploaded_file = st.file_uploader("설문 응답 CSV 파일을 업로드하세요", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    grade_col = next((col for col in df.columns if "학년" in col), None)
    if grade_col:
        selected_grades = st.sidebar.multiselect("학년 선택", sorted(df[grade_col].dropna().unique()))
        if selected_grades:
            df = df[df[grade_col].isin(selected_grades)]

    st.sidebar.header("📊 시각화 옵션")
    chart_type = st.sidebar.radio("그래프 유형 선택", ["막대그래프", "원형차트", "박스플롯", "히스토그램", "히트맵", "트리맵", "애니메이션 막대그래프"])
    metric = st.sidebar.selectbox("비교 항목 선택", ["유용성 점수", "신뢰도 점수"])

    st.subheader("📋 데이터 미리보기")
    st.dataframe(df.head())

    df_use = df[df["사용 여부"] == "예"].copy()

    if chart_type == "막대그래프":
        fig = px.bar(df_use.groupby("사용자 유형")[metric].mean().reset_index(), x="사용자 유형", y=metric)
    elif chart_type == "원형차트":
        fig = px.pie(df_use, names="감정")
    elif chart_type == "박스플롯":
        fig = px.box(df_use, x="사용자 유형", y=metric, color="사용자 유형")
    elif chart_type == "히스토그램":
        fig = px.histogram(df_use, x=metric, color="사용자 유형", barmode="overlay")
    elif chart_type == "히트맵":
        pivot = df_use.pivot_table(index="사용자 유형", columns="사용 빈도", values=metric, aggfunc="mean")
        fig = px.imshow(pivot, text_auto=True)
    elif chart_type == "트리맵":
        fig = px.treemap(df_use, path=["사용자 유형", "감정"], values=metric)
    elif chart_type == "애니메이션 막대그래프":
        fig = px.bar(df_use, x="사용자 유형", y=metric, animation_frame="사용 빈도", color="사용자 유형")

    fig.update_layout(margin=dict(l=30, r=30, t=50, b=30))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"감정별 평균 {metric}")
    fig_emotion = px.bar(df_use.groupby("감정")[metric].mean().reset_index(), x="감정", y=metric, color="감정")
    st.plotly_chart(fig_emotion, use_container_width=True)

    st.subheader(f"사용 빈도별 평균 {metric}")
    fig_freq = px.bar(df_use.groupby("사용 빈도")[metric].mean().reset_index(), x="사용 빈도", y=metric, color="사용 빈도")
    st.plotly_chart(fig_freq, use_container_width=True)

    # 🧠 요약 자동 생성
    st.subheader("🧠 설문 응답 요약")
    try:
        group_summary = df_use.groupby("사용자 유형")[metric].mean().reset_index()
        emotion_counts = df_use["감정"].value_counts().reset_index()
        emotion_counts.columns = ["감정", "응답 수"]

        summary_text = f"""
**총 응답 수**: {len(df)}명  
**사용한 응답 수**: {len(df_use)}명  
**평균 {metric}**: {df_use[metric].mean():.2f}

**사용자 유형별 평균**
{group_summary.to_string(index=False)}

**감정 분포**
{emotion_counts.to_string(index=False)}
"""
        st.markdown(summary_text)

    except Exception as e:
        st.warning(f"요약 생성 중 오류 발생: {e}")

    pdf_button = st.sidebar.button("📄 PDF 보고서 저장")
    if pdf_button:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16)
        pdf.cell(200, 10, txt="생성형 AI 교육 분석 리포트", ln=True, align="C")
        pdf.set_font("Arial", size=12)
        pdf.ln(10)
        pdf.multi_cell(0, 10, f"""비교 항목: {metric}
그래프 유형: {chart_type}
생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")

        if "animation_frame" not in fig.layout:
            img_buf = io.BytesIO()
            pio.write_image(fig, img_buf, format="png")
            with open("chart_temp.png", "wb") as f:
                f.write(img_buf.getvalue())
            pdf.image("chart_temp.png", x=10, y=60, w=180)
        else:
            pdf.ln(20)
            pdf.cell(0, 10, txt="애니메이션 그래프는 PDF에 포함되지 않습니다.", ln=True)

        output_path = "ai_edu_report.pdf"
        pdf.output(output_path)
        with open(output_path, "rb") as f:
            st.sidebar.download_button("📥 PDF 다운로드", f, file_name=output_path, mime="application/pdf")

    if st.sidebar.button("📥 Excel 리포트 다운로드"):
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
            df_use.to_excel(writer, index=False, sheet_name='분석결과')
        st.sidebar.download_button(
            label="📄 Excel 다운로드",
            data=excel_buf.getvalue(),
            file_name="ai_edu_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.subheader("🗣️ 자유 의견 워드클라우드")
    opinion_text = " ".join(df_use["의견"].dropna().astype(str)).strip()
    if opinion_text:
        try:
            wc = WordCloud(
                font_path=FONT_PATH if os.path.exists(FONT_PATH) else None,
                width=800, height=400, background_color='white',
                colormap="Set2", max_font_size=60
            ).generate(opinion_text)
            fig_wc, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig_wc)
        except Exception as e:
            st.error(f"워드클라우드 생성 오류: {e}")
    else:
        st.info("의견 텍스트가 없어 워드클라우드를 생성할 수 없습니다.")
else:
    st.info("CSV 파일을 업로드하면 분석이 시작됩니다.")
