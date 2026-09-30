"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function SignalsIndex() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/signals/BTCTMN");
  }, [router]);
  return (
    <div className="flex h-96 items-center justify-center">
      <p className="text-sm text-muted-foreground">در حال انتقال...</p>
    </div>
  );
}
