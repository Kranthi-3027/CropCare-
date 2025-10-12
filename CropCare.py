# -------------------------------------------------
# Single-Sector (Agriculture) Document Analysis App - CropCare
# -------------------------------------------------
import os, io, re, time, html, hashlib, base64
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import PyPDF2, docx
from PIL import Image
from langdetect import detect
import google.generativeai as genai
from gtts import gTTS

# -------------------------------------------------
# API / Models
# -------------------------------------------------
API_KEY = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-flash-lite"
model = genai.GenerativeModel(MODEL_NAME)
vision_model = genai.GenerativeModel(MODEL_NAME)

# -------------------------------------------------
# App Config
# -------------------------------------------------
st.set_page_config(
    page_title="CropCare",
    page_icon="🌾",
    layout="wide"
)

# -------------------------------------------------
# State Defaults
# -------------------------------------------------
DEFAULT_STATE = {
    "language_selected": False,
    "sector_selected": False,
    "selected_language": "",
    "selected_sector": "Agriculture",
    "doc_text": "",
    "summary": "",
    "chat_history": [],
    "general_messages": [],
    "_render_flag": False
}
for k, v in DEFAULT_STATE.items():
    st.session_state.setdefault(k, v)

# -------------------------------------------------
# Languages / Sectors (Simplified)
# -------------------------------------------------
LANGUAGES = {
    "English": "🇺🇸",
    "हिंदी": "🇮🇳",
    "తెలుగు": "🇮🇳",
    "മലയാളം": "🇮🇳"
}

LANG_CODE_MAP_TTS = {
    "English": "en", "हिंदी": "hi", "తెలుగు": "te", "മലയാളം": "ml"
}

SECTOR_LABELS = {
    "English":     {"Agriculture": "Agriculture"},
    "हिंदी":       {"Agriculture": "कृषि"},
    "తెలుగు":      {"Agriculture": "వ్యవసాయం"},
    "മലയാളം":     {"Agriculture": "കൃഷി"},
}

def sector_label(name: str) -> str:
    lang = st.session_state.get("selected_language", "English")
    return SECTOR_LABELS.get(lang, SECTOR_LABELS["English"]).get(name, name)

