import axios, { AxiosError } from "axios";
import type { Analysis, AnalysisListItem, Health, ModelInfo } from "./types";

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "",
  withCredentials: true, // anonim sessiya cookie’si
  timeout: 120_000,
});

export const MESSAGES = {
  network: "Server bilan bog‘lanib bo‘lmadi.",
  modelNotReady: "Sun’iy intellekt modeli hozircha tahlil qilish uchun tayyor emas.",
  unknown: "Tahlilni bajarishda xatolik yuz berdi.",
};

export class ApiError extends Error {
  constructor(public code: string, message: string, public status?: number) {
    super(message);
  }
}

interface ErrorBody { error?: { code?: string; message?: string; details?: { ui_message?: string } } }

/** Server javobini foydalanuvchiga tushunarli o‘zbekcha xabarga aylantiradi. */
export function toApiError(err: unknown): ApiError {
  if (err instanceof ApiError) return err;
  const ax = err as AxiosError<ErrorBody>;
  if (ax?.isAxiosError) {
    if (!ax.response) return new ApiError("NETWORK", MESSAGES.network);
    const body = ax.response.data?.error;
    if (body?.code === "MODEL_NOT_READY") return new ApiError(body.code, MESSAGES.modelNotReady, 503);
    if (body?.code && body.message) return new ApiError(body.code, body.message, ax.response.status);
    if (ax.response.status >= 502 && ax.response.status <= 504) return new ApiError("NETWORK", MESSAGES.network, ax.response.status);
    return new ApiError("UNKNOWN", MESSAGES.unknown, ax.response.status);
  }
  return new ApiError("UNKNOWN", MESSAGES.unknown);
}

async function call<T>(p: Promise<{ data: T }>): Promise<T> {
  try {
    return (await p).data;
  } catch (e) {
    throw toApiError(e);
  }
}

export const api = {
  health: () => call<Health>(http.get("/api/v1/health")),
  modelInfo: () => call<ModelInfo>(http.get("/api/v1/model/info")),
  analyze: (file: File, onUpload?: (percent: number) => void) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("projection_confirmed", "true");
    return call<Analysis>(
      http.post("/api/v1/analyses", fd, {
        onUploadProgress: (e) => e.total && onUpload?.(Math.round((e.loaded / e.total) * 100)),
      }),
    );
  },
  get: (id: string) => call<Analysis>(http.get(`/api/v1/analyses/${encodeURIComponent(id)}`)),
  list: (params: { grade?: number; sort?: string }) =>
    call<{ items: AnalysisListItem[]; total: number }>(http.get("/api/v1/analyses", { params })),
  remove: (id: string) => call<void>(http.delete(`/api/v1/analyses/${encodeURIComponent(id)}`)),
};

/** API nisbiy manzilini to‘liq manzilga aylantirish (VITE_API_URL berilgan bo‘lsa). */
export function apiUrl(path: string): string {
  return `${import.meta.env.VITE_API_URL ?? ""}${path}`;
}
