export interface SourceProvenance {
  type: string;
  endpoint?: string | null;
  retrieved_at?: string | null;
  synced_on_demand?: boolean;
}

export interface Hadith {
  id: string;
  kitab: string;
  nomor: number;
  arab: string;
  terjemah: string;
  content_hash?: string | null;
  source: SourceProvenance;
}

export interface SharhSection {
  id: string;
  work_slug: string;
  volume: number;
  pdf_page?: number | null;
  printed_page?: number | null;
  page: number;
  section_order?: number | null;
  title: string;
  arabic_text: string;
  normalized_text?: string | null;
  translation: string;
  source_file?: string | null;
  source_hash?: string | null;
  extraction_status?: string;
  created_at?: string;
}

export interface SharhSectionWithEvidence extends SharhSection {
  confidence?: number | null;
  match_method?: string | null;
  review_status?: string;
  verified?: boolean;
  notes?: string | null;
  evidence?: {
    number_score?: number;
    text_score?: number;
    context_score?: number;
    detected_numbers?: number[];
    quotes_found?: string[];
  } | null;
}

export interface HadithSharhResponse {
  kitab: string;
  nomor: number;
  has_hadith: boolean;
  sharh_sections: SharhSectionWithEvidence[];
  message?: string;
}

export interface CitationItem {
  type: "sharh" | "hadith";
  work?: string;
  collection?: string;
  volume?: number;
  page?: number;
  number?: number;
  title?: string;
  verified?: boolean;
  review_status?: string;
  confidence?: number;
  standard_citation?: string;
  related_hadith?: number;
  source?: string;
  endpoint?: string;
}

export interface AntiHallucinationAudit {
  passed: boolean;
  detected_hadiths?: number[];
  valid_retrieved_hadiths?: number[];
  unverified_hadiths?: number[];
  detected_pages?: number[];
  valid_retrieved_pages?: number[];
  unverified_pages?: number[];
  audit_summary?: string;
}

export interface AIResearchResponse {
  status: string;
  query: string;
  mode: string;
  provider: string;
  answer: string;
  citations: CitationItem[];
  retrieved_summary: {
    hadiths_count: number;
    sharh_sections_count: number;
    detected_hadith_number?: number | null;
  };
  anti_hallucination_audit: AntiHallucinationAudit;
}

export interface ResearchQuestion {
  title: string;
  prompt: string;
  hadith_number: number | null;
  tag: string;
}

export interface SuggestionCategory {
  category: string;
  icon: string;
  questions: ResearchQuestion[];
}

export interface AISuggestionsResponse {
  categories: SuggestionCategory[];
}

export interface AIStatusResponse {
  status: string;
  configured_provider: string;
  active_engine: string;
  gemini_configured: boolean;
  openai_configured: boolean;
  model_name: string;
  features: {
    anti_hallucination_guard: boolean;
    scholarly_turats_synthesis: boolean;
    multiformat_citations: boolean;
    knowledge_graph_linking: boolean;
  };
}

export interface ReviewQueueItem {
  link_id: string;
  hadith_id: string;
  hadith_number: number;
  collection_slug: string;
  collection_name: string;
  hadith_arabic_snippet: string;
  hadith_translation_snippet: string;
  sharh_id: string;
  sharh_title: string;
  sharh_volume: number;
  sharh_page: number;
  sharh_arabic_snippet: string;
  sharh_translation_snippet: string;
  confidence: number;
  confidence_percent: number;
  confidence_tier: "auto_candidate" | "review" | "weak_match" | "reject";
  match_method: string;
  review_status: "pending" | "verified" | "rejected";
  verified: boolean;
  evidence: {
    number_score?: number;
    text_score?: number;
    context_score?: number;
    detected_numbers?: number[];
    quotes_found?: string[];
  } | null;
  notes?: string | null;
  created_at: string;
}

export interface ReviewStats {
  total_links: number;
  pending_count: number;
  verified_count: number;
  rejected_count: number;
  auto_candidate_count: number;
  review_count: number;
  weak_match_count: number;
  avg_confidence: number;
  avg_confidence_percent: number;
}

export interface ReviewQueueResponse {
  total: number;
  stats: ReviewStats;
  queue: ReviewQueueItem[];
}

export interface CollectionSummary {
  id: string;
  slug: string;
  name: string;
  language: string;
  total_expected: number;
  total_stored: number;
  completion_percentage: number;
  first_hadith_number?: number | null;
  last_hadith_number?: number | null;
  missing_count: number;
}

export interface SyncRun {
  id: string;
  collection_slug: string;
  sync_mode: string;
  status: string;
  started_at: string;
  finished_at?: string | null;
  total_fetched: number;
  total_inserted: number;
  total_updated: number;
  total_failed: number;
  notes?: string | null;
}

export interface CitationFormats {
  standard: string;
  chicago: string;
  bibtex: string;
  markdown: string;
}
