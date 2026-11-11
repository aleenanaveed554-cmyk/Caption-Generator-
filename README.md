# AI Caption Generator

Upload a picture or describe it, pick a language and tone, get captions. Built with Streamlit + Groq.

## Run locally / in Codespaces
```bash
pip install -r requirements.txt
export GROQ_API_KEY="your_key_here"
streamlit run app.py
```

## Deploy
Streamlit Community Cloud -> New app -> select repo -> main file `app.py`
-> Advanced settings -> Secrets:
```
GROQ_API_KEY = "your_key_here"
```
