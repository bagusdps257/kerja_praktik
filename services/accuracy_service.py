import os
import difflib
import fitz


def _levenshtein_distance_with_counts(seq1, seq2):
    """
    Compute Levenshtein distance and count substitutions, deletions, and insertions
    using dynamic programming with backtracking.
    """
    m, n = len(seq1), len(seq2)
    
    # dp[i][j] = minimum edit distance between seq1[:i] and seq2[:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                cost_sub = dp[i - 1][j - 1] + 1
                cost_del = dp[i - 1][j] + 1
                cost_ins = dp[i][j - 1] + 1
                dp[i][j] = min(cost_sub, cost_del, cost_ins)

    # Backtracking to count exact S, D, I operations
    i, j = m, n
    subs, dels, inss = 0, 0, 0

    while i > 0 or j > 0:
        if i > 0 and j > 0 and seq1[i - 1] == seq2[j - 1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            subs += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            dels += 1
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            inss += 1
            j -= 1
        else:
            break

    return dp[m][n], subs, dels, inss


def calculate_cer_wer(reference_text: str, hypothesis_text: str) -> dict:
    """
    Calculate Character Error Rate (CER) and Word Error Rate (WER)
    comparing reference ground-truth text with hypothesis OCR text.
    """
    ref_chars = list(reference_text or "")
    hyp_chars = list(hypothesis_text or "")
    
    total_ref_chars = len(ref_chars)
    total_hyp_chars = len(hyp_chars)

    # Edge cases
    if total_ref_chars == 0 and total_hyp_chars == 0:
        return {
            "cer": 0.0,
            "character_accuracy": 100.0,
            "wer": 0.0,
            "word_accuracy": 100.0,
            "substitutions": 0,
            "deletions": 0,
            "insertions": 0,
            "total_reference_chars": 0,
            "total_hypothesis_chars": 0,
            "total_reference_words": 0,
            "total_hypothesis_words": 0,
            "word_substitutions": 0,
            "word_deletions": 0,
            "word_insertions": 0,
            "diff_tokens": []
        }

    if total_ref_chars == 0:
        return {
            "cer": 100.0,
            "character_accuracy": 0.0,
            "wer": 100.0,
            "word_accuracy": 0.0,
            "substitutions": 0,
            "deletions": 0,
            "insertions": total_hyp_chars,
            "total_reference_chars": 0,
            "total_hypothesis_chars": total_hyp_chars,
            "total_reference_words": 0,
            "total_hypothesis_words": len((hypothesis_text or "").split()),
            "word_substitutions": 0,
            "word_deletions": 0,
            "word_insertions": len((hypothesis_text or "").split()),
            "diff_tokens": [{"tag": "insert", "text": hypothesis_text}]
        }

    if total_hyp_chars == 0:
        return {
            "cer": 100.0,
            "character_accuracy": 0.0,
            "wer": 100.0,
            "word_accuracy": 0.0,
            "substitutions": 0,
            "deletions": total_ref_chars,
            "insertions": 0,
            "total_reference_chars": total_ref_chars,
            "total_hypothesis_chars": 0,
            "total_reference_words": len((reference_text or "").split()),
            "total_hypothesis_words": 0,
            "word_substitutions": 0,
            "word_deletions": len((reference_text or "").split()),
            "word_insertions": 0,
            "diff_tokens": [{"tag": "delete", "text": reference_text}]
        }

    # 1. Character Error Rate (CER)
    dist_char, subs_char, dels_char, inss_char = _levenshtein_distance_with_counts(ref_chars, hyp_chars)
    cer = (dist_char / total_ref_chars) * 100.0
    char_acc = max(0.0, 100.0 - cer)

    # 2. Word Error Rate (WER)
    ref_words = reference_text.split()
    hyp_words = hypothesis_text.split()
    total_ref_words = len(ref_words)
    total_hyp_words = len(hyp_words)

    if total_ref_words > 0:
        dist_word, subs_word, dels_word, inss_word = _levenshtein_distance_with_counts(ref_words, hyp_words)
        wer = (dist_word / total_ref_words) * 100.0
        word_acc = max(0.0, 100.0 - wer)
    else:
        wer = 0.0 if total_hyp_words == 0 else 100.0
        word_acc = 100.0 if total_hyp_words == 0 else 0.0
        subs_word, dels_word, inss_word = 0, 0, total_hyp_words

    # 3. Visual Diff Highlight tokens using difflib
    matcher = difflib.SequenceMatcher(None, ref_words, hyp_words)
    diff_tokens = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            diff_tokens.append({
                "tag": "equal",
                "text": " ".join(ref_words[i1:i2])
            })
        elif tag == "replace":
            diff_tokens.append({
                "tag": "replace",
                "ref": " ".join(ref_words[i1:i2]),
                "hyp": " ".join(hyp_words[j1:j2])
            })
        elif tag == "delete":
            diff_tokens.append({
                "tag": "delete",
                "text": " ".join(ref_words[i1:i2])
            })
        elif tag == "insert":
            diff_tokens.append({
                "tag": "insert",
                "text": " ".join(hyp_words[j1:j2])
            })

    return {
        "cer": round(cer, 2),
        "character_accuracy": round(char_acc, 2),
        "wer": round(wer, 2),
        "word_accuracy": round(word_acc, 2),
        "substitutions": subs_char,
        "deletions": dels_char,
        "insertions": inss_char,
        "total_reference_chars": total_ref_chars,
        "total_hypothesis_chars": total_hyp_chars,
        "total_reference_words": total_ref_words,
        "total_hypothesis_words": total_hyp_words,
        "word_substitutions": subs_word,
        "word_deletions": dels_word,
        "word_insertions": inss_word,
        "diff_tokens": diff_tokens
    }


def extract_pdf_text(filepath: str) -> dict:
    """
    Extract readable text from a Searchable PDF file per page.
    """
    if not os.path.exists(filepath):
        return {
            "success": False,
            "error": f"File '{filepath}' tidak ditemukan."
        }

    try:
        doc = fitz.open(filepath)
        page_count = len(doc)
        pages = []
        full_text_list = []

        for idx, page in enumerate(doc):
            text = page.get_text() or ""
            pages.append({
                "page_number": idx + 1,
                "text": text,
                "char_count": len(text),
                "word_count": len(text.split())
            })
            if text:
                full_text_list.append(text)

        doc.close()
        full_text = "\n\n".join(full_text_list).strip()

        return {
            "success": True,
            "page_count": page_count,
            "full_text": full_text,
            "char_count": len(full_text),
            "word_count": len(full_text.split()),
            "pages": pages
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Gagal mengekstrak teks PDF: {str(e)}"
        }
