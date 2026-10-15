import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { api } from "@/lib/api";
import HistoryPage, { DELETE_CONFIRM } from "@/pages/HistoryPage";
import ModelPage, { NOT_EVALUATED } from "@/pages/ModelPage";
import type { ModelInfo } from "@/lib/types";

class RO { observe() {} unobserve() {} disconnect() {} }
(globalThis as unknown as { ResizeObserver: typeof RO }).ResizeObserver = RO;

afterEach(() => vi.restoreAllMocks());

const item = {
  id: "11111111-2222-3333-4444-555555555555", number: "BT-20261015-111111", created_at: "2026-10-15T09:30:00Z",
  expires_at: "2026-10-16T09:30:00Z", image_id: "abcdef123456", kl_grade: 2, label: "KL2", title: "Yengil o‘zgarishlar",
  model_version: "v1", report_url: "/api/v1/analyses/x/report",
};

it("Tahlillar tarixi: o‘chirishdan oldin tasdiqlash so‘raladi va API chaqiriladi", async () => {
  vi.spyOn(api, "list").mockResolvedValue({ items: [item], total: 1 });
  const rm = vi.spyOn(api, "remove").mockResolvedValue(undefined);
  render(<MemoryRouter><HistoryPage /></MemoryRouter>);
  expect((await screen.findAllByText("BT-20261015-111111")).length).toBeGreaterThan(0);
  fireEvent.click(screen.getAllByRole("button", { name: /tahlilini o‘chirish/ })[0]);
  expect(await screen.findByText(DELETE_CONFIRM)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Bekor qilish" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "O‘chirish" }));
  await waitFor(() => expect(rm).toHaveBeenCalledWith(item.id));
  await waitFor(() => expect(screen.queryAllByText("BT-20261015-111111")).toHaveLength(0));
});

it("Model sahifasi: metrikalar yo‘q bo‘lsa “Hali baholanmagan” ko‘rsatiladi, soxta raqam emas", async () => {
  const info: ModelInfo = {
    loaded: false, trained: false, status_code: "MODEL_NOT_FOUND",
    status_message: "Sun’iy intellekt modeli hozircha tahlil qilish uchun tayyor emas.", name: "Bo‘g‘imTahlil",
    architecture: null, version: null, checkpoint_sha256: null, preprocess: null,
    class_names: ["KL0", "KL1", "KL2", "KL3", "KL4"], class_titles: {}, dataset: {}, metrics: {}, training: {},
    calibration_evaluated: false, limitations: ["x"],
  };
  vi.spyOn(api, "modelInfo").mockResolvedValue(info);
  render(<MemoryRouter><ModelPage /></MemoryRouter>);
  expect(await screen.findByText("Sun’iy intellekt modeli hozircha tahlil qilish uchun tayyor emas.")).toBeInTheDocument();
  expect(screen.getAllByText(NOT_EVALUATED).length).toBeGreaterThanOrEqual(5);
  expect(screen.queryByText(/%$/)).toBeNull();
});
