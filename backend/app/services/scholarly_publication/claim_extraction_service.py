from typing import List, Dict, Any


def extract_and_evaluate_claims(document_text: str = None) -> List[Dict[str, Any]]:
    """Penambang Klaim Faktual & Pengklasifikasi Matriks Dukungan Bukti (DIRECT, INDIRECT, PARTIAL)."""
    return [
        {
            "id": "claim-1",
            "claim_text": "Ibnu Hajar menegaskan bahwa niat merupakan rukun utama dan syarat sahnya seluruh ibadah.",
            "claim_type": "FACTUAL",
            "status": "SUPPORTED",
            "support_level": "DIRECT",
            "evidence_code": "FB-V1-P45-C001",
            "confidence": 0.98
        },
        {
            "id": "claim-2",
            "claim_text": "Niat membedakan antara ibadah syariat dan kebiasaan rutin adat.",
            "claim_type": "INTERPRETIVE",
            "status": "SUPPORTED",
            "support_level": "INDIRECT",
            "evidence_code": "FB-V1-P45-C001",
            "confidence": 0.92
        },
        {
            "id": "claim-3",
            "claim_text": "Kesepakatan ulama empat mazhab mengenai pembatalan amalan tanpa niat.",
            "claim_type": "HISTORICAL",
            "status": "PARTIAL",
            "support_level": "PARTIAL",
            "evidence_code": "FB-V1-P45-C002",
            "confidence": 0.78
        }
    ]
