import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  return (
    <div className="container flex flex-col items-center gap-4 py-24 text-center">
      <p className="text-5xl font-bold text-primary">404</p>
      <p className="text-muted">So‘ralgan sahifa topilmadi.</p>
      <Button asChild variant="outline"><Link to="/">Bosh sahifaga qaytish</Link></Button>
    </div>
  );
}
