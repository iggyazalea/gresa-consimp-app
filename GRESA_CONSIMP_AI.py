import streamlit as st
from PIL import Image
import openai
import re

import os
import platform
import pytesseract



#pip install streamlit openai pillow pytesseract
#streamlit run GRESA_CONSIMP_AI.py
# ==============================
# TESSERACT SETUP
# ==============================
if platform.system() == "Windows":
    default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(default_path):
        pytesseract.pytesseract.tesseract_cmd = default_path
    else:
        st.warning("⚠️ Tesseract not found in the default path. Please install it from: "
                   "https://github.com/UB-Mannheim/tesseract/wiki and restart.")
else:
    # For macOS/Linux, assume tesseract is in PATH
    try:
        version = pytesseract.get_tesseract_version()
    except Exception:
        st.warning("⚠️ Tesseract is not installed. Install it via your package manager.")

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="GRECS-AI", page_icon="📘", layout="wide")

# Set your OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# ==============================
# SYSTEM PROMPT
# ==============================
SYSTEM_PROMPT = """
You have two functions. 
1. GRESA Mode: You are a patient tutor who always solves problems using the GRESA method, and
2. ConSimp Mode: You are a Concept Simplifier that explains concepts into three levels, easy, intermediate and complex.

For GRESA Mode always follow this exact format:

Given:
- List the given values with units.

Required:
- State what is required.

Equation:
- Write the main formula or equations needed.

Solution:
- Show the solution in clear numbered steps.
- Start with "Step 1:", then continue sequentially.
- Do not skip or duplicate step numbers.
- Do not include LaTeX, symbols like \\text{} or \\approx, or Markdown math formatting.
- Write equations in plain text with units.

Answer:
**Final Answer here (with units if applicable)**

Rules:
- Always include all 5 parts: Given, Required, Equation, Solution, Answer.
- Do not add any extra text outside the GRESA format.
- Keep explanations simple and student-friendly.

For ConSimp Mode always follow this exact format:
1. Provide three level of explanation for a concept in:
Easy: Breaks down the concept in simple, bite-sized terms for beginners or quick understanding.

Intermediate: Adds more details and examples for students who have some background and want deeper understanding.

Advanced: Gives a full, detailed explanation including nuances, technical terms, and advanced applications for students who want mastery.

Also add process questions for each level.
"""

# ==============================
# FUNCTIONS
# ==============================
def ask_openai(prompt, mode="Teaching"):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini" if mode == "Teaching" else "gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {e}"

# ==============================
# RESET FUNCTION
# ==============================
def reset_session_state():
    # Clear text inputs
    for key in ["problem_text", "student_solution", "concept_text"]:
        if key in st.session_state:
            st.session_state[key] = ""

    # Clear uploaded files
    for key in ["uploaded_problem_file", "uploaded_student_file", "uploaded_concept_file"]:
        if key in st.session_state:
            st.session_state[key] = None

