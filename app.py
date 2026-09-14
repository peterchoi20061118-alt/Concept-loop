import os
import json
import streamlit as st
from google import genai
from google.genai import types

# 頁面基本設置
st.set_page_config(page_title="ConceptLoop - AI 學習閉環助手", layout="centered")

st.title("🧠 ConceptLoop - AI 學習助手")
st.caption("上傳學習材料 ➔ 獲取個人化例子 ➔ 即時情境測驗閉環")

# 側邊欄：設定 API Key
with st.sidebar:
    st.header("⚙️ 設置")
    api_key = st.text_input("輸入 Gemini API Key", type="password", help="前往 Google AI Studio 獲取免費 API Key")
    style = st.selectbox(
        "選擇舉例風格 (Analogy Style)",
        ["日常白話生活", "打機/電玩術語 (Gaming)", "商業與職場實戰 (Business)"]
    )

# 初始化 Session State 來保存生成內容與作答狀態
if "examples" not in st.session_state:
    st.session_state.examples = ""
if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Step 1: 輸入學習材料
st.subheader("1. 輸入你的學習內容")
user_material = st.text_area(
    "貼上課堂筆記、抽象概念或教科書段落：",
    height=150,
    placeholder="例如：機會成本 (Opportunity Cost) 是指在面臨多方案擇一決策時，被捨棄的選項中最高價值者..."
)

# 觸發生成邏輯
if st.button("🚀 開始學習（生成例子與測驗）", type="primary"):
    if not api_key:
        st.error("請在左側側邊欄輸入你的 Gemini API Key！")
    elif not user_material.strip():
        st.warning("請先輸入學習材料！")
    else:
        with st.spinner("AI 正在拆解概念並構思例子..."):
            try:
                # 初始化 Gemini 客戶端
                client = genai.Client(api_key=api_key)

                # Prompt 1: 生成生活化例子
                example_prompt = f"""
                你是一位擅長用生動比喻教學的導師。
                請閱讀以下學習材料，用繁體中文完成：
                1. 用兩至三句簡單總結核心概念。
                2. 根據指定風格「{style}」，提供 2 個生動、具體的生活化例子，幫助初學者秒懂。

                【學習材料】
                {user_material}
                """

                example_response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=example_prompt
                )
                st.session_state.examples = example_response.text

                # Prompt 2: 生成結構化情境測驗 (JSON 格式)
                quiz_prompt = f"""
                根據以下學習材料，出一道單選情境應用題（非死記硬背定義，測試用戶能否在日常情境中應用該概念）。
                材料：{user_material}

                請嚴格以 JSON 格式輸出，不要加 markdown 標記，結構如下：
                {{
                    "question": "情境題目內容",
                    "options": ["選項 A", "選項 B", "選項 C", "選項 D"],
                    "correct_index": 0,
                    "explanation": "詳細解析為什麼這個是正確答案"
                }}
                """

                quiz_response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=quiz_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )

                st.session_state.quiz = json.loads(quiz_response.text)
                st.session_state.submitted = False

            except Exception as e:
                st.error(f"發生錯誤：{str(e)}")

# Step 2: 顯示理解例子
if st.session_state.examples:
    st.divider()
    st.subheader("2. AI 概念解析與個人化例子")
    st.markdown(st.session_state.examples)

# Step 3: 互動測驗閉環
if st.session_state.quiz:
    st.divider()
    st.subheader("3. 檢驗理解：情境測驗")
    quiz = st.session_state.quiz

    st.write(f"**題目：** {quiz['question']}")
    
    user_choice = st.radio(
        "請選擇你的答案：",
        options=list(range(len(quiz['options']))),
        format_func=lambda x: f"{chr(65+x)}. {quiz['options'][x]}",
        key="quiz_radio"
    )

    if st.button("提交答案"):
        st.session_state.submitted = True

    if st.session_state.submitted:
        if user_choice == quiz['correct_index']:
            st.success("🎉 答啱咗！你已經完全掌握呢個概念嘅應用！")
        else:
            correct_letter = chr(65 + quiz['correct_index'])
            st.error(f"❌ 答錯咗。正確答案係：**{correct_letter}**")
        
        st.info(f"💡 **AI 解析：** {quiz['explanation']}")
