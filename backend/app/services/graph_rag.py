import json
import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.graph import GraphEdge, GraphNode
from app.services.graph_service import serialize_edge, serialize_node
from app.services.hybrid_search import hybrid_search

logger = logging.getLogger("graph_rag")


def expand_query_via_knowledge_graph(
    db: Session,
    query: str,
    retrieval_mode: str = "research",
    limit: int = 5,
) -> dict[str, Any]:
    """
    Eksekusi GraphRAG:
    1. Hybrid Search menemukan simpul bibit (seed chunks)
    2. Knowledge Graph melakukan ekspansi multi-hop (Syarah -> Naskah Asli -> Topik -> Bab)
    3. Menyusun graph-enriched evidence dengan rantai sitasi primer lengkap
    """
    # 1. Hybrid Search
    search_res = hybrid_search(
        db=db,
        query=query,
        retrieval_mode=retrieval_mode,
        limit=limit,
    )

    seed_results = search_res.get("results", [])
    if not seed_results:
        return {
            "query": query,
            "seed_count": 0,
            "expanded_nodes_count": 0,
            "graph_evidence": [],
            "subgraph": {"nodes": [], "edges": []},
        }

    # 2. Ambil entity_ids dari hasil pencarian
    node_ids = set()
    expanded_edges: list[GraphEdge] = []
    evidence_chain = []

    for r in seed_results:
        hadith_num = r.get("hadith_number")
        sharh_id = r.get("sharh_section_id")

        matched_graph_nodes = []
        if hadith_num:
            hn = db.scalar(
                select(GraphNode)
                .where(GraphNode.node_type == "hadith")
                .where(GraphNode.label.like(f"%#{hadith_num}"))
            )
            if hn:
                matched_graph_nodes.append(hn)

        if sharh_id:
            sn = db.scalar(
                select(GraphNode)
                .where(GraphNode.node_type == "sharh_section")
                .where(GraphNode.entity_id == sharh_id)
            )
            if sn:
                matched_graph_nodes.append(sn)

        for seed_node in matched_graph_nodes:
            node_ids.add(seed_node.id)

            # Traversal 1-hop & 2-hop
            q_e = select(GraphEdge).where(
                (GraphEdge.source_node_id == seed_node.id) | (GraphEdge.target_node_id == seed_node.id)
            )
            if retrieval_mode == "research":
                q_e = q_e.where(GraphEdge.verified == True)

            direct_edges = list(db.scalars(q_e))
            for e in direct_edges:
                expanded_edges.append(e)
                node_ids.add(e.source_node_id)
                node_ids.add(e.target_node_id)

                # Jika target adalah sharh, ambil sumber halaman fisiknya (LOCATED_IN)
                target_node = db.scalar(select(GraphNode).where(GraphNode.id == e.target_node_id))
                if target_node and target_node.node_type == "sharh_section":
                    q_hop2 = select(GraphEdge).where(
                        GraphEdge.source_node_id == target_node.id,
                        GraphEdge.relation_type == "LOCATED_IN"
                    )
                    for e2 in db.scalars(q_hop2):
                        expanded_edges.append(e2)
                        node_ids.add(e2.target_node_id)

        # Susun item evidence chain
        evidence_chain.append({
            "hadith_number": hadith_num,
            "sharh_title": r.get("sharh_title"),
            "volume": r.get("volume"),
            "page": r.get("printed_page"),
            "citation": r.get("citation_inline"),
            "snippet": r.get("snippet"),
            "verified": r.get("verified"),
            "relevance_percentage": r.get("relevance_percentage"),
        })

    # Ambil seluruh node objek
    all_nodes = list(db.scalars(select(GraphNode).where(GraphNode.id.in_(node_ids))))

    return {
        "query": query,
        "retrieval_mode": retrieval_mode,
        "seed_count": len(seed_results),
        "expanded_nodes_count": len(all_nodes),
        "expanded_edges_count": len(expanded_edges),
        "evidence_chain": evidence_chain,
        "subgraph": {
            "nodes": [serialize_node(n) for n in all_nodes],
            "edges": [serialize_edge(e) for e in expanded_edges],
        },
    }
