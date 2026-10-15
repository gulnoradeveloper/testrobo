import { Alert } from "./ui/alert";

export function MedicalDisclaimer({ className }: { className?: string }) {
  return (
    <Alert variant="warning" title="Tibbiy ogohlantirish" className={className}>
      Bo‘g‘imTahlil — ilmiy-tadqiqot prototipi. Sun’iy intellekt bahosi shifokor tashxisi emas va davolashni belgilash uchun
      asos bo‘lmaydi. Klinik qaror faqat malakali mutaxassis tomonidan qabul qilinadi.
    </Alert>
  );
}
