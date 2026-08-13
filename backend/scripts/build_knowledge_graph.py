import logging
import sys

from app.database import SessionLocal
from app.services.graph_builder import build_knowledge_graph
from app.services.graph_service import get_graph_stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_knowledge_graph_script")


def main():
    print("=" * 80)
    print("  MEMBANGUN KNOWLEDGE GRAPH SHAHIH BUKHARI & SYARAH FATHUL BARI (TAHAP 9)")
    print("=" * 80)

    db = SessionLocal()
    try:
        results = build_knowledge_graph(db)
        print(f"[✓] Berhasil membuat {results['nodes_created']} Nodes.")
        print(f"[✓] Berhasil membuat {results['edges_created']} Edges ({results['verified_edges']} Verified, {results['candidate_edges']} Candidates).")
        
        stats = get_graph_stats(db)
        print("\n" + "-" * 80)
        print("  DISTRIBUSI SIMPUL (NODE TYPES):")
        for n_type, count in stats["node_types"].items():
            print(f"  • {n_type:<16}: {count} node")

        print("\n  DISTRIBUSI RELASI (RELATION TYPES):")
        for r_type, count in stats["relation_types"].items():
            print(f"  • {r_type:<18}: {count} edge")

        print("=" * 80)
        print("  KNOWLEDGE GRAPH SIAP DIGUNAKAN UNTUK VISUALISASI & GRAPHRAG")
        print("=" * 80)
    except Exception as err:
        logger.exception("Gagal membangun knowledge graph: %s", err)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