# -------------------------------------------------
# UI Translations
# -------------------------------------------------
UI_TRANSLATIONS = {
    "English": {
        "select_language": "🌍 Select Your Language",
        "choose_language": "Choose your preferred language to continue",
        "selected_language": "Selected Language",
        "back_language": "← Back to Language Selection",
        "settings": "⚙️ Settings",
        "change_lang_sector": "🔄 Change Language",
        "current": "Current",
        "uploader_any": "Upload ANY file type (📄 Documents + 🖼️ Images)",
        "sample_doc_btn": "📝 Load sample {sector} document",
        "sample_try": "Try sample data if there is no file ready",
        "extracting": "Extracting text…",
        "generating": "Generating analysis…",
        "thinking": "Thinking...",
        "no_text": "No readable text found in the uploaded file.",
        "analyzing_image": "🔍 Analyzing image...",
        "image_analysis_header": "🖼️ Image Analysis",
        "uploaded_image_caption": "Uploaded {sector} Image",
        "extracting_image_text": "Extracting text from image...",
        "enhanced_title_suffix": " – Enhanced AI Analysis",
        "info_agri": "🌍 Language: {lang_flag} {lang} | 🌾 Sector: Agricultural Analysis + Crop Image Recognition",
        "tab_doc": "📄 Enhanced {sector} Analysis",
        "tab_gen": "🧭 General {sector} Help",
        "enhanced_analysis_header": "📊 Enhanced {sector} Analysis",
        "chat_about_analysis": "💬 Ask Questions About This Analysis",
        "chat_placeholder": "Ask any question about this analysis...",
        "examples_try": "Try asking:",
        "gen_help_header": "🧭 General {sector} Help & Consultation",
        "gen_help_caption": "Ask any {sector_lower}-related questions — here to help!",
        "gen_chat_placeholder": "Ask any {sector_lower} question...",
        "examples_caption": "Example questions:",
        "enhanced_features_title": "🚀 Features:",
        "features_agri_1": "🌱 Crop disease detection",
        "features_agri_2": "🐛 Pest identification",
        "features_agri_3": "📊 Soil analysis from images",
        "disclaimer_block_header": "⚠️ Disclaimer:",
        "disclaimer_agri": "- Agricultural: Recommendations are general—consider local conditions",
        "disclaimer_footer": "- Always verify critical information with qualified professionals",
        "document": "Document",
        "analysis_summary": "📑 Analysis Summary"
    },
    "हिंदी": {
        "select_language": "🌍 अपनी भाषा चुनें",
        "choose_language": "जारी रखने के लिए अपनी पसंदीदा भाषा चुनें",
        "selected_language": "चयनित भाषा",
        "back_language": "← भाषा चयन पर वापस",
        "settings": "⚙️ सेटिंग्स",
        "change_lang_sector": "🔄 भाषा बदलें",
        "current": "वर्तमान",
        "uploader_any": "किसी भी फ़ाइल प्रकार को अपलोड करें (📄 दस्तावेज़ + 🖼️ छवियाँ)",
        "sample_doc_btn": "📝 नमूना {sector} दस्तावेज़ लोड करें",
        "sample_try": "यदि फ़ाइल तैयार नहीं है तो नमूना आज़माएँ",
        "extracting": "पाठ निकाला जा रहा है…",
        "generating": "विश्लेषण बनाया जा रहा है…",
        "thinking": "सोच रहा है...",
        "no_text": "अपलोड की गई फ़ाइल में पढ़ने योग्य पाठ नहीं मिला।",
        "analyzing_image": "🔍 छवि का विश्लेषण हो रहा है...",
        "image_analysis_header": "🖼️ छवि विश्लेषण",
        "uploaded_image_caption": "अपलोड की गई {sector} छवि",
        "extracting_image_text": "छवि से पाठ निकाला जा रहा है...",
        "enhanced_title_suffix": " – उन्नत AI विश्लेषण",
        "info_agri": "🌍 भाषा: {lang_flag} {lang} | 🌾 क्षेत्र: कृषि विश्लेषण + फसल छवि पहचान",
        "tab_doc": "📄 उन्नत {sector} विश्लेषण",
        "tab_gen": "🧭 सामान्य {sector} सहायता",
        "enhanced_analysis_header": "📊 उन्नत {sector} विश्लेषण",
        "chat_about_analysis": "💬 इस विश्लेषण के बारे में प्रश्न पूछें",
        "chat_placeholder": "इस विश्लेषण के बारे में कोई भी प्रश्न पूछें...",
        "examples_try": "कोशिश करें पूछने की:",
        "gen_help_header": "🧭 सामान्य {sector} सहायता और परामर्श",
        "gen_help_caption": "किसी भी {sector_lower}-संबंधित प्रश्न पूछें — मदद के लिए तैयार!",
        "gen_chat_placeholder": "कोई भी {sector_lower} प्रश्न पूछें...",
        "examples_caption": "उदाहरण प्रश्न:",
        "enhanced_features_title": "🚀 विशेषताएँ:",
        "features_agri_1": "🌱 फसल रोग पहचान",
        "features_agri_2": "🐛 कीट पहचान",
        "features_agri_3": "📊 छवियों से मिट्टी विश्लेषण",
        "disclaimer_block_header": "⚠️अस्वीकरण:",
        "disclaimer_agri": "- कृषि: सिफारिशें सामान्य हैं—स्थानीय परिस्थितियों पर विचार करें",
        "disclaimer_footer": "- महत्वपूर्ण जानकारी को हमेशा योग्य विशेषज्ञों से सत्यापित करें",
        "document": "दस्तावेज़",
        "analysis_summary": "📑 विश्लेषण सारांश"
    },
    "తెలుగు": {
        "select_language": "🌍 మీ భాషను ఎంచుకోండి",
        "choose_language": "కొనసాగేందుకు మీకు నచ్చిన భాషను ఎంచుకోండి",
        "selected_language": "ఎంచుకున్న భాష",
        "back_language": "← భాష ఎంపికకు వెనక్కి",
        "settings": "⚙️ అమరికలు",
        "change_lang_sector": "🔄 భాష మార్చండి",
        "current": "ప్రస్తుతము",
        "uploader_any": "ఏ ఫైల్ రకమైనా అప్లోడ్ చేయండి (📄 పత్రాలు + 🖼️ చిత్రాలు)",
        "sample_doc_btn": "📝 నమూనా {sector} పత్రాన్ని లోడ్ చేయండి",
        "sample_try": "ఫైళ్లు సిద్ధంగా లేకపోతే నమూనా ప్రయత్నించండి",
        "extracting": "పాఠ్యాన్ని వెలికితీస్తున్నాం…",
        "generating": "విశ్లేషణను సృష్టిస్తున్నాం…",
        "thinking": "ఆలోచిస్తున్నాను...",
        "no_text": "ఈ ఫైల్‌లో చదవగలిగే పాఠ్యం కనిపించలేదు.",
        "analyzing_image": "🔍 చిత్రాన్ని విశ్లేషిస్తున్నాం...",
        "image_analysis_header": "🖼️ చిత్రం విశ్లేషణ",
        "uploaded_image_caption": "అప్లోడ్ చేసిన {sector} చిత్రం",
        "extracting_image_text": "చిత్రం నుండి పాఠ్యాన్ని వెలికితీస్తున్నాం...",
        "enhanced_title_suffix": " – అధునాతన AI విశ్లేషణ",
        "info_agri": "🌍 భాష: {lang_flag} {lang} | 🌾 విభాగం: వ్యవసాయ విశ్లేషణ + పంట చిత్రం గుర్తింపు",
        "tab_doc": "📄 అధునాతన {sector} విశ్లేషణ",
        "tab_gen": "🧭 సాధారణ {sector} సహాయం",
        "enhanced_analysis_header": "📊 అధునాతన {sector} విశ్లేషణ",
        "chat_about_analysis": "💬 ఈ విశ్లేషణ గురించి ప్రశ్నలు అడగండి",
        "chat_placeholder": "ఈ విశ్లేషణ గురించి ఏదైనా ప్రశ్న అడగండి...",
        "examples_try": "ఇలా అడగండి:",
        "gen_help_header": "🧭 సాధారణ {sector} సహాయం & సలహా",
        "gen_help_caption": "ఏదైనా {sector_lower} సంబంధిత ప్రశ్నలు అడగండి — సహాయం కోసం సిద్ధంగా ఉన్నాము!",
        "gen_chat_placeholder": "ఏదైనా {sector_lower} ప్రశ్న అడగండి...",
        "examples_caption": "ఉదాహరణ ప్రశ్నలు:",
        "enhanced_features_title": "🚀 లక్షణాలు:",
        "features_agri_1": "🌱 పంట రోగాల గుర్తింపు",
        "features_agri_2": "🐛 కీటకాలను గుర్తించడం",
        "features_agri_3": "📊 చిత్రాల నుండి మట్టి విశ్లేషణ",
        "disclaimer_block_header": "⚠️ గమనిక:",
        "disclaimer_agri": "- వ్యవసాయం: సిఫారసులు సాధారణం — స్థానిక పరిస్థితులను పరిగణించండి",
        "disclaimer_footer": "- ముఖ్య సమాచారాన్ని ఎల్లప్పుడూ అర్హులైన నిపుణులతో ధృవీకరించండి",
        "document": "పత్రం",
        "analysis_summary": "📑 విశ్లేషణ సారాంశం"
    },
    "മലയാളം": {
        "select_language": "🌍 ഭാഷ തിരഞ്ഞെടുക്കുക",
        "choose_language": "തുടരാൻ ഇഷ്ടമുള്ള ഭാഷ തിരഞ്ഞെടുക്കുക",
        "selected_language": "തിരഞ്ഞെടുത്ത ഭാഷ",
        "back_language": "← ഭാഷ തിരഞ്ഞെടുപ്പിലേക്ക് മടങ്ങുക",
        "settings": "⚙️ ക്രമീകരണങ്ങൾ",
        "change_lang_sector": "🔄 ഭാഷ മാറ്റുക",
        "current": "നിലവിൽ",
        "uploader_any": "ഏത് ഫയൽ തരം വേണമെങ്കിലും അപ്‌ലോഡ് ചെയ്യുക (📄 രേഖകൾ + 🖼️ ചിത്രങ്ങൾ)",
        "sample_doc_btn": "📝 സാമ്പിൾ {sector} രേഖ ലോഡ് ചെയ്യുക",
        "sample_try": "ഫയൽ ഇല്ലെങ്കിൽ സാമ്പിൾ പരീക്ഷിക്കുക",
        "extracting": "ടെക്സ്റ്റ് എടുത്തുകൊണ്ടിരിക്കുന്നു…",
        "generating": "വിശകലനം സൃഷ്ടിക്കുന്നു…",
        "thinking": "ചിന്തിക്കുന്നു...",
        "no_text": "അപ്‌ലോഡ് ചെയ്ത ഫയലിൽ വായിക്കാൻ പറ്റുന്ന ടെക്സ്റ്റ് കണ്ടെത്താനായില്ല.",
        "analyzing_image": "🔍 ചിത്രം വിശകലനം ചെയ്യുന്നു...",
        "image_analysis_header": "🖼️ ചിത്രം വിശകലനം",
        "uploaded_image_caption": "അപ്‌ലോഡ് ചെയ്ത {sector} ചിത്രം",
        "extracting_image_text": "ചിത്രത്തിൽ നിന്ന് ടെക്സ്റ്റ് എടുത്തുകൊണ്ടിരിക്കുന്നു...",
        "enhanced_title_suffix": " – ഉയർന്ന നിലവാരമുള്ള AI വിശകലനം",
        "info_agri": "🌍 ഭാഷ: {lang_flag} {lang} | 🌾 വിഭാഗം: കാർഷിക വിശകലനം + വിള ചിത്ര തിരിച്ചറിയൽ",
        "tab_doc": "📄 ഉയർന്ന നിലവാരമുള്ള {sector} വിശകലനം",
        "tab_gen": "🧭 പൊതുവായ {sector} സഹായം",
        "enhanced_analysis_header": "📊 ഉയർന്ന നിലവാരമുള്ള {sector} വിശകലനം",
        "chat_about_analysis": "💬 ഈ വിശകലനത്തെ കുറിച്ച് ചോദ്യങ്ങൾ ചോദിക്കുക",
        "chat_placeholder": "ഈ വിശകലനത്തെ കുറിച്ച് ഏതെങ്കിലും ചോദ്യമുണ്ടോ...",
        "examples_try": "ഇങ്ങനെ ചോദിക്കുക:",
        "gen_help_header": "🧭 പൊതുവായ {sector} സഹായവും നിർദേശവും",
        "gen_help_caption": "{sector_lower} സംബന്ധമായ ഏതെങ്കിലും ചോദ്യങ്ങൾ ചോദിക്കുക — സഹായത്തിനായി തയ്യാറാണ്!",
        "gen_chat_placeholder": "ഏതെങ്കിലും {sector_lower} ചോദ്യം ചോദിക്കുക...",
        "examples_caption": "ഉദാഹരണ ചോദ്യങ്ങൾ:",
        "enhanced_features_title": "🚀 വിശേഷഗുണങ്ങൾ:",
        "features_agri_1": "🌱 വിള രോഗം തിരിച്ചറിയൽ",
        "features_agri_2": "🐛 കീടം തിരിച്ചറിയൽ",
        "features_agri_3": "📊 ചിത്രങ്ങളിൽ നിന്ന് മണ്ണ് വിശകലനം",
        "disclaimer_block_header": "⚠️ അറിയിപ്പ്:",
        "disclaimer_agri": "- കാർഷികം: നിർദേശങ്ങൾ പൊതുവായതാണ് — പ്രാദേശിക സാഹചര്യങ്ങൾ പരിഗണിക്കുക",
        "disclaimer_footer": "- പ്രധാന വിവരങ്ങൾ എപ്പോഴും യോഗ്യനായ വിദഗ്ധരുമായി സ്ഥിരീകരിക്കുക",
        "document": "രേഖ",
        "analysis_summary": "📑 വിശകലന സംഗ്രഹം"
    },
}

