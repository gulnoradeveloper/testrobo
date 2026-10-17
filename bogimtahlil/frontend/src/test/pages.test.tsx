import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { api } from "@/lib/api";
import HistoryPage, { DELETE_CONFIRM } from "@/pages/HistoryPage";
import ModelPage, { NA } from "@/pages/ModelPage";
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

const emptyExp = {
  dataset: { available: false, name: null },
  training: {
    resnet18: { title: "ResNet-18", available: false, history: [], validation: null, best_epoch: null, epochs_run: null, training_minutes: null, pretrained: null },
    efficientnet_b0: { title: "EfficientNet-B0", available: false, history: [], validation: null, best_epoch: null, epochs_run: null, training_minutes: null, pretrained: null },
  },
  comparison: { available: false },
  test: { available: false },
  class_names: ["KL0", "KL1", "KL2", "KL3", "KL4"],
};

const noModel: ModelInfo = {
  loaded: false, trained: false, status_code: "MODEL_NOT_FOUND",
  status_message: "Model hali o‘qitilmagan: artifacts/model.pt mavjud emas.", name: "Bo‘g‘imTahlil",
  architecture: null, version: null, checkpoint_sha256: null, preprocess: null,
  class_names: ["KL0", "KL1", "KL2", "KL3", "KL4"], class_titles: {}, dataset: {}, metrics: {}, training: {},
  calibration_evaluated: false, limitations: ["Cheklov matni"],
};

it("Model sahifasi: model yo‘q — sahifa ochiladi, “Natija mavjud emas”, soxta raqam yo‘q", async () => {
  vi.spyOn(api, "modelInfo").mockResolvedValue(noModel);
  vi.spyOn(api, "experiments").mockResolvedValue(emptyExp as never);
  render(<MemoryRouter><ModelPage /></MemoryRouter>);
  expect(await screen.findByText("Model hali o‘qitilmagan", { selector: "p" })).toBeInTheDocument();
  for (const t of ["Model pasporti", "Ma’lumotlar to‘plami", "O‘qitish jarayoni", "Model samaradorligi",
    "ResNet-18 va EfficientNet-B0 qiyosi", "Tasniflash xatoliklari jadvali", "Model cheklovlari"]) {
    expect(screen.getByText(t)).toBeInTheDocument();
  }
  expect(screen.getAllByText(NA).length).toBeGreaterThanOrEqual(10);
  expect(screen.queryByText(/\d+(\.\d+)?%/)).toBeNull();
  expect(screen.queryByText("Server bilan bog‘lanib bo‘lmadi.")).toBeNull();
});

it("Model sahifasi: server javob bermasa — alohida “server” xabari va qayta urinish", async () => {
  const { ApiError } = await import("@/lib/api");
  vi.spyOn(api, "modelInfo").mockRejectedValue(new ApiError("NETWORK", "Server bilan bog‘lanib bo‘lmadi."));
  vi.spyOn(api, "experiments").mockResolvedValue(emptyExp as never);
  render(<MemoryRouter><ModelPage /></MemoryRouter>);
  expect(await screen.findByText("Server bilan bog‘lanib bo‘lmadi.")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Qayta urinish/ })).toBeInTheDocument();
  expect(screen.queryByText("Model hali o‘qitilmagan")).toBeNull();
});

it("Model sahifasi: real tajriba fayllari bo‘lsa — qiymatlar ko‘rsatiladi", async () => {
  const m = { accuracy: 0.6123, balanced_accuracy: 0.55, macro_precision: 0.5, macro_recall: 0.5, macro_f1: 0.5432,
    quadratic_weighted_kappa: 0.8123, recall: { KL0: 0.9, KL1: 0.2, KL2: 0.5, KL3: 0.7, KL4: 0.8 },
    confusion_matrix: [[9, 1, 0, 0, 0], [3, 2, 0, 0, 0], [0, 1, 4, 0, 0], [0, 0, 1, 7, 0], [0, 0, 0, 1, 4]], n_samples: 33 };
  vi.spyOn(api, "modelInfo").mockResolvedValue({ ...noModel, loaded: true, trained: true, status_code: null,
    status_message: "Model yuklangan va tahlilga tayyor.", architecture: "EfficientNet-B0", version: "v1" });
  vi.spyOn(api, "experiments").mockResolvedValue({ ...emptyExp, test: { available: true, ...m },
    comparison: { available: true, selected: "efficientnet_b0", reason: "EfficientNet-B0 tanlandi", rule: "val macro F1" } } as never);
  render(<MemoryRouter><ModelPage /></MemoryRouter>);
  expect(await screen.findByText("61.2%")).toBeInTheDocument();
  expect(screen.getByText("0.543")).toBeInTheDocument();
  expect(screen.getByText("0.812")).toBeInTheDocument();
  expect(screen.getByText("Model ishlamoqda")).toBeInTheDocument();
});
