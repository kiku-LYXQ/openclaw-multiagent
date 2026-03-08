/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GAME_STATE_WS?: string;
  readonly VITE_CONTROL_API?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
