import { AlertTriangle } from "lucide-react";

export function BacktestDisclaimer() {
  return (
    <div
      role="note"
      className="border-amber-500/40 bg-amber-500/5 text-amber-700 dark:text-amber-400 mb-4 flex gap-3 rounded-md border p-3 text-xs leading-6"
    >
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <div>
        <strong className="font-bold">هشدار مهم:</strong>{" "}
        نتایج بک‌تست بر اساس دیتای تاریخی <b>بایننس</b> است و ممکن است با
        شرایط واقعی <b>والکس</b> (کارمزد، اسپرد، نقدینگی، تومان) متفاوت باشد.
        این نتایج تضمین آینده نیست.
      </div>
    </div>
  );
}
