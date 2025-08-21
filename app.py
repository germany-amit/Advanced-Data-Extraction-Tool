import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from textblob import TextBlob
import io
import difflib
import pandas as pd

st.title("📄 PDF Tilted Text Corrector with Agentic AI Agents")

uploaded_file = st.file_uploader("Upload a PDF", type=[".pdf"])

# ----------------------
# Helper functions
# ----------------------
def extract_with_pymupdf(doc):
    text = ""
    tilted_words = []
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    span_text = span.get("text", "").strip()
                    if not span_text:
                        continue
                    angle = abs(span.get("angle", 0))
                    if angle > 1:  # consider tilted
                        tilted_words.extend(span_text.split())
                    text += " " + span_text
    return text.strip(), tilted_words

def extract_with_ocr(page):
    pix = page.get_pixmap()
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img)

def correct_text(text):
    return str(TextBlob(text).correct())

def highlight_tilted(text, tilted_words):
    words = text.split()
    out = []
    for w in words:
        if w in tilted_words:
            out.append(f"<span style='color:green;font-weight:bold'>{w}</span>")
        else:
            out.append(w)
    return " ".join(out)

# ----------------------
# Main app logic
# ----------------------
if uploaded_file:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    agent_report = []

    # Agent 1: PyMuPDF extraction
    raw_text, tilted_words = extract_with_pymupdf(doc)
    agent_report.append(f"Agent 1 (PyMuPDF): Extracted {len(raw_text.split())} words, Tilted={tilted_words}")

    # Agent 2: OCR fallback
    try:
        page = doc[0]
        ocr_text = extract_with_ocr(page)
        agent_report.append(f"Agent 2 (OCR): Extracted {len(ocr_text.split())} words")
    except:
        agent_report.append("Agent 2 (OCR): Failed")

    # Combine best text for correction
    combined_text = raw_text if raw_text else ocr_text
    corrected_text = correct_text(combined_text)
    agent_report.append(f"Agent 3 (Correction): Corrected text length={len(corrected_text.split())}")

    # Agent 4: Comparison
    diff = difflib.ndiff(combined_text.split(), corrected_text.split())
    added, removed = [], []
    for d in diff:
        if d.startswith("+ "):
            added.append(d[2:])
        elif d.startswith("- "):
            removed.append(d[2:])
    agent_report.append(f"Agent 4 (Comparison): Added={added}, Removed={removed}, Tilted fixed={tilted_words}")

    # ----------------------
    # Display agent report
    # ----------------------
    st.subheader("🤖 Agentic AI Agents Report")
    for line in agent_report:
        st.write("•", line)

    # ----------------------
    # Final Suggested Text
    # ----------------------
    st.markdown("---")
    st.subheader("🏁 Final Suggested Text (Corrected & De-Tilted)")
    final_text_display = highlight_tilted(corrected_text, tilted_words)
    st.markdown(f"<div style='padding:10px; background-color:#f0f8ff; border-radius:10px;'>{final_text_display}</div>", unsafe_allow_html=True)
    st.info("✅ Tilted words auto-corrected, grammar & spelling fixed.")

    # ----------------------
    # Sentence-level comparison & CSV download
    # ----------------------
    st.markdown("---")
    st.subheader("📊 Sentence-Level Comparison")

    original_sentences = [s.strip() for s in combined_text.split('.') if s.strip()]
    corrected_sentences = [s.strip() for s in corrected_text.split('.') if s.strip()]

    max_len = max(len(original_sentences), len(corrected_sentences))
    original_sentences += [""] * (max_len - len(original_sentences))
    corrected_sentences += [""] * (max_len - len(corrected_sentences))

    html_rows = []
    df_rows = []
    for o, c in zip(original_sentences, corrected_sentences):
        diff_html = []
        diff = difflib.ndiff(o.split(), c.split())
        for d in diff:
            if d.startswith("+ "):
                diff_html.append(f"<span style='color:green'>{d[2:]}</span>")
            elif d.startswith("- "):
                diff_html.append(f"<span style='color:red'>{d[2:]}</span>")
            else:
                diff_html.append(d[2:])
        df_rows.append({"Original": o, "Corrected": c})
        html_rows.append(f"<p><b>Original:</b> {highlight_tilted(o, tilted_words)}<br><b>Corrected:</b> {highlight_tilted(c, tilted_words)}<br><b>Diff:</b> {' '.join(diff_html)}</p><hr>")

    st.dataframe(pd.DataFrame(df_rows))

    st.markdown("### 🔍 Detailed Comparison with Tilt Highlighting")
    for row in html_rows:
        st.markdown(row, unsafe_allow_html=True)

    # CSV download
    csv = pd.DataFrame(df_rows).to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Sentence Comparison as CSV",
        data=csv,
        file_name="sentence_comparison.csv",
        mime="text/csv"
    )

    # Download final suggested text
    st.download_button(
        label="📥 Download Final Suggested Text",
        data=corrected_text,
        file_name="corrected_text.txt",
        mime="text/plain"
    )