def extract_text_from_image(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        return pytesseract.image_to_string(image)
    except Exception as e:
        return f"⚠️ OCR Error: {e}"


def display_gresa_response(response_text):
    sections = {
        "Given:": "#cce5ff",  # blue
        "Required:": "#ffe5b4",  # orange
        "Equation:": "#e6ccff",  # purple
        "Solution:": "#fff3b0",  # yellow
        "Answer:": "#d4edda"   # green
    }

    # Remove LaTeX-like text
    clean_text = re.sub(r'(\\text\{.*?\}|\\approx|\\[a-zA-Z]+|\$+)', '', response_text)

    # Split into sections
    pattern = r"(Given:|Required:|Equation:|Solution:|Answer:)"
    splits = re.split(pattern, clean_text)

    content_dict = {}
    current_sec = ""
    for part in splits:
        if part in sections:
            current_sec = part
            content_dict[current_sec] = ""
        else:
            if current_sec:
                content_dict[current_sec] += part.strip() + "\n"

    # Display formatted sections
    for sec, color in sections.items():
        if sec in content_dict:
            content = content_dict[sec].strip()
            if not content:
                continue

            with st.expander(f"**{sec}** (click to expand)"):
                lines = content.split("\n")
                display_lines = []

                if sec in "Given:":
                    # Simple bullets
                    for line in lines:
                        line = line.strip()
                        if line:
                            display_lines.append(f"{line}")
                            
                elif sec == "Required:":
                    for line in lines:
                        line = line.strip()
                        if line:
                            display_lines.append(f"{line}")
                            
                elif sec == "Equation:":
                    for line in lines:
                        line = line.strip()
                        if line:
                            display_lines.append(f"{line}")

                elif sec == "Solution:":
                    # Keep AI's step numbering, don’t re-add
                    for line in lines:
                        line = line.strip()
                        if line:
                            display_lines.append(f"{line}")

                elif sec == "A:":
                    for line in lines:
                        line = line.strip()
                        if line:
                            display_lines.append(f"**{line}**")

                html_content = "<br>".join(display_lines)
                st.markdown(
                    f'<div style="background-color:{color}; padding:10px; border-radius:5px;">{html_content}</div>',
                    unsafe_allow_html=True
                )


def get_problem_input(label_text="Enter your problem:"):
    if 'problem_text' not in st.session_state:
        st.session_state.problem_text = ""

    col1, col2 = st.columns(2)
    with col1:
        text_input = st.text_area(f"✍️ {label_text}", value=st.session_state.problem_text)
    with col2:
        uploaded_file = st.file_uploader("📸 Or upload an image", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            extracted_text = extract_text_from_image(uploaded_file)
            st.write("📖 Extracted Text from Image:")
            st.code(extracted_text)
            if text_input.strip() == "":
                text_input = extracted_text

    st.session_state.problem_text = text_input
    return text_input


# ==============================
# APP UI
# ==============================
# Initialize login state
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Password check
if not st.session_state["authenticated"]:
    password = st.text_input("Enter Password", type="password")

    if password == "crhsshs123":   # ✅ test password (local only)
        st.session_state["authenticated"] = True
        st.success("Access Granted ✅")
        st.rerun()
    elif password:  # if something was entered but wrong
        st.error("❌ Incorrect password")
        st.stop()
    else:
        st.stop()  # 🚨 stop execution if nothing entered yet

st.title("📘 GRESA and Concept Simplifier AI")
st.write("From word problems to tough concepts, **GRECS-AI** have your back. This AI-powered study tool solves Math and Science word problems with the GRESA method and uses Concept Simplifier to explain complex concepts from any subject into easy-to-understand ideas. ")

mode = st.sidebar.radio("Choose Mode:", ["GRESA Mode", "Concept Simplifier Mode"])

# Refresh button in sidebar
st.sidebar.button("🔄 Refresh / Clear Inputs", on_click=reset_session_state)

# Optional: auto-reset on mode switch
if 'last_mode' not in st.session_state:
    st.session_state.last_mode = mode

if st.session_state.last_mode != mode:
    reset_session_state()
    st.session_state.last_mode = mode

# ==============================
# GRESA Mode
# ==============================
if mode == "GRESA Mode":
    st.header("👨‍🏫 GRESA Mode")
    st.write("Input a worded problem (text or image). AI will solve it **step-by-step using GRESA**.")
    problem_text = get_problem_input("Enter your problem here:")

    if st.button("Solve with GRESA"):
        if problem_text.strip():
            with st.spinner("Thinking..."):
                prompt = f"Solve this problem step-by-step using the GRESA method. Problem: {problem_text}"
                answer = ask_openai(prompt, mode="Teaching")
            st.success("Here’s the solution:")
            display_gresa_response(answer)
        else:
            st.warning("Please enter a worded problem or upload an image of the worded problem first.")

# ==============================
# Concept Simplifier Mode
# ==============================
elif mode == "Concept Simplifier Mode":
    st.header("📚 Concept Simplifier Mode")
    st.write("Input a concept or topic (text or image). AI will provide explanations at three levels and process questions for each.")

    # Step 1: Get concept/topic input
    concept_text = get_problem_input("Enter the concept or topic here:")

    if st.button("Simplify Concept"):
        if concept_text.strip():
            with st.spinner("Generating explanations..."):
                consimp_prompt = f"""
                You are a teacher explaining concepts in three levels. Follow this exact format:

                Concept/Topic: {concept_text}

                Easy:
                - Provide a simple, bite-sized explanation for beginners.
                - Include 1–2 process questions for practice.

                Intermediate:
                - Provide a more detailed explanation with examples.
                - Include 2–3 process questions for practice.

                Advanced:
                - Provide a full, technical explanation with nuances and advanced applications.
                - Include 3–5 process questions for practice.

                Rules:
                - Always include all three levels.
                - Label clearly: Easy, Intermediate, Advanced.
                - Use simple, clear language where appropriate.
                """

                response = ask_openai(consimp_prompt, mode="Teaching")

            # Display AI response in expanders for readability
            levels = ["Easy", "Intermediate", "Advanced"]
            for level in levels:
                pattern = rf"{level}:(.*?)(?=Easy:|Intermediate:|Advanced:|$)"
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(1).strip()
                    if content:
                        with st.expander(f"**{level} Explanation**"):
                            st.markdown(content)
        else:
            st.warning("Please enter a concept or topic first.")








