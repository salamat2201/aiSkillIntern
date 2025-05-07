import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
from azureml.core import Run

load_dotenv() ## load all our environment variables

run = Run.get_context()

if run.id.startswith("OfflineRun"):
    print("Running locally - ScriptRunContext not available")
else:
    print("Running in Azure - ScriptRunContext is active")

genai.configure(api_key='AIzaSyCvJtoOUZ_XXyC2juqkx8UgD8P_C_-qt5I')

def get_gemini_repsonse(input):
    model=genai.GenerativeModel('gemini-2.0-flash')
    response=model.generate_content(input)
    return response.text

def input_pdf_text(uploaded_file):
    reader=pdf.PdfReader(uploaded_file)
    text=""
    for page in range(len(reader.pages)):
        page=reader.pages[page]
        text+=str(page.extract_text())
    return text

#Prompt Template

input_prompt = """
You are an expert ATS (Applicant Tracking System) specialized in tech hiring.
Your task is to evaluate the given resume content and compare it to the job description.
Provide:

1. An estimated match percentage (from 0% to 100%) indicating how well the resume fits the job.
2. A list of important missing keywords.
3. A short professional summary of the candidate based on the resume.

Use this JSON structure:
{{
  "JD Match": "85%",
  "MissingKeywords": ["Python", "Kubernetes"],
  "Profile Summary": "Experienced data analyst with 5 years in financial data reporting..."
}}

Resume:
{text}

Job Description:
{jd}
"""


## streamlit app
st.title("Smart ATS")
st.text("Improve Your Resume ATS")
jd=st.text_area("Paste the Job Description")
uploaded_file=st.file_uploader("Upload Your Resume",type="pdf",help="Please uplaod the pdf")

submit = st.button("Submit")

import re

def extract_json_from_text(text):
    try:
        json_str = re.search(r"\{.*\}", text, re.DOTALL).group()
        return json.loads(json_str)
    except:
        return None

# Внутри блока submit
if submit:
    if uploaded_file is not None and jd.strip() != "":
        text = input_pdf_text(uploaded_file)
        final_prompt = input_prompt.format(text=text, jd=jd)
        response = get_gemini_repsonse(final_prompt)

        st.subheader("📊 ATS Analysis Result")
        result = extract_json_from_text(response)

        if result:
            # Процент совпадения
            st.metric(label="✅ JD Match", value=result["JD Match"])

            # Разделитель
            st.divider()

            # Отсутствующие ключевые слова
            st.markdown("### ❌ Missing Keywords")
            if result["MissingKeywords"]:
                st.code(", ".join(result["MissingKeywords"]), language="markdown")
            else:
                st.success("Все ключевые слова присутствуют!")

            # Разделитель
            st.divider()

            # Профиль
            st.markdown("### 🧑‍💼 Profile Summary")
            st.info(result["Profile Summary"])

        else:
            st.error("⚠️ Не удалось распарсить результат. Ниже — сырой ответ модели:")
            st.write(response)
