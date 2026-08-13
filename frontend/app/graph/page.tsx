"use client";

import { useState, useEffect, useRef, useMemo, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Network,
  ShieldCheck,
  Search,
  BookOpen,
  FileText,
  Bot,
  Layers,
  Sparkles,
  ExternalLink,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Filter,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Clock,
  Compass,
  RotateCcw,
  GitCommit,
  UserCheck,
  Hash,
  Activity,
  Share2,
} from "lucide-react";
import {
  getGraphStats,
  getHadithSubgraph,
  getSharhSubgraph,
  getNodeNeighbors,
  findGraphPath,
  searchGraphNodes,
  triggerGraphBuild,
} from "@/lib/api";
import { useToast } from "@/components/Toast";

interface GraphNodeItem {
  id: string;
  node_type: string;
  entity_id?: string | null;
  label: string;
  metadata?: any;
}

interface GraphEdgeItem {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relation_type: string;
  confidence: number;
  verified: boolean;
  evidence_id?: string | null;
  metadata?: any;
}

interface GraphData {
  root_node_id?: string;
  nodes: GraphNodeItem[];
  edges: GraphEdgeItem[];
}

const NODE_COLORS: Record<string, { bg: string; border: string; text: string; glow: string }> = {
  hadith: { bg: "#064e3b", border: "#10b981", text: "#a7f3d0", glow: "rgba(16, 185, 129, 0.4)" },
  sharh_section: { bg: "#451a03", border: "#f59e0b", text: "#fef3c7", glow: "rgba(245, 158, 11, 0.4)" },
  source_page: { bg: "#082f49", border: "#38bdf8", text: "#e0f2fe", glow: "rgba(56, 189, 248, 0.4)" },
  book: { bg: "#31104b", border: "#c084fc", text: "#f3e8ff", glow: "rgba(192, 132, 252, 0.4)" },
  topic: { bg: "#4c0519", border: "#fb7185", text: "#ffe4e6", glow: "rgba(251, 113, 133, 0.4)" },
  person: { bg: "#134e4a", border: "#2dd4bf", text: "#ccfbf1", glow: "rgba(45, 212, 191, 0.4)" },
  collection: { bg: "#3f2c06", border: "#eab308", text: "#fef08a", glow: "rgba(234, 179, 8, 0.4)" },
};

function KnowledgeGraphContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialHadith = searchParams.get("hadith") ? parseInt(searchParams.get("hadith")!) : 1;

  const { showToast } = useToast();
  const [selectedHadithNum, setSelectedHadithNum] = useState<number>(initialHadith);
  const [verifiedOnly, setVerifiedOnly] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"visualizer" | "pathfinder" | "stats">("visualizer");

  // Graph Data & Selection
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNodeItem | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [stats, setStats] = useState<any | null>(null);

  // Path Finder State
  const [allNodesList, setAllNodesList] = useState<GraphNodeItem[]>([]);
  const [pathSourceId, setPathSourceId] = useState<string>("");
  const [pathTargetId, setPathTargetId] = useState<string>("");
  const [pathResult, setPathResult] = useState<any | null>(null);
  const [findingPath, setFindingPath] = useState<boolean>(false);

  // Visualizer Zoom & Pan
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // 1. Fetch Stats & Subgraph for current Hadith
  const loadGraph = async (hNum: number, vOnly: boolean) => {
    setLoading(true);
    try {
      const [subgraphRes, statsRes] = await Promise.all([
        getHadithSubgraph(hNum, vOnly),
        getGraphStats(),
      ]);
      setGraphData(subgraphRes);
      setStats(statsRes);

      // Auto select root node (Hadith)
      if (subgraphRes.nodes && subgraphRes.nodes.length > 0) {
        const root = subgraphRes.nodes.find((n: GraphNodeItem) => n.id === subgraphRes.root_node_id);
        setSelectedNode(root || subgraphRes.nodes[0]);
      }
    } catch (err: any) {
      showToast(`Gagal memuat Knowledge Graph: ${err.message}`, "error");
    } finally {
      setLoading(false);
    }
  };

  // 2. Fetch list of all nodes for path finder dropdown
  const loadAllNodes = async () => {
    try {
      const res = await searchGraphNodes("", undefined, 100);
      setAllNodesList(res.nodes || []);
      if (res.nodes && res.nodes.length >= 2) {
        setPathSourceId(res.nodes[0].id);
        setPathTargetId(res.nodes[1].id);
      }
    } catch (err) {
      console.error("Gagal memuat daftar simpul:", err);
    }
  };

  useEffect(() => {
    loadGraph(selectedHadithNum, verifiedOnly);
    loadAllNodes();
  }, [selectedHadithNum, verifiedOnly]);

  const handlePathFind = async () => {
    if (!pathSourceId || !pathTargetId) {
      showToast("Pilih simpul asal dan simpul tujuan.", "warning");
      return;
    }
    setFindingPath(true);
    try {
      const res = await findGraphPath(pathSourceId, pathTargetId, verifiedOnly);
      setPathResult(res);
      if (!res.path_found) {
        showToast("Tidak ditemukan jalur relasi langsung antara kedua simpul ini.", "info");
      }
    } catch (err: any) {
      showToast(`Gagal mencari jalur: ${err.message}`, "error");
    } finally {
      setFindingPath(false);
    }
  };

  const handleRebuildGraph = async () => {
    try {
      showToast("Membangun ulang Knowledge Graph...", "info");
      const res = await triggerGraphBuild();
      showToast(res.message || "Knowledge Graph berhasil diperbarui!", "success");
      loadGraph(selectedHadithNum, verifiedOnly);
    } catch (err: any) {
      showToast(`Gagal: ${err.message}`, "error");
    }
  };

  // Node Layout Positions (Physics Layout Simulator on Canvas/SVG)
  const nodePositions = useMemo(() => {
    const pos: Record<string, { x: number; y: number }> = {};
    const width = 640;
    const height = 480;
    const centerX = width / 2;
    const centerY = height / 2;

    const rootId = graphData.root_node_id;
    const nodes = graphData.nodes;

    if (!nodes || nodes.length === 0) return pos;

    // Place Root Node in center
    if (rootId) {
      pos[rootId] = { x: centerX, y: centerY };
    }

    // Categorize outer nodes by type for organized concentric placement
    const outerNodes = nodes.filter((n) => n.id !== rootId);
    const n = outerNodes.length;

    outerNodes.forEach((node, i) => {
      let radius = 175;
      if (node.node_type === "source_page") radius = 225;
      if (node.node_type === "topic") radius = 150;
      if (node.node_type === "book" || node.node_type === "collection") radius = 185;

      const angle = (i / n) * 2 * Math.PI - Math.PI / 2;
      pos[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    });

    return pos;
  }, [graphData]);

  // Mouse pan handlers for SVG canvas
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => setIsDragging(false);

  const quickHadiths = [
    { num: 1, label: "#1 Niat & Amal", desc: "Hadis Niat" },
    { num: 2, label: "#2 Salsalah", desc: "Lonceng Wahyu" },
    { num: 3, label: "#3 Gua Hira", desc: "Ru'ya Shadiqah" },
    { num: 4, label: "#4 Tilaawah", desc: "Jibril & Al-Qur'an" },
    { num: 10, label: "#10 Lisan & Tangan", desc: "Muslim Sejati" },
    { num: 59, label: "#59 Ilmu Syar'i", desc: "Pengangkatan Ilmu" },
    { num: 1513, label: "#1513 Thawaf", desc: "Haji & Hajar Aswad" },
    { num: 1891, label: "#1891 I'tikaf", desc: "Lailatul Qadar" },
  ];

  // Connected edges for selected node
  const connectedEdges = useMemo(() => {
    if (!selectedNode) return [];
    return graphData.edges.filter(
      (e) => e.source_node_id === selectedNode.id || e.target_node_id === selectedNode.id
    );
  }, [selectedNode, graphData]);

  return (
    <div className="min-h-screen bg-[#071912] text-[#ecfdf5] pb-24 animate-fade-in">
      
      {/* Header Banner */}
      <div className="border-b border-[#133e30] bg-gradient-to-r from-[#0b281f] via-[#082018] to-[#0b281f] py-8 px-4 sm:px-6 lg:px-8 shadow-xl">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="px-3 py-1 text-xs font-bold uppercase tracking-wider rounded-full bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/40">
                Tahap 9 — Knowledge Graph & GraphRAG
              </span>
              <span className="flex items-center gap-1.5 text-xs text-[#6ee7b7]">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Relational Provenance & Multi-Hop Traversal
              </span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white flex items-center gap-3">
              <Network className="w-9 h-9 text-[#f59e0b]" />
              Fathul Bari Knowledge Graph
            </h1>
            <p className="mt-2 text-sm text-[#a7f3d0]/80 max-w-2xl">
              Lapisan relasional ontologi islami yang menghubungkan hadis Shahih Bukhari, bab/kitab, syarah Ibnu Hajar, halaman naskah fisik, dan topik fiqih berdasar data terverifikasi.
            </p>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center gap-2 bg-[#0b221a] p-1.5 rounded-2xl border border-[#1a4a39] shadow-inner">
            <button
              onClick={() => setActiveTab("visualizer")}
              className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                activeTab === "visualizer"
                  ? "bg-[#10b981] text-[#071912] shadow-md shadow-[#10b981]/25"
                  : "text-[#a7f3d0] hover:bg-[#133e30]"
              }`}
            >
              <Compass className="w-4 h-4" />
              Graph Visualizer
            </button>
            <button
              onClick={() => setActiveTab("pathfinder")}
              className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                activeTab === "pathfinder"
                  ? "bg-[#f59e0b] text-[#071912] shadow-md shadow-[#f59e0b]/25"
                  : "text-[#a7f3d0] hover:bg-[#133e30]"
              }`}
            >
              <GitCommit className="w-4 h-4" />
              Multi-Hop Path Finder
            </button>
            <button
              onClick={() => setActiveTab("stats")}
              className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                activeTab === "stats"
                  ? "bg-[#818cf8] text-[#071912] shadow-md shadow-[#818cf8]/25"
                  : "text-[#a7f3d0] hover:bg-[#133e30]"
              }`}
            >
              <Activity className="w-4 h-4" />
              Statistik Ontologi
            </button>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 space-y-6">
        
        {/* TAB 1: Visualizer Canvas */}
        {activeTab === "visualizer" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Left Column: Canvas and Interactive Viewport */}
            <div className="lg:col-span-8 space-y-4">
              
              {/* Controls Bar */}
              <div className="bg-[#0b221a] border border-[#1a4a39] rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3 shadow-xl">
                
                {/* Verified vs Full Graph Toggle */}
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-[#a7f3d0]/80">Mode Graf:</span>
                  <div className="flex bg-[#071912] p-1 rounded-xl border border-[#1a4a39]">
                    <button
                      onClick={() => setVerifiedOnly(false)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        !verifiedOnly ? "bg-[#10b981] text-[#071912]" : "text-[#94a3b8] hover:text-white"
                      }`}
                    >
                      Full Graph (Kandidat & Verified)
                    </button>
                    <button
                      onClick={() => setVerifiedOnly(true)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
                        verifiedOnly ? "bg-emerald-500 text-[#071912]" : "text-[#94a3b8] hover:text-white"
                      }`}
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Verified Only (Strict)
                    </button>
                  </div>
                </div>

                {/* Canvas Zoom Controls */}
                <div className="flex items-center gap-2 bg-[#071912] px-3 py-1.5 rounded-xl border border-[#1a4a39] text-xs">
                  <button
                    onClick={() => setZoom((z) => Math.max(0.5, z - 0.15))}
                    className="p-1 text-[#a7f3d0] hover:text-white"
                    title="Zoom Out"
                  >
                    <ZoomOut className="w-4 h-4" />
                  </button>
                  <span className="font-mono text-xs text-[#f59e0b] w-12 text-center font-bold">
                    {(zoom * 100).toFixed(0)}%
                  </span>
                  <button
                    onClick={() => setZoom((z) => Math.min(2.5, z + 0.15))}
                    className="p-1 text-[#a7f3d0] hover:text-white"
                    title="Zoom In"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      setZoom(1);
                      setPan({ x: 0, y: 0 });
                    }}
                    className="p-1 text-[#a7f3d0] hover:text-white border-l border-[#1a4a39] pl-2"
                    title="Reset Posisi"
                  >
                    <Maximize2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Quick Hadith Selector Pills */}
              <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
                <span className="text-xs text-[#a7f3d0]/60 font-semibold shrink-0">Pilih Hadis Fokus:</span>
                {quickHadiths.map((qh) => (
                  <button
                    key={qh.num}
                    onClick={() => setSelectedHadithNum(qh.num)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 border ${
                      selectedHadithNum === qh.num
                        ? "bg-[#f59e0b] text-[#071912] border-[#f59e0b] shadow-lg shadow-[#f59e0b]/25"
                        : "bg-[#0b221a] hover:bg-[#133e30] text-[#a7f3d0] border-[#1a4a39]"
                    }`}
                  >
                    {qh.label}
                  </button>
                ))}
              </div>

              {/* SVG Interactive Canvas */}
              <div
                className="relative h-[520px] rounded-3xl bg-[#081d16] border border-[#1a4a39] overflow-hidden shadow-2xl cursor-grab active:cursor-grabbing select-none"
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
              >
                {loading ? (
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-xs text-[#a7f3d0] space-y-3 bg-[#081d16]/80 z-20">
                    <div className="w-10 h-10 border-3 border-[#10b981] border-t-transparent rounded-full animate-spin"></div>
                    <span>Mengonstruksi Knowledge Graph Subgraf Hadis #{selectedHadithNum}...</span>
                  </div>
                ) : (
                  <svg
                    className="w-full h-full"
                    viewBox="0 0 640 480"
                    preserveAspectRatio="xMidYMid meet"
                  >
                    <defs>
                      <marker
                        id="arrow-verified"
                        viewBox="0 0 10 10"
                        refX="22"
                        refY="5"
                        markerWidth="6"
                        markerHeight="6"
                        orient="auto-start-reverse"
                      >
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
                      </marker>
                      <marker
                        id="arrow-candidate"
                        viewBox="0 0 10 10"
                        refX="22"
                        refY="5"
                        markerWidth="6"
                        markerHeight="6"
                        orient="auto-start-reverse"
                      >
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="#f59e0b" />
                      </marker>
                    </defs>

                    <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
                      {/* 1. Draw Edges */}
                      {graphData.edges.map((edge) => {
                        const p1 = nodePositions[edge.source_node_id];
                        const p2 = nodePositions[edge.target_node_id];
                        if (!p1 || !p2) return null;

                        const isHighlighted =
                          selectedNode &&
                          (edge.source_node_id === selectedNode.id || edge.target_node_id === selectedNode.id);

                        return (
                          <g key={edge.id} className="transition-opacity duration-200">
                            <line
                              x1={p1.x}
                              y1={p1.y}
                              x2={p2.x}
                              y2={p2.y}
                              stroke={edge.verified ? "#10b981" : "#f59e0b"}
                              strokeWidth={isHighlighted ? 3 : edge.verified ? 1.8 : 1.2}
                              strokeDasharray={edge.verified ? "none" : "4,3"}
                              opacity={isHighlighted ? 1.0 : selectedNode ? 0.35 : 0.75}
                              markerEnd={edge.verified ? "url(#arrow-verified)" : "url(#arrow-candidate)"}
                            />
                            {/* Relation Type Label */}
                            <text
                              x={(p1.x + p2.x) / 2}
                              y={(p1.y + p2.y) / 2 - 4}
                              fill={edge.verified ? "#6ee7b7" : "#fde68a"}
                              fontSize="8"
                              fontFamily="monospace"
                              textAnchor="middle"
                              opacity={isHighlighted ? 1.0 : 0.6}
                              className="pointer-events-none select-none font-bold"
                            >
                              {edge.relation_type}
                            </text>
                          </g>
                        );
                      })}

                      {/* 2. Draw Nodes */}
                      {graphData.nodes.map((node) => {
                        const pos = nodePositions[node.id];
                        if (!pos) return null;

                        const isSelected = selectedNode?.id === node.id;
                        const isRoot = graphData.root_node_id === node.id;
                        const colors = NODE_COLORS[node.node_type] || NODE_COLORS.hadith;
                        const radius = isRoot ? 26 : 18;

                        return (
                          <g
                            key={node.id}
                            transform={`translate(${pos.x}, ${pos.y})`}
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedNode(node);
                            }}
                            className="cursor-pointer transition-transform duration-150 hover:scale-110"
                          >
                            {/* Glow circle if selected */}
                            {isSelected && (
                              <circle
                                r={radius + 8}
                                fill="none"
                                stroke={colors.border}
                                strokeWidth="2.5"
                                strokeDasharray="3,3"
                                className="animate-spin"
                                style={{ animationDuration: "6s" }}
                              />
                            )}

                            {/* Main Node Circle */}
                            <circle
                              r={radius}
                              fill={colors.bg}
                              stroke={isSelected ? "#ffffff" : colors.border}
                              strokeWidth={isSelected ? 3 : 2}
                              style={{
                                filter: isSelected ? `drop-shadow(0 0 12px ${colors.glow})` : "none",
                              }}
                            />

                            {/* Node Icon / Initial Letter */}
                            <text
                              textAnchor="middle"
                              dy="4"
                              fill="#ffffff"
                              fontSize={isRoot ? "11" : "9"}
                              fontWeight="bold"
                              fontFamily="sans-serif"
                              className="pointer-events-none"
                            >
                              {node.node_type === "hadith" ? "H" : node.node_type === "sharh_section" ? "§" : node.node_type === "source_page" ? "P" : node.node_type === "topic" ? "T" : node.node_type === "book" ? "B" : "•"}
                            </text>

                            {/* Node Label Below */}
                            <text
                              textAnchor="middle"
                              dy={radius + 13}
                              fill={colors.text}
                              fontSize="9.5"
                              fontWeight="bold"
                              fontFamily="sans-serif"
                              className="pointer-events-none select-none"
                              style={{ textShadow: "0 1px 3px rgba(0,0,0,0.8)" }}
                            >
                              {node.label.length > 24 ? node.label.slice(0, 22) + ".." : node.label}
                            </text>
                          </g>
                        );
                      })}
                    </g>
                  </svg>
                )}

                {/* Canvas Overlay Legends */}
                <div className="absolute bottom-3 left-3 bg-[#071912]/90 backdrop-blur-md p-3 rounded-2xl border border-[#1a4a39] text-[11px] space-y-1.5 z-10 shadow-xl">
                  <div className="font-bold text-white text-[10px] uppercase tracking-wider mb-1">
                    Legenda Entitas:
                  </div>
                  <div className="grid grid-cols-2 gap-x-3 gap-y-1">
                    <span className="flex items-center gap-1.5 text-emerald-400">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Hadis Bukhari
                    </span>
                    <span className="flex items-center gap-1.5 text-amber-400">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Seksi Fathul Bari
                    </span>
                    <span className="flex items-center gap-1.5 text-sky-400">
                      <span className="w-2.5 h-2.5 rounded-full bg-sky-500"></span> Halaman Naskah
                    </span>
                    <span className="flex items-center gap-1.5 text-rose-400">
                      <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Topik Fiqih/Kajian
                    </span>
                    <span className="flex items-center gap-1.5 text-purple-400">
                      <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span> Kitab / Bab
                    </span>
                    <span className="flex items-center gap-1.5 text-teal-400">
                      <span className="w-2.5 h-2.5 rounded-full bg-teal-500"></span> Tokoh / Author
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Node Inspector Sidebar */}
            <div className="lg:col-span-4 space-y-4">
              {selectedNode ? (
                <div className="bg-[#0b221a] border border-[#1a4a39] rounded-3xl p-6 shadow-2xl space-y-5">
                  
                  {/* Inspector Header */}
                  <div className="border-b border-[#1a4a39] pb-4">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-[#10b981]/20 text-[#10b981] border border-[#10b981]/40">
                        {selectedNode.node_type.replace("_", " ")}
                      </span>
                      <span className="font-mono text-[10px] text-[#94a3b8]">ID: {selectedNode.id.slice(0, 8)}..</span>
                    </div>
                    <h3 className="text-base font-extrabold text-white leading-snug">
                      {selectedNode.label}
                    </h3>
                  </div>

                  {/* Node Content / Text snippet */}
                  {selectedNode.metadata && (
                    <div className="space-y-2.5 text-xs">
                      {selectedNode.metadata.arabic_text && (
                        <div className="p-3.5 rounded-2xl bg-[#071912] border border-[#1a4a39]">
                          <div className="font-arabic text-lg leading-loose text-right text-[#fef3c7]" dir="rtl">
                            {selectedNode.metadata.arabic_text}
                          </div>
                        </div>
                      )}

                      {selectedNode.metadata.translation && (
                        <div className="p-3 rounded-xl bg-[#071912] border border-[#1a4a39] text-[#ecfdf5]/90 leading-relaxed">
                          {selectedNode.metadata.translation}
                        </div>
                      )}

                      {selectedNode.metadata.volume && (
                        <div className="flex justify-between py-1.5 border-b border-[#133e30]">
                          <span className="text-[#a7f3d0]/70">Volume & Halaman:</span>
                          <span className="font-semibold text-[#f59e0b]">
                            Jilid {selectedNode.metadata.volume} (Hal. {selectedNode.metadata.printed_page})
                          </span>
                        </div>
                      )}

                      {selectedNode.metadata.role && (
                        <div className="flex justify-between py-1.5 border-b border-[#133e30]">
                          <span className="text-[#a7f3d0]/70">Peran:</span>
                          <span className="font-semibold text-[#ecfdf5]">{selectedNode.metadata.role}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Connected Edges Breakdown */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-[#a7f3d0] flex items-center justify-between">
                      <span>Relasi Terhubung ({connectedEdges.length})</span>
                      <span className="text-[10px] text-emerald-400 font-mono">
                        {connectedEdges.filter((e) => e.verified).length} Verified
                      </span>
                    </h4>

                    <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1">
                      {connectedEdges.map((e) => {
                        const isOutgoing = e.source_node_id === selectedNode.id;
                        const otherNodeId = isOutgoing ? e.target_node_id : e.source_node_id;
                        const otherNode = graphData.nodes.find((n) => n.id === otherNodeId);

                        return (
                          <div
                            key={e.id}
                            className="p-2.5 rounded-xl bg-[#071912] border border-[#1a4a39] text-xs flex items-center justify-between gap-2"
                          >
                            <div className="space-y-0.5 truncate">
                              <div className="flex items-center gap-1.5 font-mono text-[10px]">
                                <span className={isOutgoing ? "text-[#f59e0b]" : "text-[#38bdf8]"}>
                                  {isOutgoing ? "➔ OUT:" : "⬅ IN:"}
                                </span>
                                <span className="font-bold text-white">{e.relation_type}</span>
                              </div>
                              <div className="text-[11px] text-[#a7f3d0] truncate">
                                {otherNode?.label || "Node"}
                              </div>
                            </div>

                            <span
                              className={`px-2 py-0.5 rounded text-[9px] font-bold shrink-0 uppercase border ${
                                e.verified
                                  ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                                  : "bg-amber-500/20 text-amber-300 border-amber-500/30"
                              }`}
                            >
                              {e.verified ? "✓ Verified" : "Candidate"}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Fast Action Buttons */}
                  <div className="pt-2 flex flex-col gap-2">
                    {selectedNode.node_type === "hadith" && (
                      <Link
                        href={`/hadith/${selectedHadithNum}`}
                        className="w-full py-2.5 px-4 rounded-xl bg-[#10b981]/20 hover:bg-[#10b981]/30 text-[#a7f3d0] font-bold text-xs flex items-center justify-center gap-2 transition-colors border border-[#10b981]/30"
                      >
                        <BookOpen className="w-4 h-4" />
                        Buka Hadis di Pembaca
                      </Link>
                    )}

                    <Link
                      href="/source"
                      className="w-full py-2.5 px-4 rounded-xl bg-[#f59e0b]/20 hover:bg-[#f59e0b]/30 text-[#f59e0b] font-bold text-xs flex items-center justify-center gap-2 transition-colors border border-[#f59e0b]/30"
                    >
                      <FileText className="w-4 h-4" />
                      Inspeksi Lembar Naskah (Source)
                    </Link>

                    <Link
                      href={`/ai?q=${encodeURIComponent(selectedNode.label)}`}
                      className="w-full py-2.5 px-4 rounded-xl bg-[#133e30] hover:bg-[#1a4a39] text-white font-bold text-xs flex items-center justify-center gap-2 transition-colors"
                    >
                      <Bot className="w-4 h-4 text-[#f59e0b]" />
                      Tanya Asisten AI (GraphRAG)
                    </Link>
                  </div>

                </div>
              ) : (
                <div className="p-12 text-center rounded-3xl bg-[#0b221a] border border-[#1a4a39] text-xs text-[#a7f3d0]/60 space-y-2">
                  <Network className="w-10 h-10 mx-auto text-[#2a6a53]" />
                  <p>Klik salah satu lingkaran simpul di kanvas graf untuk melihat inspeksi metadata dan relasinya.</p>
                </div>
              )}
            </div>

          </div>
        )}

        {/* TAB 2: Multi-Hop Path Finder */}
        {activeTab === "pathfinder" && (
          <div className="bg-[#0b221a] border border-[#1a4a39] rounded-3xl p-8 shadow-2xl space-y-6">
            <div className="border-b border-[#1a4a39] pb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <GitCommit className="w-6 h-6 text-[#f59e0b]" />
                Multi-Hop Path Finder (Eksplorasi Jalur Ontologi)
              </h2>
              <p className="text-xs text-[#a7f3d0]/70 mt-1">
                Menemukan rantai relasi terpendek antara dua hadis, seksi syarah, bab kitab, atau topik kajian fiqih menggunakan algoritma pencarian jalur graf berarah.
              </p>
            </div>

            {/* Selector Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-[#a7f3d0] mb-2">Simpul Asal (Source Entity):</label>
                <select
                  value={pathSourceId}
                  onChange={(e) => setPathSourceId(e.target.value)}
                  className="w-full bg-[#071912] border border-[#1a4a39] rounded-2xl p-3 text-xs text-white focus:outline-none focus:border-[#10b981]"
                >
                  {allNodesList.map((n) => (
                    <option key={n.id} value={n.id}>
                      [{n.node_type.toUpperCase()}] {n.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#a7f3d0] mb-2">Simpul Tujuan (Target Entity):</label>
                <select
                  value={pathTargetId}
                  onChange={(e) => setPathTargetId(e.target.value)}
                  className="w-full bg-[#071912] border border-[#1a4a39] rounded-2xl p-3 text-xs text-white focus:outline-none focus:border-[#10b981]"
                >
                  {allNodesList.map((n) => (
                    <option key={n.id} value={n.id}>
                      [{n.node_type.toUpperCase()}] {n.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handlePathFind}
                disabled={findingPath}
                className="px-6 py-3 rounded-2xl bg-gradient-to-r from-[#f59e0b] to-[#d97706] hover:from-[#d97706] hover:to-[#b45309] text-[#071912] font-extrabold text-xs flex items-center gap-2 shadow-lg shadow-[#f59e0b]/20 transition-all disabled:opacity-50"
              >
                <Search className="w-4 h-4" />
                <span>{findingPath ? "Mencari Jalur Graf..." : "Temukan Rantai Hubungan"}</span>
              </button>
            </div>

            {/* Path Result Display */}
            {pathResult && pathResult.path_found && (
              <div className="p-6 rounded-2xl bg-[#071912] border border-[#10b981]/40 space-y-4">
                <div className="flex items-center justify-between text-xs border-b border-[#1a4a39] pb-3">
                  <span className="font-bold text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    Jalur Ditemukan ({pathResult.hops} Hop Relasi)
                  </span>
                  <span className="font-mono text-[#94a3b8]">{pathResult.path_nodes.length} Simpul Terhubung</span>
                </div>

                {/* Step by step path visualizer */}
                <div className="flex flex-col sm:flex-row items-center gap-3 overflow-x-auto py-3">
                  {pathResult.path_nodes.map((node: GraphNodeItem, idx: number) => {
                    const edge = pathResult.path_edges[idx];
                    return (
                      <div key={node.id} className="flex items-center gap-3 shrink-0">
                        <div className="p-4 rounded-2xl bg-[#0b221a] border border-[#10b981]/60 text-center min-w-[170px] shadow-lg">
                          <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-[#10b981]/20 text-[#6ee7b7]">
                            {node.node_type}
                          </span>
                          <div className="font-bold text-xs text-white mt-1.5 line-clamp-2">
                            {node.label}
                          </div>
                        </div>

                        {edge && (
                          <div className="flex flex-col items-center shrink-0">
                            <span className="font-mono text-[9px] text-[#f59e0b] font-bold">
                              {edge.relation_type}
                            </span>
                            <ArrowRight className="w-5 h-5 text-[#f59e0b]" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: Ontology Statistics */}
        {activeTab === "stats" && stats && (
          <div className="space-y-6">
            
            {/* Top Scoreboard */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39]">
                <div className="text-xs font-bold text-[#94a3b8] uppercase mb-1">Total Simpul (Nodes)</div>
                <div className="text-3xl font-extrabold text-[#ecfdf5]">{stats.total_nodes}</div>
                <div className="text-xs text-[#a7f3d0]/70 mt-1">7 Kategori Entitas</div>
              </div>

              <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39]">
                <div className="text-xs font-bold text-[#94a3b8] uppercase mb-1">Total Relasi (Edges)</div>
                <div className="text-3xl font-extrabold text-emerald-400">{stats.total_edges}</div>
                <div className="text-xs text-[#a7f3d0]/70 mt-1">8 Tipe Hubungan</div>
              </div>

              <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39]">
                <div className="text-xs font-bold text-[#94a3b8] uppercase mb-1">Rasio Verifikasi</div>
                <div className="text-3xl font-extrabold text-[#f59e0b]">{stats.verified_percentage}%</div>
                <div className="text-xs text-emerald-300 font-bold mt-1">{stats.verified_edges} Verified Edges</div>
              </div>

              <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39]">
                <div className="text-xs font-bold text-[#94a3b8] uppercase mb-1">Kandidat Review</div>
                <div className="text-3xl font-extrabold text-amber-400">{stats.candidate_edges}</div>
                <div className="text-xs text-[#94a3b8] mt-1">Pending Kurasi Reviewer</div>
              </div>
            </div>

            {/* Breakdown Tables */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39] shadow-xl space-y-4">
                <h3 className="text-sm font-bold text-white border-b border-[#1a4a39] pb-3">
                  Distribusi Simpul (Node Types)
                </h3>
                <div className="divide-y divide-[#133e30]">
                  {Object.entries(stats.node_types).map(([tName, count]: any) => (
                    <div key={tName} className="py-2.5 flex justify-between items-center text-xs">
                      <span className="font-semibold text-[#a7f3d0] capitalize">{tName.replace("_", " ")}</span>
                      <span className="font-mono font-bold text-white bg-[#071912] px-2.5 py-0.5 rounded-lg border border-[#133e30]">
                        {count} simpul
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-6 rounded-3xl bg-[#0b221a] border border-[#1a4a39] shadow-xl space-y-4">
                <h3 className="text-sm font-bold text-white border-b border-[#1a4a39] pb-3">
                  Distribusi Relasi (Relation Types)
                </h3>
                <div className="divide-y divide-[#133e30]">
                  {Object.entries(stats.relation_types).map(([rName, count]: any) => (
                    <div key={rName} className="py-2.5 flex justify-between items-center text-xs">
                      <span className="font-mono font-semibold text-[#f59e0b]">{rName}</span>
                      <span className="font-mono font-bold text-white bg-[#071912] px-2.5 py-0.5 rounded-lg border border-[#133e30]">
                        {count} relasi
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={handleRebuildGraph}
                className="px-5 py-3 rounded-2xl bg-[#133e30] hover:bg-[#1a4a39] text-[#a7f3d0] font-bold text-xs flex items-center gap-2 transition-colors border border-[#2a6a53]"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Bangun Ulang Knowledge Graph dari Database</span>
              </button>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}

export default function KnowledgeGraphPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#071912] p-12 text-center text-[#a7f3d0]">
          Memuat Knowledge Graph Fathul Bari & Bukhari...
        </div>
      }
    >
      <KnowledgeGraphContent />
    </Suspense>
  );
}
