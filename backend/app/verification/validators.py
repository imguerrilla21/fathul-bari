from app.verification.state_machine import can_transition

def validate_state_transition(current_state: str, new_state: str):
    if not can_transition(current_state, new_state):
        raise ValueError(f"Invalid state transition from {current_state} to {new_state}")
    return True