def get_text(key: str) -> str:
    lang = st.session_state.get("selected_language", "English")
    return UI_TRANSLATIONS.get(lang, UI_TRANSLATIONS["English"]).get(key, key)

def pick_tts_code(lang_name: str) -> str:
    return LANG_CODE_MAP_TTS.get(lang_name, "en")

# -------------------------------------------------
# CSS Styling
# -------------------------------------------------
PALETTES = {
    "Agriculture":{"brand": "#16A34A", "brand2": "#F59E0B", "bg1": "#DCFCE7", "bg2": "#FEF3C7"},
}
pal = PALETTES["Agriculture"]
st.markdown(f"""
<style>
/* Force readable light scheme and strong foreground */
html {{ color-scheme: light; }}
:root {{
  --brand: {pal["brand"]};
  --brand-2: {pal["brand2"]};
  --bg-grad-1: {pal["bg1"]};
  --bg-grad-2: {pal["bg2"]};
  --text: #0F172A;              /* Dark slate for high contrast */
  --text-weak: #334155;
  --surface: #ffffff;
  --border: #E5E7EB;
}}
/* Background stays colorful but subtle */
.stApp {{
  background:
    radial-gradient(1200px 600px at 10% 0%, var(--bg-grad-1), transparent 60%),
    radial-gradient(1000px 500px at 100% 10%, var(--bg-grad-2), transparent 60%),
    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}}
/* GLOBAL TYPOGRAPHY */
html, body, [class*="css"] {{
  font-family: "Inter","Poppins","Noto Sans","Noto Sans Telugu","Noto Sans Devanagari","Noto Sans Malayalam",
               system-ui,-apple-system,Segoe UI,Roboto,"Helvetica Neue",Arial,"Noto Color Emoji","Apple Color Emoji","Segoe UI Emoji",sans-serif !important;
  color: var(--text);
}}
h1, h2, h3, h4, h5, h6 {{
  color: var(--text) !important;
  font-weight: 700;
}}
/* BUTTONS */
div.stButton > button {{
  background: linear-gradient(135deg, var(--brand), var(--brand-2));
  color: #fff !important;
  border: none; border-radius: 14px;
  padding: 0.9rem 1.1rem;
  box-shadow: 0 8px 24px rgba(0,0,0,.12);
  transition: transform .15s ease, box-shadow .15s ease, filter .2s ease;
}}
div.stButton > button:hover {{
  transform: translateY(-1px);
  box-shadow: 0 12px 30px rgba(0,0,0,.18);
  filter: brightness(1.03);
}}
/* TABS */
.stTabs [role="tab"][aria-selected="true"] {{
  background: linear-gradient(135deg, var(--brand), var(--brand-2));
  color: #fff !important; border-color: transparent !important;
}}
/* TEXT INPUTS */
.stTextInput > div > div input:focus,
.stTextArea > div > textarea:focus {{
  border-color: var(--brand);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand) 25%, transparent);
}}
/* Separate sections subtly */
.hr-soft {{ margin: .8rem 0 1rem 0; border: none; height: 1px;
  background: linear-gradient(90deg, transparent, #e5e7eb, transparent); }}
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------
# AI Helpers
# -------------------------------------------------
def analyze_image_with_ai(image_bytes: bytes, language: str, query: str | None = None) -> str:
    image_part = {"mime_type": "image/jpeg", "data": base64.b64encode(image_bytes).decode('utf-8')}
    prompt = f"You are CropCare. Analyze this agricultural image in {language}: identification, problems, solutions, and prevention."
    try:
        # Pass both prompt and image to the vision model
        response = vision_model.generate_content([prompt, image_part])
        return response.text
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def get_sector_prompt(mode: str = "summary") -> str:
    prompts = {
        "summary": "You are CropCare 🌾, an agricultural document explainer. ONLY analyze agricultural documents.",
        "chat": "You are CropCare 🌾, an agricultural assistant. ONLY answer agriculture questions.",
        "general": "You are CropCare 🌾, an agricultural guide. ONLY provide farming information."
    }
    return prompts.get(mode, prompts["summary"])

def ask_ai(document_text: str | None = None, query: str | None = None, mode: str = "summary", image_bytes: bytes | None = None) -> str:
    language = st.session_state.selected_language

    if not document_text:
        document_text = st.session_state.get("doc_text", "")

    if image_bytes:
        return analyze_image_with_ai(image_bytes, language, query)

    sector_restriction = "CRITICAL: Provide only agriculture-related information."
    lang_clause = f"Respond ONLY in {language}."
    base_prompt = get_sector_prompt(mode)

    if mode == "summary":
        prompt = f"""{base_prompt}
{lang_clause}
{sector_restriction}
Analyze this document in {language}:
- Summary, Key findings, Important recommendations, and Risks
Document:
{document_text}
"""
    elif mode == "chat":
        prompt = f"""{base_prompt}
{lang_clause}
{sector_restriction}
Document context:
{document_text}
User question: {query}
"""
    else: # general mode
        prompt = f"""{base_prompt}
{lang_clause}
{sector_restriction}
User question: {query}
"""
    # For text-only tasks, we can use the 'model' object
    response = model.generate_content(prompt, generation_config={"temperature": 0.7, "max_output_tokens": 1500})
    return response.text

# -------------------------------------------------
# TTS
# -------------------------------------------------
def clean_text(text: str) -> str:
    # Removes emojis and markdown for cleaner TTS
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002700-\U000027BF"
        u"\U0001F900-\U0001F9FF"
        u"\U00002600-\U000026FF"
        u"\U00002B00-\U00002BFF"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    text = re.sub(r'(\*\*|__|\*|_|#+)', '', text)
    return text.strip()

def tts_speak_toggle(text: str, lang_name: str):
    safe_text = clean_text(text)
    lang_code = pick_tts_code(lang_name)
    try:
        tts = gTTS(text=safe_text, lang=lang_code, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        st.audio(audio_buffer.getvalue(), format='audio/mp3')
    except Exception as e:
        st.error(f"TTS generation failed: {e}")

# -------------------------------------------------
# OCR with Gemini Vision
# -------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def extract_text_with_gemini_vision(_image_bytes: bytes) -> str:
    """Uses Gemini Vision to extract text from an image."""
    image_part = {"mime_type": "image/jpeg", "data": base64.b64encode(_image_bytes).decode('utf-8')}
    prompt = "Extract all text from this image. Only return the raw text content, with no additional commentary or formatting."
    try:
        response = vision_model.generate_content([prompt, image_part])
        return response.text.strip()
    except Exception as e:
        st.error(f"Gemini Vision OCR failed: {e}")
        return ""

def preprocess_pil(img: Image.Image) -> Image.Image:
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img

# -------------------------------------------------
# Extraction
# -------------------------------------------------
def extract_text_from_pdf(uploaded_file) -> str:
    # First, try standard text extraction
    try:
        uploaded_file.seek(0)
        pdf = PyPDF2.PdfReader(uploaded_file)
        txt = "\n".join((p.extract_text() or "") for p in pdf.pages).strip()
        if len(txt) > 20:
            return txt
    except Exception as e:
        st.warning(f"Standard PDF text extraction failed, trying visual OCR: {e}")

    # Fallback to Gemini Vision OCR for scanned PDFs
    try:
        uploaded_file.seek(0)
        import pdf2image
        images = pdf2image.convert_from_bytes(uploaded_file.read(), dpi=200) # 200 dpi is a good balance
        out = []
        bar = st.progress(0.0, "Visually analyzing PDF pages...")
        for i, im in enumerate(images, 1):
            im = preprocess_pil(im)
            buf = io.BytesIO()
            im.save(buf, format="JPEG")
            page_bytes = buf.getvalue()
            text = extract_text_with_gemini_vision(page_bytes)
            if text:
                out.append(text)
            bar.progress(i/len(images))
        bar.empty()
        return "\n\n--- Page Break ---\n\n".join(out).strip()
    except Exception as e:
        st.error(f"Visual PDF processing failed. Ensure 'poppler' is installed. Error: {e}")
        return ""


def extract_text_from_docx(f):
    try:
        return "\n".join(p.text for p in docx.Document(f).paragraphs).strip()
    except Exception as e:
        st.error(f"DOCX read error: {e}")
        return ""

def extract_text(file):
    if not file: return ""
    ext = file.name.lower().split(".")[-1]
    if ext == "pdf":
        return extract_text_from_pdf(file)
    elif ext == "docx":
        return extract_text_from_docx(file)
    elif ext in ("jpg", "jpeg", "png"):
        # Use Gemini Vision directly for images
        return extract_text_with_gemini_vision(file.getvalue())
    elif ext == "txt":
        return file.read().decode("utf-8", errors="ignore")
    else:
        st.error("Unsupported file type")
        return ""

# -------------------------------------------------
# Examples
# -------------------------------------------------
EXAMPLE_DOC_Q = {
    "Agriculture": {
        "English": ["What disease is this?", "How do I treat this crop issue?", "When should I harvest?"],
        "हिंदी": ["यह कौन-सी बीमारी है?", "इस फसल समस्या का इलाज कैसे करें?", "कटाई कब करनी चाहिए?"],
        "తెలుగు": ["ఇది ఏ వ్యాధి?", "ఈ పంట సమస్యను ఎలా పరిష్కరించాలి?", "పంటను ఎప్పుడు కోయాలి?"],
        "മലയാളം": ["ഇത് ഏത് രോഗമാണ്?", "ഈ വിള പ്രശ്നം എങ്ങനെ പരിഹരിക്കാം?", "എപ്പോൾ കൊയ്ത്ത് നടത്തണം?"],
    },
}
EXAMPLE_GEN_Q = {
    "Agriculture": {
        "English": ["Tomato leaves are yellow—cause?", "How to identify pest damage?", "Best time to plant corn?"],
        "हिंदी": ["टमाटर के पत्ते पीले—कारण?", "कीट नुकसान कैसे पहचानें?", "मक्का बोने का सही समय?"],
        "తెలుగు": ["టమోటా ఆకులు పసుపు—కారణం?", "కీటకాల నష్టం ఎలా గుర్తించాలి?", "మొక్కజొన్న ఎప్పుడు నాటాలి?"],
        "മലയാളം": ["തക്കാളി ഇലകൾ മഞ്ഞ—കാരണം?", "കീടനാശം എങ്ങനെ തിരിച്ചറിയാം?", "മക്ക ചോളം വിതയ്ക്കാൻ മികച്ച സമയം?"],
    },
}

# -------------------------------------------------
# Language Selection
# -------------------------------------------------
def show_language_selection():
    st.markdown(f"<h1 style='text-align:center;'>{get_text('select_language')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; font-size:18px; margin-bottom:24px;'>{get_text('choose_language')}</p>", unsafe_allow_html=True)
    st.markdown("<hr class='hr-soft'/>", unsafe_allow_html=True)

    cols = st.columns(4)
    lang_map = list(LANGUAGES.items())

    for i, col in enumerate(cols):
        with col:
            lang_name, lang_emoji = lang_map[i]
            if st.button(f"{lang_emoji} {lang_name}", use_container_width=True):
                st.session_state.selected_language = lang_name
                st.session_state.language_selected = True
                st.rerun()

# -------------------------------------------------
# Main App
# -------------------------------------------------
def show_main_app():
    st.title(f"🌾 CropCare{get_text('enhanced_title_suffix')}")

    lang = st.session_state.selected_language
    st.info(get_text("info_agri").format(lang_flag=LANGUAGES[lang], lang=lang))

    with st.sidebar:
        st.subheader(get_text("settings"))
        if st.button(get_text("change_lang_sector"), use_container_width=True):
            # Reset state to go back to language selection
            for k in list(st.session_state.keys()):
                if k in DEFAULT_STATE: st.session_state[k] = DEFAULT_STATE[k]
            st.rerun()

        st.markdown("---")
        st.caption(f"{get_text('current')}: {lang} → {sector_label('Agriculture')}")
        st.markdown(f"### {get_text('enhanced_features_title')}")
        st.markdown(f"- {get_text('features_agri_1')}")
        st.markdown(f"- {get_text('features_agri_2')}")
        st.markdown(f"- {get_text('features_agri_3')}")

    tab_doc, tab_gen = st.tabs([
        get_text("tab_doc").format(sector=sector_label('Agriculture')),
        get_text("tab_gen").format(sector=sector_label('Agriculture'))
    ])

    with tab_doc:
        st.header(get_text("tab_doc").format(sector=sector_label('Agriculture')))
        up = st.file_uploader(get_text("uploader_any"), type=["pdf", "docx", "txt", "jpg", "jpeg", "png"])

        if up:
            file_extension = up.name.lower().split(".")[-1]
            is_image = file_extension in ("jpg", "jpeg", "png")

            if is_image:
                st.subheader(get_text("image_analysis_header"))
                st.image(up, caption=get_text("uploaded_image_caption").format(sector=sector_label('Agriculture')), use_column_width=True)
                with st.spinner(get_text("analyzing_image")):
                    st.session_state.summary = ask_ai(mode="summary", image_bytes=up.getvalue())
                with st.spinner(get_text("extracting_image_text")):
                    st.session_state.doc_text = extract_text(up) # This will use Gemini Vision
            else: # Document
                with st.spinner(get_text("extracting")):
                    text = extract_text(up)
                if text:
                    st.session_state.doc_text = text
                    with st.spinner(get_text("generating")):
                        st.session_state.summary = ask_ai(document_text=text, mode="summary")
                else:
                    st.warning(get_text("no_text"))

        if st.session_state.summary:
            st.subheader(get_text("enhanced_analysis_header").format(sector=sector_label('Agriculture')))
            st.write(st.session_state.summary)
            tts_speak_toggle(st.session_state.summary, st.session_state.selected_language)
            st.divider()

            st.subheader(get_text("chat_about_analysis"))
            for m in st.session_state.chat_history:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

            try_examples = EXAMPLE_DOC_Q["Agriculture"].get(st.session_state.selected_language, [])
            st.caption(f"{get_text('examples_try')} {' • '.join(try_examples)}")

            q = st.chat_input(get_text("chat_placeholder"))
            if q:
                st.session_state.chat_history.append({"role": "user", "content": q})
                with st.spinner(get_text("thinking")):
                    ans = ask_ai(query=q, mode="chat")
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
                st.rerun()

    with tab_gen:
        st.header(get_text("gen_help_header").format(sector=sector_label('Agriculture')))
        st.caption(get_text("gen_help_caption").format(sector_lower=sector_label('Agriculture').lower()))
        for m in st.session_state.general_messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        try_examples2 = EXAMPLE_GEN_Q["Agriculture"].get(st.session_state.selected_language, [])
        st.caption(f"{get_text('examples_caption')} {' • '.join(try_examples2)}")

        q2 = st.chat_input(get_text("gen_chat_placeholder").format(sector_lower=sector_label('Agriculture').lower()))
        if q2:
            st.session_state.general_messages.append({"role": "user", "content": q2})
            with st.spinner(get_text("thinking")):
                ans2 = ask_ai(query=q2, mode="general")
            st.session_state.general_messages.append({"role": "assistant", "content": ans2})
            st.rerun()

    # Disclaimer
    st.markdown(f"---\n**{get_text('disclaimer_block_header')}**\n{get_text('disclaimer_agri')}\n\n{get_text('disclaimer_footer')}")

# -------------------------------------------------
# Main
# -------------------------------------------------
def main():
    if not st.session_state.language_selected:
        show_language_selection()
    else:
        st.session_state.selected_sector = "Agriculture"
        st.session_state.sector_selected = True
        show_main_app()

if __name__ == "__main__":
    main()