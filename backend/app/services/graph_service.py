import json
import logging
import uuid
from collections import deque
from typing import Any
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.graph import GraphEdge, GraphNode
from app.utils.db_helpers import to_uuid

logger = logging.getLogger("graph_service")


def serialize_node(node: GraphNode) -> dict[str, Any]:
    """Mengubah objek GraphNode menjadi dictionary serializable."""
    meta = {}
    if node.metadata_json:
        try:
            meta = json.loads(node.metadata_json)
        except Exception:
            meta = {}

    return {
        "id": str(node.id),
        "node_type": node.node_type,
        "entity_id": node.entity_id,
        "label": node.label,
        "metadata": meta,
        "created_at": node.created_at.isoformat() if node.created_at else None,
    }


def serialize_edge(edge: GraphEdge) -> dict[str, Any]:
    """Mengubah objek GraphEdge menjadi dictionary serializable dengan provenance audit."""
    meta = {}
    if edge.metadata_json:
        try:
            meta = json.loads(edge.metadata_json)
        except Exception:
            meta = {}

    return {
        "id": str(edge.id),
        "source_node_id": str(edge.source_node_id),
        "target_node_id": str(edge.target_node_id),
        "relation_type": edge.relation_type,
        "confidence": edge.confidence,
        "verified": edge.verified,
        "evidence_id": edge.evidence_id,
        "metadata": meta,
        "created_at": edge.created_at.isoformat() if edge.created_at else None,
    }


def get_graph_stats(db: Session) -> dict[str, Any]:
    """Mengambil rekapitulasi statistik Knowledge Graph."""
    total_nodes = db.scalar(select(func.count(GraphNode.id))) or 0
    total_edges = db.scalar(select(func.count(GraphEdge.id))) or 0
    verified_edges = db.scalar(select(func.count(GraphEdge.id)).where(GraphEdge.verified == True)) or 0

    # Distribusi tipe simpul
    type_counts = {}
    types = list(db.execute(select(GraphNode.node_type, func.count(GraphNode.id)).group_by(GraphNode.node_type)))
    for t_name, count in types:
        type_counts[t_name] = count

    # Distribusi tipe relasi
    rel_counts = {}
    relations = list(db.execute(select(GraphEdge.relation_type, func.count(GraphEdge.id)).group_by(GraphEdge.relation_type)))
    for r_name, count in relations:
        rel_counts[r_name] = count

    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "verified_edges": verified_edges,
        "candidate_edges": total_edges - verified_edges,
        "verified_percentage": round((verified_edges / total_edges * 100.0), 1) if total_edges > 0 else 0.0,
        "node_types": type_counts,
        "relation_types": rel_counts,
    }


def get_subgraph_for_hadith(db: Session, hadith_number: int, verified_only: bool = False) -> dict[str, Any]:
    """Mengambil subgraf lengkap untuk hadis tertentu (Syarah, Kitab, Topik, Halaman Naskah)."""
    # 1. Cari node Hadith
    h_node = db.scalar(
        select(GraphNode)
        .where(GraphNode.node_type == "hadith")
        .where(GraphNode.label.like(f"%#{hadith_number}"))
    )

    if not h_node:
        return {"nodes": [], "edges": [], "root_node_id": None}

    node_ids = {h_node.id}
    edges_found: list[GraphEdge] = []

    # 2. Ambil 1-hop outgoing dan incoming edges
    query_edges = select(GraphEdge).where(
        or_(GraphEdge.source_node_id == h_node.id, GraphEdge.target_node_id == h_node.id)
    )
    if verified_only:
        query_edges = query_edges.where(GraphEdge.verified == True)

    first_hop_edges = list(db.scalars(query_edges))
    for e in first_hop_edges:
        edges_found.append(e)
        node_ids.add(e.source_node_id)
        node_ids.add(e.target_node_id)

    # 3. Ambil 2-hop edges untuk SharhSection (misal Sharh -> SourcePage, Sharh -> Topic, Sharh -> NextSection)
    sharh_node_ids = set()
    for nid in node_ids:
        if nid != h_node.id:
            n = db.scalar(select(GraphNode).where(GraphNode.id == nid))
            if n and n.node_type == "sharh_section":
                sharh_node_ids.add(nid)

    if sharh_node_ids:
        q_hop2 = select(GraphEdge).where(GraphEdge.source_node_id.in_(sharh_node_ids))
        if verified_only:
            q_hop2 = q_hop2.where(GraphEdge.verified == True)

        second_hop_edges = list(db.scalars(q_hop2))
        for e in second_hop_edges:
            edges_found.append(e)
            node_ids.add(e.source_node_id)
            node_ids.add(e.target_node_id)

    # Ambil semua objek nodes
    nodes = list(db.scalars(select(GraphNode).where(GraphNode.id.in_(node_ids))))

    return {
        "root_node_id": str(h_node.id),
        "total_nodes": len(nodes),
        "total_edges": len(edges_found),
        "nodes": [serialize_node(n) for n in nodes],
        "edges": [serialize_edge(e) for e in edges_found],
    }


