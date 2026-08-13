class VerificationState:
    AI_GENERATED = "AI_GENERATED"
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    REJECTED = "REJECTED"
    CORRECTED = "CORRECTED"
    DISPUTED = "DISPUTED"

ALLOWED_TRANSITIONS = {
    VerificationState.AI_GENERATED: [VerificationState.PENDING_REVIEW, VerificationState.VERIFIED, VerificationState.REJECTED],
    VerificationState.PENDING_REVIEW: [VerificationState.VERIFIED, VerificationState.PARTIALLY_VERIFIED, VerificationState.REJECTED, VerificationState.CORRECTED],
    VerificationState.VERIFIED: [VerificationState.DISPUTED],
    VerificationState.REJECTED: [VerificationState.CORRECTED, VerificationState.DISPUTED],
    VerificationState.CORRECTED: [VerificationState.PENDING_REVIEW, VerificationState.VERIFIED],
    VerificationState.DISPUTED: [VerificationState.VERIFIED, VerificationState.REJECTED]
}

def can_transition(current_state: str, new_state: str) -> bool:
    if current_state not in ALLOWED_TRANSITIONS:
        return False
    return new_state in ALLOWED_TRANSITIONS[current_state]
