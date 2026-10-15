import { AxiosError, AxiosHeaders } from "axios";
import { MESSAGES, toApiError } from "@/lib/api";

function axiosErr(status?: number, data?: unknown) {
  const cfg = { headers: new AxiosHeaders() };
  return new AxiosError("x", "ERR", cfg, null, status === undefined ? undefined : { status, data, statusText: "", headers: {}, config: cfg });
}

describe("toApiError — o‘zbekcha xatolik xabarlari", () => {
  it("server javob bermasa", () => {
    expect(toApiError(axiosErr()).message).toBe("Server bilan bog‘lanib bo‘lmadi.");
  });
  it("model tayyor bo‘lmasa — TT dagi aniq matn", () => {
    const e = toApiError(axiosErr(503, { error: { code: "MODEL_NOT_READY", message: "Sun’iy intellekt modeli hali tayyor emas." } }));
    expect(e.message).toBe(MESSAGES.modelNotReady);
    expect(e.code).toBe("MODEL_NOT_READY");
  });
  it("server xabarini o‘zgartirmasdan ko‘rsatadi", () => {
    const e = toApiError(axiosErr(403, { error: { code: "FORBIDDEN", message: "Ushbu ma’lumotni ko‘rishga ruxsat yo‘q." } }));
    expect(e.message).toBe("Ushbu ma’lumotni ko‘rishga ruxsat yo‘q.");
  });
  it("proksi 502 — server bilan aloqa yo‘q", () => {
    expect(toApiError(axiosErr(502, "<html>")).message).toBe(MESSAGES.network);
  });
});