def get_subgraph_for_sharh(db: Session, sharh_id: str, verified_only: bool = False) -> dict[str, Any]:
    """Mengambil subgraf untuk seksi Fathul Bari tertentu."""
    uid = to_uuid(sharh_id)
    sec_node = db.scalar(
        select(GraphNode)
        .where(GraphNode.node_type == "sharh_section")
        .where(or_(GraphNode.entity_id == sharh_id, GraphNode.id == uid))
    )

    if not sec_node:
        return {"nodes": [], "edges": [], "root_node_id": None}

    node_ids = {sec_node.id}
    edges_found: list[GraphEdge] = []

    # 1-hop edges
    q_edges = select(GraphEdge).where(
        or_(GraphEdge.source_node_id == sec_node.id, GraphEdge.target_node_id == sec_node.id)
    )
    if verified_only:
        q_edges = q_edges.where(GraphEdge.verified == True)

    edges = list(db.scalars(q_edges))
    for e in edges:
        edges_found.append(e)
        node_ids.add(e.source_node_id)
        node_ids.add(e.target_node_id)

    nodes = list(db.scalars(select(GraphNode).where(GraphNode.id.in_(node_ids))))

    return {
        "root_node_id": str(sec_node.id),
        "total_nodes": len(nodes),
        "total_edges": len(edges_found),
        "nodes": [serialize_node(n) for n in nodes],
        "edges": [serialize_edge(e) for e in edges_found],
    }


def get_node_neighbors(db: Session, node_id: str, depth: int = 1, verified_only: bool = False) -> dict[str, Any]:
    """Melakukan traversal tetangga $k$-hop dari sebuah simpul."""
    uid = to_uuid(node_id)
    start_node = db.scalar(select(GraphNode).where(GraphNode.id == uid)) if uid else None
    if not start_node:
        return {"nodes": [], "edges": [], "root_node_id": None}

    visited_nodes = {start_node.id}
    visited_edges: dict[uuid.UUID, GraphEdge] = {}

    queue = deque([(start_node.id, 0)])

    while queue:
        curr_id, curr_depth = queue.popleft()
        if curr_depth >= depth:
            continue

        q_edges = select(GraphEdge).where(
            or_(GraphEdge.source_node_id == curr_id, GraphEdge.target_node_id == curr_id)
        )
        if verified_only:
            q_edges = q_edges.where(GraphEdge.verified == True)

        for edge in db.scalars(q_edges):
            visited_edges[edge.id] = edge
            neighbor_id = edge.target_node_id if edge.source_node_id == curr_id else edge.source_node_id
            if neighbor_id not in visited_nodes:
                visited_nodes.add(neighbor_id)
                queue.append((neighbor_id, curr_depth + 1))

    nodes = list(db.scalars(select(GraphNode).where(GraphNode.id.in_(visited_nodes))))

    return {
        "root_node_id": str(start_node.id),
        "depth": depth,
        "total_nodes": len(nodes),
        "total_edges": len(visited_edges),
        "nodes": [serialize_node(n) for n in nodes],
        "edges": [serialize_edge(e) for e in visited_edges.values()],
    }


def find_shortest_path(db: Session, source_id: str, target_id: str, verified_only: bool = False) -> dict[str, Any]:
    """Mencari jalur relasi (Multi-Hop Path) terpendek antara dua simpul menggunakan BFS."""
    src_uid = to_uuid(source_id)
    dst_uid = to_uuid(target_id)

    src_node = db.scalar(select(GraphNode).where(GraphNode.id == src_uid)) if src_uid else None
    dst_node = db.scalar(select(GraphNode).where(GraphNode.id == dst_uid)) if dst_uid else None

    if not src_node or not dst_node:
        return {"path_found": False, "hops": 0, "path_nodes": [], "path_edges": []}

    if src_node.id == dst_node.id:
        return {
            "path_found": True,
            "hops": 0,
            "path_nodes": [serialize_node(src_node)],
            "path_edges": [],
        }

    # BFS Traversal
    queue = deque([[src_node.id]])
    visited = {src_node.id}
    parent_edge: dict[tuple[uuid.UUID, uuid.UUID], GraphEdge] = {}

    found_path = None

    while queue:
        path = queue.popleft()
        curr = path[-1]

        if curr == dst_node.id:
            found_path = path
            break

        # Ambil edge
        q_edges = select(GraphEdge).where(
            or_(GraphEdge.source_node_id == curr, GraphEdge.target_node_id == curr)
        )
        if verified_only:
            q_edges = q_edges.where(GraphEdge.verified == True)

        for edge in db.scalars(q_edges):
            nxt = edge.target_node_id if edge.source_node_id == curr else edge.source_node_id
            if nxt not in visited:
                visited.add(nxt)
                parent_edge[(curr, nxt)] = edge
                parent_edge[(nxt, curr)] = edge
                queue.append(path + [nxt])

    if not found_path:
        return {"path_found": False, "hops": 0, "path_nodes": [], "path_edges": []}

    path_nodes = []
    path_edges = []

    for nid in found_path:
        n = db.scalar(select(GraphNode).where(GraphNode.id == nid))
        if n:
            path_nodes.append(serialize_node(n))

    for i in range(len(found_path) - 1):
        pair = (found_path[i], found_path[i + 1])
        edge = parent_edge.get(pair)
        if edge:
            path_edges.append(serialize_edge(edge))

    return {
        "path_found": True,
        "hops": len(found_path) - 1,
        "path_nodes": path_nodes,
        "path_edges": path_edges,
    }


def search_graph_nodes(db: Session, query: str, node_type: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Mencari simpul graf berdasarkan teks dan tipe entitas."""
    stmt = select(GraphNode)
    if node_type:
        stmt = stmt.where(GraphNode.node_type == node_type)

    clean_q = query.strip()
    if clean_q:
        stmt = stmt.where(
            or_(
                GraphNode.label.ilike(f"%{clean_q}%"),
                GraphNode.metadata_json.ilike(f"%{clean_q}%"),
            )
        )

    stmt = stmt.limit(limit)
    nodes = list(db.scalars(stmt))
    return [serialize_node(n) for n in nodes]
