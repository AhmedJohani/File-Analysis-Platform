import threading
import signal
import os
import datetime
import re
import io
import logging
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from crewai import LLM, Agent, Task, Crew
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

# --- Threading Patch for CrewAI ---
if threading.current_thread() is not threading.main_thread():
    original_signal = signal.signal
    def safe_signal(sig, handler):
        try:
            return original_signal(sig, handler)
        except ValueError:
            return None
    signal.signal = safe_signal

# --- Configuration & Setup ---
load_dotenv()

# --- Security: Logging Configuration ---
logging.basicConfig(
    filename='secure_activity.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

st.set_page_config(
    page_title="File Analysis Platform",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Security: API Key Validation ---
if not os.getenv("GOOGLE_API_KEY"):
    st.error("⚠️ Configuration Error: Secure Key Validation Failed. System halted.")
    st.stop()

# --- Session State Initialization ---
if "language" not in st.session_state:
    st.session_state.language = "English"

# --- Localization Dictionary ---
translations = {
    "English": {
        "page_title": "File Analysis Platform",
        "tagline": "Advanced AI-Powered Insights for Your Data",
        "settings": "⚙️ Settings",
        "language_label": "Interface Language / لغة الواجهة",
        "today": "📅 **Today:**",
        "version": "v2.3.0 | Enterprise Secure Edition",
        "tabs": ["📂 Data Upload", "🎯 Analysis Goal", "📈 Visual Insights"],
        "upload_header": "### Upload Your Dataset",
        "supported_formats": "Supported formats: CSV, Excel (Max 200MB)",
        "file_uploaded": "✅ File '{filename}' verified & uploaded successfully!",
        "data_preview": "#### Data Preview",
        "data_stats": "Total Rows: {rows} | Columns: {cols}",
        "read_error": "❌ Error reading file: {e}",
        "visuals_header": "### 📊 Automated Visual Insights",
        "visuals_info": "👆 Please upload a file in the 'Data Upload' tab to see visual insights.",
        "num_cols": "Detected Numerical Columns: {cols}",
        "cat_cols": "Detected Categorical Columns: {cols}",
        "dist_title": "Distribution of {col}",
        "corr_title": "Correlation Matrix",
        "top_10": "Top 10 Categories in {col}",
        "goal_header": "### Define Your Analysis Objective",
        "goal_label": "What is your required to analyze this file?",
        "goal_placeholder": "e.g., Identify top 3 factors driving sales decline in Q3 and suggest cost-saving measures...",
        "launch_btn": "🚀 Launch Analysis",
        "err_no_file": "⚠️ Please upload a data file first.",
        "err_no_intent": "⚠️ Please describe your analysis goal.",
        "err_no_api": "❌ Configuration Error.",
        "status_active": "🚀 AJ Agent is Active",
        "status_persona": "🏗️ **Constructing Agent Persona...**",
        "agent_role": "**🤖 Agent Role:** {role}\n\n**🎯 Goal:** {goal}",
        "status_task": "📝 **Designing Analysis Task...**",
        "status_thinking": "🧠 **Thinking & Analyzing Data...** (This may take 30-60 seconds)",
        "status_complete": "✅ Analysis Complete!",
        "success_msg": "✅ Analysis Complete!",
        "report_header": "### 📝 Executive Report",
        "download_btn": "⬇️ Download Official PDF Report",
        "download_help": "💡 You can rename the file and choose the location in the browser's download prompt.",
        "analysis_error": "❌ An unexpected error occurred. Technical details have been logged.",
        "pdf_title": "AJ Analysis Report",
        "pdf_generated": "Generated on: {date}",
        "agent_backstory": "You are a top-tier consultant for AJ Intelligent Solutions. Your expertise is specifically tailored to: '{intent}'. You deliver clear, data-backed, and commercially viable recommendations.",
        "security_warning": "⚠️ Security Alert: {message}"
    },
    "Arabic": {
        "page_title": "منصة تحليل الملفات",
        "tagline": "رؤى متقدمة لبياناتك مدعومة بالذكاء الاصطناعي",
        "settings": "⚙️ الإعدادات",
        "language_label": "Interface Language / لغة الواجهة",
        "today": "📅 **التاريخ:**",
        "version": "الإصدار 2.3.0 | نسخة المؤسسات الآمنة",
        "tabs": ["📂 رفع البيانات", "🎯 هدف التحليل", "📈 الرؤى البيانية"],
        "upload_header": "### رفع مجموعة البيانات",
        "supported_formats": "التنسيقات المدعومة: CSV, Excel (الحد الأقصى 200 ميجابايت)",
        "file_uploaded": "✅ تم التحقق من الملف '{filename}' ورفعه بنجاح!",
        "data_preview": "#### معاينة البيانات",
        "data_stats": "إجمالي الصفوف: {rows} | الأعمدة: {cols}",
        "read_error": "❌ خطأ في قراءة الملف: {e}",
        "visuals_header": "### 📊 رؤى بيانية آلية",
        "visuals_info": "👆 يرجى رفع ملف في تبويب 'رفع البيانات' لعرض الرؤى البيانية.",
        "num_cols": "الأعمدة الرقمية المكتشفة: {cols}",
        "cat_cols": "الأعمدة الفئوية المكتشفة: {cols}",
        "dist_title": "توزيع {col}",
        "corr_title": "مصفوفة الارتباط",
        "top_10": "أعلى 10 فئات في {col}",
        "goal_header": "### حدد هدف التحليل",
        "goal_label": "مالمطلوب من تحليل هذا الملف ؟",
        "goal_placeholder": "مثال: حدد أهم 3 عوامل تؤدي إلى انخفاض المبيعات في الربع الثالث واقترح تدابير لتوفير التكاليف...",
        "launch_btn": "🚀 بدء التحليل",
        "err_no_file": "⚠️ يرجى رفع ملف بيانات أولاً.",
        "err_no_intent": "⚠️ يرجى وصف هدف التحليل.",
        "err_no_api": "❌ خطأ في التكوين.",
        "status_active": "🚀 وكيل AJ نشط الآن",
        "status_persona": "🏗️ **جاري بناء شخصية الوكيل...**",
        "agent_role": "**🤖 دور الوكيل:** {role}\n\n**🎯 الهدف:** {goal}",
        "status_task": "📝 **جاري تصميم مهمة التحليل...**",
        "status_thinking": "🧠 **جاري التفكير وتحليل البيانات...** (قد يستغرق 30-60 ثانية)",
        "status_complete": "✅ اكتمل التحليل!",
        "success_msg": "✅ اكتمل التحليل!",
        "report_header": "### 📝 التقرير التنفيذي",
        "download_btn": "⬇️ تحميل التقرير الرسمي (PDF)",
        "download_help": "💡 يمكنك إعادة تسمية الملف واختيار الموقع في نافذة التحميل الخاصة بالمتصفح.",
        "analysis_error": "❌ حدث خطأ غير متوقع. تم تسجيل التفاصيل الفنية.",
        "pdf_title": "تقرير تحليل AJ",
        "pdf_generated": "تم الإنشاء في: {date}",
        "agent_backstory": "أنت مستشار من الدرجة الأولى لدى AJ Intelligent Solutions. خبرتك مصممة خصيصًا لـ: '{intent}'. أنت تقدم توصيات واضحة ومدعومة بالبيانات وقابلة للتطبيق تجاريًا.",
        "security_warning": "⚠️ تنبيه أمني: {message}"
    }
}

# --- Sidebar Navigation & Settings ---
with st.sidebar:
    # Logo Integration
    if os.path.exists("logo.png"):
        col1, col2, col3 = st.columns([1, 4, 1])
        with col2:
             st.image("logo.png", use_container_width=True)
    else:
        st.markdown("## AJ")
        
    st.markdown("---")
    
    # Language Selection with Persistence
    language = st.radio(
        "Interface Language / لغة الواجهة",
        options=["English", "Arabic"],
        index=0 if st.session_state.language == "English" else 1,
        key="language"
    )
    
    t = translations[st.session_state.language] 
    
    st.markdown("---")
    st.caption(f"{t['today']} {datetime.date.today()}")
    st.caption(t["version"])
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; font-size: 0.8rem; opacity: 0.7;">
            Developed by Ahmed Hassan Aljohani<br>
            Built with CrewAI & Streamlit
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Dynamic CSS for Permanent Dark Mode & RTL ---
# Permanent Dark Mode Styles
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');

    /* Global Settings - Premium Dark Theme */
    :root {
        --primary-color: #20B2AA;
        --background-color: #0E1117;
        --secondary-background-color: #262730;
        --text-color: #FAFAFA;
    }

    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        background-color: var(--background-color);
        color: var(--text-color) !important;
    }

    /* Headers */
    .main-header {
        color: var(--primary-color);
        font-weight: 700;
        font-size: 3rem;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .sub-header {
        color: #E0E0E0; /* High contrast off-white */
        opacity: 0.9;
        font-size: 1.5rem;
        font-weight: 300;
        margin-bottom: 2.5rem;
        text-align: center;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        border: 1px solid var(--primary-color);
        color: var(--primary-color);
    }
    
    /* Alerts/Status */
    .stAlert {
        border-radius: 8px;
    }

    /* Input Fields & Text Areas - Darker Background for Contrast */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #1E2129;
        color: #FAFAFA;
        border-color: #4B4B4B;
    }
    
    /* DataFrame Background */
    [data-testid="stDataFrame"] {
        background-color: #1E2129;
    }
    
    /* PDF Download Button - High Contrast Solid Teal */
    [data-testid="stDownloadButton"] > button {
        background-color: #20B2AA !important;
        color: #FFFFFF !important;
        border: 1px solid #20B2AA !important;
        font-weight: bold !important;
        transition: none !important;
        box-shadow: none !important;
        text-shadow: none !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background-color: #178A84 !important;
        color: #FFFFFF !important;
        border: 1px solid #178A84 !important;
        box-shadow: none !important;
    }
</style>
"""

# RTL Support
if st.session_state.language == "Arabic":
    rtl_css = """
<style>
    .stTextInput, .stTextArea, .stMarkdown, .stDataFrame, .stAlert, .stButton, p, h1, h2, h3, h4, h5, h6 {
        direction: rtl;
        text-align: right;
    }
    .main-header, .sub-header {
        text-align: center; /* Keep headers centered */
    }
    /* Ensure lists in markdown are also RTL if possible */
    ul {
        direction: rtl;
        text-align: right;
    }
</style>
"""
    custom_css += rtl_css

st.markdown(custom_css, unsafe_allow_html=True)

# --- Helper Functions ---

# Security: Input Sanitization
def sanitize_prompt(text):
    """
    Strips potential prompt injection attacks from user input.
    """
    patterns = [
        r"ignore previous instructions",
        r"system override",
        r"delete all files",
        r"show configuration",
        r"reveal keys"
    ]
    cleaned_text = text
    for pattern in patterns:
        cleaned_text = re.sub(pattern, "[REDACTED]", cleaned_text, flags=re.IGNORECASE)
    return cleaned_text

# Security: Strict File Validation
def validate_uploaded_file(uploaded_file):
    """
    Validates file extension, size, and magic bytes to prevent malicious uploads.
    """
    valid_extensions = ['.csv', '.xlsx']
    filename = uploaded_file.name.lower()
    
    # 1. Extension Check
    if not any(filename.endswith(ext) for ext in valid_extensions):
        return False, "Invalid file type. Only CSV and Excel are allowed."
    
    # 2. Size Check (Limit to 200MB)
    MAX_SIZE_MB = 200
    if uploaded_file.size > MAX_SIZE_MB * 1024 * 1024:
        return False, f"File size exceeds limit ({MAX_SIZE_MB}MB)."

    # 3. Magic Byte Verification
    try:
        # Read first few bytes
        header = uploaded_file.read(4)
        uploaded_file.seek(0)  # Reset pointer
        
        if filename.endswith('.xlsx'):
            # ZIP signature for .xlsx (PK\x03\x04)
            if header != b'PK\x03\x04':
                return False, "Security Check Failed: Invalid file signature for Excel."
        
        # CSVs are text files and don't have consistent magic bytes, 
        # but we can try to decode a chunk to ensure it's text.
        if filename.endswith('.csv'):
            try:
                chunk = uploaded_file.read(1024)
                uploaded_file.seek(0)
                chunk.decode('utf-8')
            except UnicodeDecodeError:
                return False, "Security Check Failed: File is not a valid text/CSV file."
                
    except Exception as e:
        return False, f"Validation Error: {str(e)}"
        
    return True, "Valid"

class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        self.font_path = None
        self.has_custom_font = False
        
        # Priority: Local arial.ttf > Local DejaVuSans.ttf > System arial.ttf
        possible_fonts = [
            "arial.ttf",
            "DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf"
        ]
        
        for path in possible_fonts:
            if os.path.exists(path):
                self.font_path = path
                self.has_custom_font = True
                break
        
        # Add Fonts if found
        if self.has_custom_font:
            try:
                self.add_font('CustomFont', '', self.font_path, uni=True)
                self.add_font('CustomFont', 'B', self.font_path, uni=True) # Map Bold to same file if no bold variant
            except Exception as e:
                logging.error(f"Font loading error: {e}")
                self.has_custom_font = False
        
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        
        if self.has_custom_font:
             self.set_font('CustomFont', '', 8)
        else:
             self.set_font('Arial', 'I', 8)
             
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_bytes(content, title, lang="English", t_dict=None):
    """
    Generates PDF in-memory and returns bytes. No file is written to disk.
    """
    try:
        pdf = PDFReport()
        pdf.add_page()
        
        # Title Page
        if pdf.has_custom_font:
            pdf.set_font("CustomFont", 'B', 18)
        else:
            pdf.set_font("Arial", 'B', 18)

        if lang == "Arabic" and pdf.has_custom_font:
            title_reshaped = get_display(arabic_reshaper.reshape(title))
            pdf.cell(0, 10, title_reshaped, ln=True, align='C')
            
            generated_on = t_dict["pdf_generated"].format(date=datetime.date.today())
            gen_reshaped = get_display(arabic_reshaper.reshape(generated_on))
            pdf.set_font("CustomFont", '', 10)
            pdf.cell(0, 10, gen_reshaped, ln=True, align='C')
            pdf.ln(10)
        else:
            pdf.cell(0, 10, title, ln=True, align='C')
            
            generated_on = t_dict["pdf_generated"].format(date=datetime.date.today())
            if pdf.has_custom_font:
                pdf.set_font("CustomFont", '', 10)
            else:
                pdf.set_font("Arial", '', 10)
            pdf.cell(0, 10, generated_on, ln=True, align='C')
            pdf.ln(10)

        # Content Parsing & Formatting
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                pdf.ln(5)
                continue
            
            # Detect Headers (Markdown style)
            # Support #, ##, ###, or **Header**
            is_header = line.startswith('#') or line.startswith('**')
            
            # Remove Markdown symbols for cleaner PDF
            clean_line = re.sub(r'^[*#]+\s*', '', line).replace('**', '').strip()
            
            if lang == "Arabic" and pdf.has_custom_font:
                reshaped_line = arabic_reshaper.reshape(clean_line)
                bidi_line = get_display(reshaped_line)
                align = 'R'
            else:
                bidi_line = clean_line
                align = 'L'

            if is_header:
                if pdf.has_custom_font:
                    pdf.set_font("CustomFont", 'B', 14)
                else:
                    pdf.set_font("Arial", 'B', 14)
                
                # Add some spacing before header
                pdf.ln(5)
                pdf.cell(0, 10, bidi_line, ln=True, align=align)
                
                # Add underline for major headers (starts with #)
                if line.startswith('#'): 
                    pdf.line(pdf.get_x(), pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
                
                pdf.ln(2)
            else:
                if pdf.has_custom_font:
                    pdf.set_font("CustomFont", '', 11)
                else:
                    pdf.set_font("Arial", '', 11)
                
                pdf.multi_cell(0, 8, bidi_line, align=align)
        
        # Output to string (latin-1 encoding of the internal byte stream) and convert to bytes
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        logging.error(f"PDF Generation Error: {e}")
        return None

def visualize_data(df, t_dict):
    st.markdown(t_dict["visuals_header"])
    
    num_cols = df.select_dtypes(include=['float64', 'int64']).columns
    cat_cols = df.select_dtypes(include=['object', 'category']).columns

    # Adaptive Chart Theme - Permanent Dark
    chart_theme = "plotly_dark"
    color_seq = ['#20B2AA', '#008080', '#40E0D0']

    if len(num_cols) > 0:
        st.info(t_dict["num_cols"].format(cols=', '.join(num_cols)))
        
        fig_hist = px.histogram(df, x=num_cols[0], title=t_dict["dist_title"].format(col=num_cols[0]), 
                                color_discrete_sequence=color_seq, template=chart_theme)
        # Ensure seamless background
        fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_hist, use_container_width=True)
        
        if len(num_cols) > 1:
            fig_corr = px.imshow(df[num_cols].corr(), text_auto=True, title=t_dict["corr_title"], 
                                 color_continuous_scale='Teal', template=chart_theme)
            fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_corr, use_container_width=True)

    if len(cat_cols) > 0:
        st.info(t_dict["cat_cols"].format(cols=', '.join(cat_cols)))
        top_counts = df[cat_cols[0]].value_counts().nlargest(10)
        fig_bar = px.bar(top_counts, x=top_counts.index, y=top_counts.values, 
                         title=t_dict["top_10"].format(col=cat_cols[0]),
                         labels={'x': cat_cols[0], 'y': 'Count'},
                         color_discrete_sequence=color_seq, template=chart_theme)
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)

# --- Main Layout ---
st.markdown(f'<div class="main-header">{t["page_title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">{t["tagline"]}</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(t["tabs"])

uploaded_file = None
df = None

# Tab 1: Data Upload
with tab1:
    st.markdown(t["upload_header"])
    st.markdown(t["supported_formats"])
    uploaded_file = st.file_uploader("", type=["csv", "xlsx"])
    
    if uploaded_file:
        # Security: Validate File
        is_valid, msg = validate_uploaded_file(uploaded_file)
        
        if not is_valid:
            st.error(t["security_warning"].format(message=msg))
            logging.warning(f"Security Alert: Invalid file upload attempt - {uploaded_file.name}")
            uploaded_file = None # Block processing
        else:
            try:
                # Security: In-Memory Processing (No disk save)
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.success(t["file_uploaded"].format(filename=uploaded_file.name))
                st.markdown(t["data_preview"])
                st.dataframe(df.head(), use_container_width=True)
                st.caption(t["data_stats"].format(rows=len(df), cols=len(df.columns)))
            except Exception as e:
                logging.error(f"File processing error: {e}")
                st.error(t["read_error"].format(e="Unable to process file. Please ensure it is not corrupted."))

# Tab 3: Visual Insights
with tab3:
    if df is not None:
        visualize_data(df, t)
    else:
        st.info(t["visuals_info"])

# Tab 2: Analysis Goal
with tab2:
    st.markdown(t["goal_header"])
    user_intent_raw = st.text_area(
        t["goal_label"],
        placeholder=t["goal_placeholder"],
        height=150,
        max_chars=2000
    )
    
    st.markdown("---")
    if st.button(t["launch_btn"], type="primary", use_container_width=True):
        if not uploaded_file or df is None:
            st.error(t["err_no_file"])
        elif not user_intent_raw:
            st.error(t["err_no_intent"])
        else:
            try:
                # Security: Sanitize Input
                user_intent = sanitize_prompt(user_intent_raw)
                if user_intent != user_intent_raw:
                     logging.warning(f"Sanitization triggered on input: {user_intent_raw}")
                
                with st.status(t["status_active"], expanded=True) as status:
                    
                    my_llm = LLM(
                        model="gemini/gemini-flash-latest",
                        api_key=os.getenv("GOOGLE_API_KEY")
                    )
                    
                    status.write(t["status_persona"])
                    dynamic_role = f"Expert Analyst - {user_intent[:40]}..."
                    dynamic_goal = f"Provide expert insights on: {user_intent}"
                    # Backstory uses formatting to inject intent
                    dynamic_backstory = t["agent_backstory"].format(intent=user_intent)
                    
                    st.info(t["agent_role"].format(role=dynamic_role, goal=dynamic_goal))
                    
                    specialized_agent = Agent(
                        role=dynamic_role,
                        goal=dynamic_goal,
                        backstory=dynamic_backstory,
                        llm=my_llm,
                        verbose=True
                    )
                    
                    status.write(t["status_task"])
                    data_str = df.to_string()
                    current_date = datetime.date.today()
                    
                    analysis_task = Task(
                        description=f'''
                        **Context:** Today is {current_date}.
                        
                        **Objective:** Analyze the provided dataset to address this specific request:
                        "{user_intent}"
                        
                        **Data Snippet:**
                        {data_str}
                        
                        **Formatting Instructions:**
                        - Write strictly in {language}.
                        - Use professional business tone.
                        - Structure with clear headings (Executive Summary, Findings, Recommendations).
                        ''',
                        agent=specialized_agent,
                        expected_output=f"A professional business report in {language}."
                    )
                    
                    status.write(t["status_thinking"])
                    my_crew = Crew(
                        agents=[specialized_agent],
                        tasks=[analysis_task]
                    )
                    
                    result = my_crew.kickoff()
                    status.update(label=t["status_complete"], state="complete", expanded=False)
                
                st.success(t["success_msg"])
                
                st.markdown(t["report_header"])
                st.markdown(result)
                
                # Dynamic Filename Generation
                clean_topic = re.sub(r'[^a-zA-Z0-9\s]', '', user_intent[:30]).replace(' ', '_')
                pdf_filename = f"Report_{clean_topic}_{datetime.date.today()}.pdf"
                
                # Security: Generate PDF in memory
                pdf_bytes = generate_pdf_bytes(str(result), t["pdf_title"], lang=language, t_dict=t)
                
                if pdf_bytes:
                    st.download_button(
                        label=t["download_btn"],
                        data=pdf_bytes,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        type="secondary"
                    )
                    st.caption(t["download_help"])
                else:
                    st.error("Error generating PDF report.")
                        
            except Exception as e:
                # Security: Error Masking
                logging.error(f"Critical Application Error: {e}", exc_info=True)
                st.error(t["analysis_error"])
