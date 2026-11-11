import base64
import io
import os

import streamlit as st
from groq import Groq
from PIL import Image

# ---------- Config ----------
# Model names change over time. Check https://console.groq.com/docs/models
# and override via env vars / Streamlit secrets if needed.
def get_setting(name, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


API_KEY = get_setting("GROQ_API_KEY")
VISION_MODEL = get_setting("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
TEXT_MODEL = get_setting("GROQ_TEXT_MODEL", "llama-3.3-70b-versatile")

LANGUAGES = {
    "English": "English",
    "Urdu (اردو)": "Urdu, written in Urdu (Nastaliq/Arabic) script",
    "Roman Urdu": "Roman Urdu (Urdu written using English/Latin letters)",
    "Hindi (हिन्दी)": "Hindi, written in Devanagari script",
    "Hinglish": "Hinglish (Hindi written in Latin letters mixed with English)",
    "Arabic (العربية)": "Arabic, written in Arabic script",
    "Pashto (پښتو)": "Pashto, written in Pashto script",
    "Punjabi (پنجابی)": "Punjabi, written in Shahmukhi script",
    "Spanish": "Spanish",
    "French": "French",
    "German": "German",
    "Turkish": "Turkish",
    "Chinese (中文)": "Simplified Chinese",
    "Japanese (日本語)": "Japanese",
}
RTL_LANGS = {"Urdu (اردو)", "Arabic (العربية)", "Pashto (پښتو)", "Punjabi (پنجابی)"}

TONES = ["Fun", "Professional", "Emotional", "Inspirational", "Funny / Witty",
         "Romantic", "Poetic", "Short & Catchy"]
PLATFORMS = ["Instagram", "Facebook", "TikTok", "LinkedIn", "X (Twitter)", "WhatsApp Status"]


# ---------- Helpers ----------
def image_to_data_url(file, max_side=1024):
    img = Image.open(file).convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}", img


def build_prompt(language_desc, tone, platform, count, hashtags, emojis, extra):
    rules = [
        f"Write {count} different caption(s) for {platform}.",
        f"Tone: {tone}.",
        f"Language: {language_desc}. Write ONLY in this language.",
        "Keep each caption short, natural and engaging.",
        "Number the captions 1, 2, 3...",
        "Do not add explanations or extra commentary.",
    ]
    rules.append("Include relevant emojis." if emojis else "Do not use emojis.")
    rules.append("Add 3-5 relevant hashtags at the end of each caption." if hashtags
                 else "Do not add hashtags.")
    if extra:
        rules.append(f"Extra context from the user: {extra}")
    return "\n".join(rules)


def generate(client, prompt, data_url=None, description=None):
    if data_url:
        model = VISION_MODEL
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url}},
        ]
    else:
        model = TEXT_MODEL
        content = f"{prompt}\n\nPicture description: {description}"

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": content}],
        temperature=0.9,
        max_tokens=800,
    )
    return resp.choices[0].message.content.strip()


# ---------- UI ----------
st.set_page_config(page_title="AI Caption Generator", page_icon="✨", layout="centered")
st.title("✨ AI Caption Generator")
st.caption("Upload a picture or describe it, and get captions in your language. Powered by Groq.")

if not API_KEY:
    st.error("GROQ_API_KEY is missing. Add it as an environment variable (Codespaces) "
             "or in Streamlit secrets (deployment).")
    st.stop()

client = Groq(api_key=API_KEY)

with st.sidebar:
    st.header("Settings")
    language = st.selectbox("Caption language", list(LANGUAGES.keys()))
    tone = st.selectbox("Tone", TONES)
    platform = st.selectbox("Platform", PLATFORMS)
    count = st.slider("Number of captions", 1, 5, 3)
    hashtags = st.checkbox("Add hashtags", value=True)
    emojis = st.checkbox("Add emojis", value=True)

tab_img, tab_txt = st.tabs(["📷 Upload picture", "📝 Describe picture"])

with tab_img:
    uploaded = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png", "webp"])
    extra = st.text_input("Optional extra details (place, mood, occasion...)")
    if uploaded:
        data_url, preview = image_to_data_url(uploaded)
        st.image(preview, use_container_width=True)
    if st.button("Generate from picture", type="primary", disabled=not uploaded):
        with st.spinner("Looking at your picture..."):
            try:
                prompt = build_prompt(LANGUAGES[language], tone, platform, count,
                                      hashtags, emojis, extra)
                st.session_state["result"] = generate(client, prompt, data_url=data_url)
            except Exception as e:
                st.session_state["result"] = None
                st.error(f"Something went wrong: {e}")

with tab_txt:
    description = st.text_area("Describe your picture", height=120,
                               placeholder="e.g. Me and my friends at the beach during sunset")
    if st.button("Generate from description", type="primary", disabled=not description.strip()):
        with st.spinner("Writing captions..."):
            try:
                prompt = build_prompt(LANGUAGES[language], tone, platform, count,
                                      hashtags, emojis, "")
                st.session_state["result"] = generate(client, prompt, description=description)
            except Exception as e:
                st.session_state["result"] = None
                st.error(f"Something went wrong: {e}")

result = st.session_state.get("result")
if result:
    st.subheader("Your captions")
    if language in RTL_LANGS:
        html = result.replace("\n", "<br>")
        st.markdown(f"<div dir='rtl' style='font-size:1.3rem;line-height:2'>{html}</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown(result)
    with st.expander("Copy all"):
        st.code(result, language=None)
