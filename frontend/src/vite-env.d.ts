/// <reference types="vite/client" />

declare global {
  interface Window {
    setTheme?: (preferencia: "system" | "dark" | "light") => void;
    getThemePreference?: () => "system" | "dark" | "light";
  }

  interface BeforeInstallPromptEvent extends Event {
    prompt(): Promise<void>;
    readonly userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
  }

  interface WindowEventMap {
    beforeinstallprompt: BeforeInstallPromptEvent;
  }

  interface Navigator {
    readonly standalone?: boolean;
    readonly audioSession?: { type: string };
  }
}

export {};
