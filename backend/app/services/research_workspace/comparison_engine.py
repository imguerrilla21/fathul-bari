from typing import Dict, Any, List


def compare_text_variants(text1: str, text2: str) -> Dict[str, Any]:
    """
    Mesin Penjelajah Komparasi Perbedaan Riwayat Hadis (Arabic Text Sequence Diff Engine):
    Membandingkan urutan kata antara riwayat Shahih Bukhari (#1) dan Shahih Muslim (#1907).
    """
    words1 = text1.split()
    words2 = text2.split()

    diff_tokens = []
    i = j = 0

    while i < len(words1) or j < len(words2):
        if i < len(words1) and j < len(words2) and words1[i] == words2[j]:
            diff_tokens.append({"word": words1[i], "status": "UNCHANGED"})
            i += 1
            j += 1
        elif i < len(words1) and (j >= len(words2) or words1[i] not in words2[j:j+3]):
            diff_tokens.append({"word": words1[i], "status": "REMOVED"})
            i += 1
        elif j < len(words2):
            diff_tokens.append({"word": words2[j], "status": "ADDED"})
            j += 1

    return {
        "text1": text1,
        "text2": text2,
        "total_words_text1": len(words1),
        "total_words_text2": len(words2),
        "diff_tokens": diff_tokens
    }
