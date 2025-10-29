import streamlit as st
from PIL import Image
import openai
import re
import os
import platform
import pytesseract

# ==============================
# TESSERACT SETUP
# ==============================
if platform.system() == "Windows":
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    else:
        st.warning("⚠️ Tesseract not found. Install it from: "
                   "https://github.com/UB-Mannheim/tesseract/wiki")
else:
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        st.warning("⚠️ Tesseract not found. Install it via your package manager.")

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="GRECS-AI", page_icon="📘", layout="wide")
openai.api_key = os.getenv("OPENAI_API_KEY")

# ==============================
# FUNCTIONS
# ==============================
def ask_openai(prompt):
    """Query OpenAI Chat API"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {e}"

def reset_session_state():
    """Clears session state inputs"""
    for key in ["problem_text", "concept_text", "uploaded_problem_file"]:
        st.session_state[key] = ""

def extract_text_from_image(uploaded_file):
    """Extracts text using OCR"""
    try:
        image = Image.open(uploaded_file)
        return pytesseract.image_to_string(image)
    except Exception as e:
        return f"⚠️ OCR Error: {e}"

def display_gresa_response(response_text):
    """Formats and displays GRESA response"""
    sections = {
        "Given:": "#cce5ff",
        "Required:": "#ffe5b4",
        "Equation:": "#e6ccff",
        "Solution:": "#fff3b0",
        "Answer:": "#d4edda"
    }

    clean_text = re.sub(r'(\\text\{.*?\}|\\approx|\\[a-zA-Z]+|\$+)', '', response_text)
    splits = re.split(r"(Given:|Required:|Equation:|Solution:|Answer:)", clean_text)

    content_dict, current_sec = {}, ""
    for part in splits:
        if part in sections:
            current_sec = part
            content_dict[current_sec] = ""
        elif current_sec:
            content_dict[current_sec] += part.strip() + "\n"

    for sec, color in sections.items():
        if sec in content_dict and content_dict[sec].strip():
            with st.expander(f"**{sec}** (click to expand)"):
                st.markdown(
                    f'<div style="background-color:{color}; padding:10px; border-radius:5px;">'
                    f'{content_dict[sec].strip().replace("\n", "<br>")}</div>',
                    unsafe_allow_html=True
                )

def get_problem_input(label_text="Enter your problem:"):
    """Handles text or image input for problems/concepts"""
    if 'problem_text' not in st.session_state:
        st.session_state.problem_text = ""

    col1, col2 = st.columns(2)
    with col1:
        text_input = st.text_area(f"✍️ {label_text}", value=st.session_state.problem_text)
    with col2:
        uploaded_file = st.file_uploader("📸 Or upload an image", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            extracted_text = extract_text_from_image(uploaded_file)
            st.write("📖 Extracted Text:")
            st.code(extracted_text)
            if not text_input.strip():
                text_input = extracted_text

    st.session_state.problem_text = text_input
    return text_input

# ==============================
# LOGIN SYSTEM
# ==============================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    password = st.text_input("Enter Password", type="password")
    if password == "crhsshs123":
        st.session_state["authenticated"] = True
        st.success("Access Granted ✅")
        st.rerun()
    elif password:
        st.error("❌ Incorrect password")
    st.stop()

# ==============================
# APP INTERFACE
# ==============================
st.title("📘 GRESA and Concept Simplifier AI")
st.write(
    "From word problems to tough concepts, **GRECS-AI** have your back. This AI-powered study tool solves Math and Science word problems with the GRESA method and uses Concept Simplifier to explain complex concepts from any subject into easy-to-understand ideas. ")

mode = st.sidebar.radio("Choose Mode:", ["GRESA Mode", "Concept Simplifier Mode"])
st.sidebar.button("🔄 Refresh / Clear Inputs", on_click=reset_session_state)

# ==============================
# GRESA MODE
# ==============================
if mode == "GRESA Mode":
    st.header("👨‍🏫 GRESA Mode")
    problem_text = get_problem_input("Enter your worded problem:")
    if st.button("Solve with GRESA"):
        if problem_text.strip():
            with st.spinner("Solving using GRESA..."):
                prompt = f"""
                Solve this problem step-by-step using the GRESA method.
                Make your answers correct and accurate.
                Follow this exact format and rules:

                FORMAT (must follow exactly):
                Given:
                • (list each given in bullet form; include variable, equals sign, value, and unit)

                Required:
                (write what is being asked, short and clear)

                Equation:
                (write the main formula(s) needed using plain text characters; do NOT use LaTeX or dollar signs)
                Examples:
                W_applied = F * d * cos(theta)
                N = m * g * cos(theta)

                Solution:
                Show the solution in clear numbered steps.
                Start with "Step 1:" and continue sequentially (Step 2:, Step 3:, ...).
                Do not skip or duplicate step numbers. Give spaces for each steps.
                Show substitutions and arithmetic (keep it concise).
                Use plain text math (no LaTeX, no $).
                Example step:
                Step 1: N = m * g * cos(theta) = 5 * 9.81 * cos(30) = 42.47 N

                Answer:
                State the final answer in one concise sentence with the numeric value and unit.
                Example:
                The total work done on the block is 393.8 J.

                RULES (mandatory):
                - Use plain text only. Do NOT include: "$", "text", "\,", LaTeX commands, HTML tags, or bold/asterisk markers (**).
                - "Given" must be bullet points beginning with "•".
                - Equations must be plain ASCII-friendly and readable (use *, /, ^ or function names like cos()).
                - Units must be normal text (e.g., N, J, m, kg).
                - Keep explanations clear and concise; avoid extra commentary.
                - Always include all five labeled sections exactly as above: Given, Required, Equation, Solution, Answer.


                Problem: {problem_text}"""
                answer = ask_openai(prompt)
            st.success("Here’s the solution:")
            display_gresa_response(answer)

            # --- Download button for GRESA Mode (includes problem) ---
            safe_title = re.sub(r'[^A-Za-z0-9]+', '_', problem_text.strip())[:30] or "Problem"
            filename = f"GRECS-AI_GRESA_{safe_title}.txt"

            # Combine problem and answer in one text file
            full_text = f"Problem:\n{problem_text.strip()}\n\nGRESA Solution:\n{answer.strip()}"

            st.download_button(
                label="📥 Download GRESA Answer as TXT",
                data=full_text.encode('utf-8'),
                file_name=filename,
                mime="text/plain"
            )

        else:
            st.warning("Please input a problem or upload an image first.")



# ==============================
# CONCEPT SIMPLIFIER MODE
# ==============================
else:
    st.header("📚 Concept Simplifier Mode")
    concept_text = get_problem_input("Enter the concept/topic and MELCs here:")

    if st.button("Simplify Concept"):
        if concept_text.strip():
            with st.spinner("Simplifying the concept..."):
                prompt = f"""
                You are a teacher explaining concepts in three levels and you answer accordingly based on the given MELCs. 
                If no MELCs is given, just explain the concept in three levels. Follow this exact format:

                Concept/Topic: {concept_text}

                Easy:
                - Provide a simple, bite-sized explanation for students with beginner level.
                - Include 5 process questions for practice.
                
                Intermediate:
                - Provide a more detailed explanation with examples for average students.
                - Include 5 process questions for practice.
                
                Advanced:
                - Provide a full, technical explanation with examples, nuances and advanced applications for advanced students.
                - Include 5 process questions for practice.

                RULES (mandatory):
                - Always include all three levels.
                - Label clearly: Easy, Intermediate, Advanced.
                - Use simple, clear language where appropriate.
                - For topics with many examples, give all examples.
                - Use plain text only. Do NOT include: "$", "text", "\,", LaTeX commands, HTML tags, or bold/asterisk markers (**).
                - For concepts with equations, it must be plain ASCII-friendly and readable (use *, /, ^ or function names like cos()).
                - Units must be normal text (e.g., N, J, m, kg).
                - Keep explanations clear and concise; avoid extra commentary.
                - Add legit reference if available, it can be a legit internet link, book, etc.
                """
                response = ask_openai(prompt)

            for level in ["Easy", "Intermediate", "Advanced"]:
                match = re.search(rf"{level}:(.*?)(?=Easy:|Intermediate:|Advanced:|$)",
                                  response, re.DOTALL | re.IGNORECASE)
                if match:
                    with st.expander(f"**{level} Explanation**"):
                        st.markdown(match.group(1).strip())

            # --- Download button for Concept Simplifier Mode ---
            safe_title = re.sub(r'[^A-Za-z0-9]+', '_', concept_text.strip())[:30] or "Concept"
            filename = f"GRECS-AI_Simplified_{safe_title}.txt"

            st.download_button(
                label="📥 Download Simplified Explanation as Text File",
                data=response.encode('utf-8'),
                file_name=filename,
                mime="text/plain"
            )

        else:
            st.warning("Please enter a concept or upload an image first.")


