package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/777amp/pub-info/micro-apps/model-check/internal/catalog"
	"github.com/777amp/pub-info/micro-apps/model-check/internal/provider"
	"github.com/777amp/pub-info/micro-apps/model-check/internal/provider/vercel"
	"github.com/777amp/pub-info/micro-apps/model-check/internal/store"
)

// App is the thin Wails v2 binding adapter. All business logic lives in internal/.
type App struct {
	ctx     context.Context
	service *catalog.Service
}

func NewApp() *App {
	repoRoot := findRepoRoot()
	vercelModelsPath := ""
	hiddenPaths := map[string]string{}

	if repoRoot != "" {
		candidate := filepath.Join(repoRoot, "vercel", "model-updates", "models.json")
		if _, err := os.Stat(candidate); err == nil {
			vercelModelsPath = candidate
		}
		hiddenPaths[vercel.ProviderID] = filepath.Join(repoRoot, "vercel", "model-updates", "hidden_models.json")
	}

	fallbackDir := ""
	if cfgDir, err := os.UserConfigDir(); err == nil && cfgDir != "" {
		fallbackDir = filepath.Join(cfgDir, "model-check")
	}

	reg := provider.NewRegistry()
	_ = reg.Register(vercel.New(vercel.WithLocalSnapshot(vercelModelsPath)))

	hiddenStore := store.NewHiddenStore(hiddenPaths, fallbackDir)
	return &App{
		service: catalog.NewService(reg, hiddenStore),
	}
}

func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
}

// ListProviders returns all registered model providers (extensible).
func (a *App) ListProviders() []provider.ProviderInfo {
	return a.service.ListProviders()
}

// GetCatalog loads (or returns cached) models for the given provider.
func (a *App) GetCatalog(providerID string) (catalog.Snapshot, error) {
	providerID = strings.TrimSpace(providerID)
	if providerID == "" {
		return catalog.Snapshot{}, fmt.Errorf("provider ID is required")
	}
	return a.service.GetCatalog(a.requestCtx(), providerID, false, false)
}

// RefreshCatalog forces a fresh fetch from the provider's live API (with local fallback).
func (a *App) RefreshCatalog(providerID string) (catalog.Snapshot, error) {
	providerID = strings.TrimSpace(providerID)
	if providerID == "" {
		return catalog.Snapshot{}, fmt.Errorf("provider ID is required")
	}
	return a.service.GetCatalog(a.requestCtx(), providerID, true, false)
}

// HideModel persistently hides a model for the given provider.
func (a *App) HideModel(providerID, modelID string) (catalog.Snapshot, error) {
	return a.service.SetHidden(a.requestCtx(), strings.TrimSpace(providerID), strings.TrimSpace(modelID), true)
}

// UnhideModel persistently unhides a model for the given provider.
func (a *App) UnhideModel(providerID, modelID string) (catalog.Snapshot, error) {
	return a.service.SetHidden(a.requestCtx(), strings.TrimSpace(providerID), strings.TrimSpace(modelID), false)
}

func (a *App) requestCtx() context.Context {
	if a.ctx != nil {
		return a.ctx
	}
	return context.Background()
}

// findRepoRoot walks up from the current working directory (and executable path)
// to locate pub-info's vercel/model-updates directory when running inside the repo.
func findRepoRoot() string {
	starts := []string{}
	if wd, err := os.Getwd(); err == nil {
		starts = append(starts, wd)
	}
	if exe, err := os.Executable(); err == nil {
		starts = append(starts, filepath.Dir(exe))
	}

	for _, start := range starts {
		dir := start
		for range 8 {
			if _, err := os.Stat(filepath.Join(dir, "vercel", "model-updates", "models.json")); err == nil {
				return dir
			}
			parent := filepath.Dir(dir)
			if parent == dir {
				break
			}
			dir = parent
		}
	}
	return ""
}
