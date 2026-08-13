import re
from typing import List, Dict, Any

TRANSMISSION_TERMS = ["حدثنا", "حدثني", "أخبرنا", "عن", "قال", "سمعت"]

def parse_isnad_chain(sanad_text: str) -> Dict[str, Any]:
    """
    Parses a Sanad text into an ordered list of nodes and transmission edges.
    """
    nodes = []
    edges = []
    
    # Very basic tokenization heuristic for the chain.
    # Split by transmission terms to extract names
    pattern = r"(" + "|".join(TRANSMISSION_TERMS) + r")"
    parts = re.split(pattern, sanad_text)
    
    current_term = None
    position = 1
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        if part in TRANSMISSION_TERMS:
            current_term = part
        else:
            # It's a name
            node_id = f"node_{position}"
            nodes.append({
                "id": node_id,
                "position": position,
                "surface_name": part,
                "role": "NARRATOR"
            })
            
            if position > 1:
                # Link previous node to this node
                edges.append({
                    "from_node_index": position - 1,
                    "to_node_index": position,
                    "transmission_term": current_term or "UNKNOWN",
                    "edge_type": "TEACHER_OF"
                })
            
            position += 1
            current_term = None
            
    return {
        "nodes": nodes,
        "edges": edges,
        "confidence": 0.8
    }
