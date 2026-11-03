import { onlineManager } from "@tanstack/react-query";
import { useSyncExternalStore } from "react";

export function useEnLinea(): boolean {
  return useSyncExternalStore(
    (avisar) => onlineManager.subscribe(avisar),
    () => onlineManager.isOnline(),
    () => true,
  );
}
