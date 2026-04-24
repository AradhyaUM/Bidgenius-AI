import fitz  # PyMuPDF
import os
import shutil

# ─────────────────────────────────────────────
# PORTABLE POPPLER PATH DETECTION
# Works on your laptop AND on any other machine
# ─────────────────────────────────────────────
def _find_poppler():
    """
    Try to find Poppler automatically:
    1. If POPPLER_PATH env var is set, use that.
    2. If pdftoppm / pdfinfo is on PATH (Linux / Railway), use None (pdf2image finds it).
    3. Fall back to common Windows install locations.
    Returns the path string or None.
    """
    # Env var override (set this in .env if needed)
    from_env = os.environ.get("POPPLER_PATH")
    if from_env and os.path.isdir(from_env):
        return from_env

    # Already on system PATH (Linux, Mac, Railway)
    if shutil.which("pdftoppm"):
        return None   # pdf2image will find it automatically

    # Common Windows install locations
    windows_candidates = [
        r"C:\Users\UDAY MENDULKAR\AppData\Local\Programs\Release-25.12.0-0\poppler-25.12.0\Library\bin",
        r"C:\Program Files\poppler\bin",
        r"C:\poppler\bin",
        r"C:\tools\poppler\bin",
    ]
    for path in windows_candidates:
        if os.path.isdir(path):
            return path

    print("⚠️ Poppler not found — OCR will be unavailable. "
          "Set POPPLER_PATH in your .env file.")
    return None

POPPLER_PATH = _find_poppler()


# ─────────────────────────────────────────────
# QUALITY CHECK
# ─────────────────────────────────────────────
def is_garbage(text):
    if not text or len(text.strip()) < 100:
        return True
    # If more than 15% of chars are replacement chars, it's junk
    junk_ratio = text.count("�") / max(len(text), 1)
    if junk_ratio > 0.15:
        return True
    # If there are almost no spaces (binary data leaked through)
    space_ratio = text.count(" ") / max(len(text), 1)
    if space_ratio < 0.02:
        return True
    return False


# ─────────────────────────────────────────────
# PYMUPDF EXTRACTION  (primary)
# ─────────────────────────────────────────────
def extract_text(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))   # "text" mode — clean extraction
        doc.close()

        full_text = "\n".join(pages)

        if is_garbage(full_text):
            print("⚠️ PyMuPDF output looks like garbage, trying OCR...")
            return extract_text_ocr(pdf_path)

        return full_text

    except Exception as e:
        print(f"❌ PyMuPDF error: {e}, falling back to OCR")
        return extract_text_ocr(pdf_path)


# ─────────────────────────────────────────────
# PDFMINER FALLBACK  (better for complex layouts)
# pip install pdfminer.six — free, no Poppler needed
# ─────────────────────────────────────────────
def extract_text_pdfminer(pdf_path):
    """
    pdfminer.six handles complex column layouts better than PyMuPDF.
    Use this as a second fallback before OCR.
    """
    try:
        from pdfminer.high_level import extract_text as pm_extract
        text = pm_extract(pdf_path)
        if not is_garbage(text):
            return text
        return None
    except ImportError:
        print("💡 Install pdfminer.six for better PDF handling: pip install pdfminer.six")
        return None
    except Exception as e:
        print(f"❌ pdfminer error: {e}")
        return None


# ─────────────────────────────────────────────
# OCR  (last resort — scanned PDFs)
# ─────────────────────────────────────────────
def extract_text_ocr(pdf_path):
    if POPPLER_PATH is None and not shutil.which("pdftoppm"):
        print("⛔ OCR skipped — Poppler not available")
        return ""

    try:
        from pdf2image import convert_from_path
        import pytesseract
        import cv2
        import numpy as np

        convert_kwargs = {"dpi": 200, "thread_count": 2}
        if POPPLER_PATH:
            convert_kwargs["poppler_path"] = POPPLER_PATH

        images = convert_from_path(pdf_path, **convert_kwargs)
        full_text = []

        for img in images:
            img_np = np.array(img)
            gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
            # Adaptive threshold works better than fixed threshold on varied docs
            thresh = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            text = pytesseract.image_to_string(
                thresh,
                lang="eng",          # removed hin — causes issues if hindi pack not installed
                config="--oem 3 --psm 6"
            )
            full_text.append(text)

        return "\n".join(full_text)

    except ImportError as e:
        print(f"⛔ OCR dependency missing: {e}")
        return ""
    except Exception as e:
        print(f"❌ OCR error: {e}")
        return ""


# ─────────────────────────────────────────────
# SMART EXTRACTION  — tries all methods
# ─────────────────────────────────────────────
def smart_extract(pdf_path):
    """
    Try methods in order: PyMuPDF → pdfminer → OCR.
    Returns the best result.
    """
    # Method 1: PyMuPDF
    text = None
    try:
        doc = fitz.open(pdf_path)
        pages = [page.get_text("text") for page in doc]
        doc.close()
        candidate = "\n".join(pages)
        if not is_garbage(candidate):
            text = candidate
    except Exception:
        pass

    # Method 2: pdfminer (better column layout handling)
    if not text:
        text = extract_text_pdfminer(pdf_path)

    # Method 3: OCR (scanned documents)
    if not text:
        print("⚠️ All text methods failed, attempting OCR...")
        text = extract_text_ocr(pdf_path)

    return text or ""