export interface ModelRef {
  name: string;
  version: string;
  architecture: string;
  checkpoint_sha256: string;
  training_status: string;
}

export interface Probability { grade: number; label: string; title: string; probability: number }

export interface Analysis {
  id: string;
  number: string;
  status: string;
  created_at: string;
  expires_at: string;
  model: ModelRef;
  prediction: { kl_grade: number; label: string; title: string; description: string; reference: string };
  probabilities: Probability[];
  timing: Record<string, number>;
  processing_time_ms: number;
  image: { image_id: string; width: number; height: number; url: string };
  heatmap: { available: boolean; heatmap_url: string | null; overlay_url: string | null; note: string; error?: string | null };
  report_url: string;
  disclaimer: string;
  probability_note: string;
  limitations: string[];
  specialist_advice: string;
}

export interface AnalysisListItem {
  id: string;
  number: string;
  created_at: string;
  expires_at: string;
  image_id: string;
  kl_grade: number;
  label: string;
  title: string;
  model_version: string;
  report_url: string;
}

export interface Health {
  status: string;
  version: string;
  database: string;
  model_loaded: boolean;
  model_trained: boolean;
  model_status_message: string;
  device: string;
}

export interface ClassMetrics { precision: number; recall: number; f1: number; support: number }

export interface EvalMetrics {
  n_samples: number;
  accuracy: number;
  balanced_accuracy: number;
  macro_precision: number;
  macro_recall: number;
  macro_f1: number;
  quadratic_weighted_kappa: number;
  per_class: Record<string, ClassMetrics>;
  confusion_matrix: number[][];
  early_grade_confusion?: {
    pairs: Record<string, { count: number; rate_of_true_class: number }>;
    error_rate_within_kl0_kl2: number;
  };
}

export interface ModelInfo {
  loaded: boolean;
  trained: boolean;
  status_code: string | null;
  status_message: string;
  name: string;
  architecture: string | null;
  version: string | null;
  checkpoint_sha256: string | null;
  preprocess: Record<string, unknown> | null;
  class_names: string[];
  class_titles: Record<string, string>;
  dataset: Record<string, unknown>;
  metrics: { test?: EvalMetrics; validation?: EvalMetrics; calibration_evaluated?: boolean };
  training: Record<string, unknown>;
  calibration_evaluated: boolean;
  limitations: string[];
}
