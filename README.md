File Analysis Platform: AI-Powered Insights
Advanced Data Analysis Platform built with CrewAI & Streamlit 

🌟 Overview
File Analysis Platform is an enterprise-grade SaaS platform designed to transform raw datasets into executive-level insights. Developed by Ahmed Aljohani, the platform leverages multi-agent AI systems to provide deep data analysis and automated professional reporting. It is optimized for high-performance cloud environments and follows the latest development standards for 2026.

✨ Key Features
🤖 AI Agent Analysis: Utilizes CrewAI and Gemini 1.5 Flash to simulate a top-tier consultant tailored to your specific analysis goal.

📊 Automated Visuals: Generates instant interactive histograms, correlation matrices, and bar charts using Plotly Express.

📄 Dynamic PDF Reports: Automatically creates in-memory PDF executive reports with full support for complex text reshaping and bidirectional formatting.

🌍 Intelligent Localization: A seamless interface that adapts to user preferences, including dynamic filename generation in both English and Arabic.

🛡️ Robust Security: Includes strict file validation (magic bytes), input sanitization to prevent prompt injection, and secure API key management via system secrets.

🌙 Premium Dark Mode: A custom-themed UI designed to reduce eye strain during long analytical sessions.

🛠️ Tech Stack

Frontend: Streamlit (v1.53.1+) 

AI Framework: CrewAI (v0.30.0+)

LLM Model: Google Gemini 1.5 Flash

Data Science: Pandas, Plotly Express

Reporting: FPDF, Arabic-Reshaper, Python-BiDi

🚀 Installation & Setup
Clone the repository:

Bash
git clone https://github.com/ahmedjohani/file-analysis-platform.git


Install dependencies:

Bash
pip install -r requirements.txt
Set up Environment Variables: Create a .env file or use your hosting provider's Secrets manager:

مقتطف الرمز
GOOGLE_API_KEY=your_secure_api_key_here
Run the application:

Bash
streamlit run my_agent.py


🛡️ Stability & Security Patches
This project implements advanced engineering solutions to handle cloud-specific challenges:

Telemetry Isolation: Environment variables are configured to disable telemetry at the entry point to ensure stability in multi-threaded cloud environments.

Threading Patch: A custom signal-handling override is implemented to prevent the ValueError: signal only works in main thread common in Streamlit/CrewAI integrations.

Import Optimization: A strictly ordered initialization sequence ensures all system resources are defined before being accessed by the AI engine.

👤 Developer
Ahmed Aljohani

Status: Computer Science Student & Programmer.

Focus: Building AI-driven solutions for service-based businesses.