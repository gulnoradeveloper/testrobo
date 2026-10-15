import { MAX_BYTES, precheckFile } from "@/pages/AnalyzePage";

const f = (name: string, type: string, size: number) => {
  const file = new File([new Uint8Array(Math.min(size, 10))], name, { type });
  Object.defineProperty(file, "size", { value: size });
  return file;
};

describe("precheckFile", () => {
  it("PNG/JPEG qabul qilinadi", () => {
    expect(precheckFile(f("a.png", "image/png", 1000))).toBeNull();
    expect(precheckFile(f("a.JPEG", "image/jpeg", 1000))).toBeNull();
  });
  it("noto‘g‘ri format rad etiladi", () => {
    expect(precheckFile(f("a.dcm", "application/dicom", 1000))).toBe("Fayl formati qo‘llab-quvvatlanmaydi.");
    expect(precheckFile(f("a.png", "image/gif", 1000))).toBe("Fayl formati qo‘llab-quvvatlanmaydi.");
  });
  it("20 MB dan katta fayl rad etiladi", () => {
    expect(precheckFile(f("a.png", "image/png", MAX_BYTES + 1))).toBe("Fayl hajmi belgilangan chegaradan oshgan.");
  });
});
