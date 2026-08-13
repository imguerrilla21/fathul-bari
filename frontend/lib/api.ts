import {
  AIResearchResponse,
  AISuggestionsResponse,
  AIStatusResponse,
  CitationFormats,
  CollectionSummary,
  Hadith,
  HadithSharhResponse,
  ReviewQueueItem,
  ReviewQueueResponse,
  SyncRun,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
      cache: "no-store",
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Request failed with status ${res.status}`);
    }

    return await res.json();
  } catch (err: any) {
    console.error(`API Error on [${endpoint}]:`, err);
    throw err;
  }
}

// -----------------------------------------------------------------------------
// Hadith Endpoints
// -----------------------------------------------------------------------------
export async function getHadith(kitab: string = "shahih_bukhari", nomor: number = 1): Promise<Hadith> {
  return fetchJson<Hadith>(`/api/v1/hadith/${kitab}/${nomor}?auto_sync=true`);
}

export async function searchHadiths(
  query: string,
  kitab: string = "shahih_bukhari",
  limit: number = 20,
  offset: number = 0
): Promise<{ query: string; total: number; limit: number; offset: number; results: Hadith[] }> {
  return fetchJson<{ query: string; total: number; limit: number; offset: number; results: Hadith[] }>(
    `/api/v1/hadith/search?q=${encodeURIComponent(query)}&kitab=${kitab}&limit=${limit}&offset=${offset}`
  );
}

// -----------------------------------------------------------------------------
// Tahap 8 Hybrid Search Engine Endpoints
// -----------------------------------------------------------------------------
export async function hybridSearch(
  query: string,
  mode: string = "research",
  volume?: number | null,
  limit: number = 10,
  verifiedOnly: boolean = false
): Promise<any> {
  return fetchJson<any>("/api/v1/search/hybrid", {
    method: "POST",
    body: JSON.stringify({
      query,
      mode,
      volume: volume || null,
      limit,
      verified_only: verifiedOnly,
    }),
  });
}

export async function getSearchEngineStats(): Promise<any> {
  return fetchJson<any>("/api/v1/search/stats");
}

export async function getRecentRetrievalLogs(limit: number = 20): Promise<any> {
  return fetchJson<any>(`/api/v1/search/logs?limit=${limit}`);
}

export async function runSearchEvaluation(): Promise<any> {
  return fetchJson<any>("/api/v1/search/evaluate", {
    method: "POST",
  });
}

export async function getCollectionsSummary(): Promise<CollectionSummary[]> {
  return fetchJson<CollectionSummary[]>("/api/v1/hadith/collections");
}

// -----------------------------------------------------------------------------
// Syarah Fathul Bari Endpoints
// -----------------------------------------------------------------------------
export async function getSharhByHadith(kitab: string = "shahih_bukhari", nomor: number = 1): Promise<HadithSharhResponse> {
  return fetchJson<HadithSharhResponse>(`/api/v1/sharh/hadith/${kitab}/${nomor}`);
}

// -----------------------------------------------------------------------------
// Syarah AI Assistant (RAG) Endpoints
// -----------------------------------------------------------------------------
export async function askAIAssistant(
  query: string,
  hadithNumber?: number | null,
  mode: string = "syarah_focus",
  kitab: string = "shahih_bukhari"
): Promise<AIResearchResponse> {
  return fetchJson<AIResearchResponse>("/api/v1/ai/ask", {
    method: "POST",
    body: JSON.stringify({
      query,
      hadith_number: hadithNumber,
      mode,
      kitab,
    }),
  });
}

export async function getAISuggestions(): Promise<AISuggestionsResponse> {
  return fetchJson<AISuggestionsResponse>("/api/v1/ai/suggestions");
}

export async function getAIStatus(): Promise<AIStatusResponse> {
  return fetchJson<AIStatusResponse>("/api/v1/ai/status");
}

export async function validateCitation(
  collectionSlug: string = "shahih_bukhari",
  hadithNumber?: number | null,
  volume?: number | null,
  page?: number | null
): Promise<{ is_valid: boolean; citations: CitationFormats; human_verified: boolean }> {
  return fetchJson<{ is_valid: boolean; citations: CitationFormats; human_verified: boolean }>(
    "/api/v1/ai/validate-citation",
    {
      method: "POST",
      body: JSON.stringify({
        collection_slug: collectionSlug,
        hadith_number: hadithNumber,
        volume,
        page,
      }),
    }
  );
}

// -----------------------------------------------------------------------------
// Review Dashboard (Tahap 5) Endpoints
// -----------------------------------------------------------------------------
export async function getReviewQueue(
  status: string = "pending",
  minConfidence: number = 0.0,
  volume?: string,
  search?: string
): Promise<ReviewQueueResponse> {
  let url = `/api/v1/review/queue?status=${status}&minimum_confidence=${minConfidence}&limit=100`;
  if (volume) url += `&volume=${volume}`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  return fetchJson<ReviewQueueResponse>(url);
}

export async function getReviewLinkDetail(linkId: string): Promise<{ link: ReviewQueueItem; citations: CitationFormats }> {
  return fetchJson<{ link: ReviewQueueItem; citations: CitationFormats }>(`/api/v1/review/links/${linkId}`);
}

export async function verifyReviewLink(
  linkId: string,
  notes?: string,
  reviewer?: string
): Promise<{ status: string; link_id: string; verified: boolean; audit_id?: string }> {
  const reqId = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : undefined;
  return fetchJson<{ status: string; link_id: string; verified: boolean; audit_id?: string }>(
    `/api/v1/review/links/${linkId}/verify`,
    {
      method: "POST",
      headers: {
        ...(reviewer ? { "X-Reviewer": reviewer } : {}),
        ...(reqId ? { "X-Request-ID": reqId } : {}),
      },
      body: JSON.stringify({
        notes: notes || "Diverifikasi oleh peneliti di Review Dashboard Next.js",
        reviewer: reviewer || "Reviewer Ahli",
      }),
    }
  );
}

export async function rejectReviewLink(
  linkId: string,
  notes?: string,
  reviewer?: string
): Promise<{ status: string; link_id: string; verified: boolean; audit_id?: string }> {
  const reqId = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : undefined;
  return fetchJson<{ status: string; link_id: string; verified: boolean; audit_id?: string }>(
    `/api/v1/review/links/${linkId}/reject`,
    {
      method: "POST",
      headers: {
        ...(reviewer ? { "X-Reviewer": reviewer } : {}),
        ...(reqId ? { "X-Request-ID": reqId } : {}),
      },
      body: JSON.stringify({
        notes: notes || "Ditolak oleh peneliti di Review Dashboard Next.js",
        reviewer: reviewer || "Reviewer Ahli",
      }),
    }
  );
}

// -----------------------------------------------------------------------------
// Tahap 6 Source Viewer & Audit Trail Endpoints
// -----------------------------------------------------------------------------
export async function getSourceSections(volume?: number | null, limit: number = 100): Promise<any> {
  const url = volume ? `/api/v1/source/sections?volume=${volume}&limit=${limit}` : `/api/v1/source/sections?limit=${limit}`;
  return fetchJson<any>(url);
}

export async function getSourceMetadata(sharhId: string): Promise<any> {
  return fetchJson<any>(`/api/v1/source/sharh/${sharhId}`);
}

export async function getSharhAuditTrail(sharhId: string): Promise<any> {
  return fetchJson<any>(`/api/v1/source/audit/sharh_section/${sharhId}`);
}

export async function getLinkAuditTrail(linkId: string): Promise<any> {
  return fetchJson<any>(`/api/v1/source/audit/link/${linkId}`);
}

export async function getRecentAudits(limit: number = 30): Promise<any> {
  return fetchJson<any>(`/api/v1/source/audit/recent?limit=${limit}`);
}

// -----------------------------------------------------------------------------
// Tahap 9 Knowledge Graph & GraphRAG Endpoints
// -----------------------------------------------------------------------------
export async function getGraphStats(): Promise<any> {
  return fetchJson<any>("/api/v1/graph/stats");
}

export async function getHadithSubgraph(hadithNumber: number, verifiedOnly: boolean = false): Promise<any> {
  return fetchJson<any>(`/api/v1/graph/hadith/${hadithNumber}?verified_only=${verifiedOnly}`);
}

export async function getSharhSubgraph(sharhId: string, verifiedOnly: boolean = false): Promise<any> {
  return fetchJson<any>(`/api/v1/graph/sharh/${sharhId}?verified_only=${verifiedOnly}`);
}

export async function getNodeNeighbors(nodeId: string, depth: number = 1, verifiedOnly: boolean = false): Promise<any> {
  return fetchJson<any>(`/api/v1/graph/node/${nodeId}/neighbors?depth=${depth}&verified_only=${verifiedOnly}`);
}

export async function findGraphPath(sourceId: string, targetId: string, verifiedOnly: boolean = false): Promise<any> {
  return fetchJson<any>(`/api/v1/graph/path?source_id=${sourceId}&target_id=${targetId}&verified_only=${verifiedOnly}`);
}

export async function searchGraphNodes(query: string = "", nodeType?: string, limit: number = 30): Promise<any> {
  const params = new URLSearchParams();
  if (query) params.append("q", query);
  if (nodeType) params.append("node_type", nodeType);
  params.append("limit", limit.toString());
  return fetchJson<any>(`/api/v1/graph/nodes?${params.toString()}`);
}

export async function triggerGraphBuild(): Promise<any> {
  return fetchJson<any>("/api/v1/graph/build", { method: "POST" });
}

export async function expandGraphRAG(query: string, mode: string = "research", limit: number = 5): Promise<any> {
  return fetchJson<any>("/api/v1/graph/rag-expand", {
    method: "POST",
    body: JSON.stringify({ query, mode, limit }),
  });
}

// -----------------------------------------------------------------------------
// Admin & Sync Endpoints
// -----------------------------------------------------------------------------
export async function getSyncRuns(): Promise<SyncRun[]> {
  return fetchJson<SyncRun[]>("/api/v1/admin/sync-runs?limit=20");
}

export async function triggerSync(
  start: number,
  end: number,
  mode: string = "range",
  collection: string = "shahih_bukhari"
): Promise<{ status: string; fetched: number; inserted: number; failed: number }> {
  return fetchJson<{ status: string; fetched: number; inserted: number; failed: number }>(
    `/api/v1/admin/sync?sync_mode=${mode}`,
    {
      method: "POST",
      body: JSON.stringify({
        collection_slug: collection,
        start,
        end,
      }),
    }
  );
}
