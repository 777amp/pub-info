export interface ProviderInfo {
  id: string;
  name: string;
  browseUrl: string;
}

export interface Pricing {
  inputPerMillion?: number;
  outputPerMillion?: number;
  cacheReadPerMillion?: number;
  cacheWritePerMillion?: number;
  imagePerUnit?: number;
  inputDisplay: string;
  outputDisplay: string;
  display: string;
  hasTiers: boolean;
  variesByProvider: boolean;
}

export interface Model {
  provider: string;
  id: string;
  slug: string;
  name: string;
  ownedBy: string;
  type: string;
  description: string;
  contextWindow: number;
  maxTokens: number;
  released: number;
  knowledge: string;
  zdr: string;
  noTraining: string;
  tags: string[];
  inputMods: string[];
  outputMods: string[];
  pricing: Pricing;
  hidden: boolean;
}

export interface CatalogSnapshot {
  provider: ProviderInfo;
  source: "live" | "local";
  fetchedAt: number;
  models: Model[];
  types: string[];
  tags: string[];
  visibleCount: number;
  hiddenCount: number;
}

interface WailsAppBinding {
  ListProviders(): Promise<ProviderInfo[]>;
  GetCatalog(providerID: string): Promise<CatalogSnapshot>;
  RefreshCatalog(providerID: string): Promise<CatalogSnapshot>;
  HideModel(providerID: string, modelID: string): Promise<CatalogSnapshot>;
  UnhideModel(providerID: string, modelID: string): Promise<CatalogSnapshot>;
}

declare global {
  interface Window {
    go?: {
      main?: {
        App?: WailsAppBinding;
      };
    };
  }
}

function binding(): WailsAppBinding {
  const app = window.go?.main?.App;
  if (!app) {
    throw new Error("Wails backend bindings are not available. Launch via the Model Check desktop app or `wails dev`.");
  }
  return app;
}

export const api = {
  listProviders: () => binding().ListProviders(),
  getCatalog: (providerID: string) => binding().GetCatalog(providerID),
  refreshCatalog: (providerID: string) => binding().RefreshCatalog(providerID),
  hideModel: (providerID: string, modelID: string) => binding().HideModel(providerID, modelID),
  unhideModel: (providerID: string, modelID: string) => binding().UnhideModel(providerID, modelID),
};
