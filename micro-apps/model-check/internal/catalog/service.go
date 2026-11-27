package catalog

import (
	"context"
	"fmt"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/777amp/pub-info/micro-apps/model-check/internal/provider"
	"github.com/777amp/pub-info/micro-apps/model-check/internal/store"
)

// Snapshot is the complete payload returned to the frontend for a provider.
type Snapshot struct {
	Provider     provider.ProviderInfo `json:"provider"`
	Source       string                `json:"source"` // "live" or "local"
	FetchedAt    int64                 `json:"fetchedAt"`
	Models       []provider.Model      `json:"models"`
	Types        []string              `json:"types"`
	Tags         []string              `json:"tags"`
	VisibleCount int                   `json:"visibleCount"`
	HiddenCount  int                   `json:"hiddenCount"`
}

type cacheEntry struct {
	models    []provider.Model
	source    string
	fetchedAt int64
}

// Service coordinates providers, in-memory caching, and persistent hidden state.
type Service struct {
	registry *provider.Registry
	hidden   *store.HiddenStore

	mu    sync.RWMutex
	cache map[string]cacheEntry
}

func NewService(reg *provider.Registry, hidden *store.HiddenStore) *Service {
	return &Service{
		registry: reg,
		hidden:   hidden,
		cache:    make(map[string]cacheEntry),
	}
}

func (s *Service) ListProviders() []provider.ProviderInfo {
	return s.registry.List()
}

// GetCatalog returns the catalog for providerID, using the in-memory cache
// unless forceRefresh is true.
func (s *Service) GetCatalog(ctx context.Context, providerID string, forceRefresh bool, localOnly bool) (Snapshot, error) {
	p, ok := s.registry.Get(providerID)
	if !ok {
		return Snapshot{}, fmt.Errorf("unknown provider %q", providerID)
	}

	s.mu.RLock()
	entry, cached := s.cache[providerID]
	s.mu.RUnlock()

	if !cached || forceRefresh {
		res, err := p.Fetch(ctx, localOnly)
		if err != nil {
			return Snapshot{}, err
		}
		entry = cacheEntry{
			models:    res.Models,
			source:    res.Source,
			fetchedAt: time.Now().Unix(),
		}
		s.mu.Lock()
		s.cache[providerID] = entry
		s.mu.Unlock()
	}

	hiddenSet, err := s.hidden.Load(providerID)
	if err != nil {
		return Snapshot{}, err
	}

	return buildSnapshot(p.Info(), entry, hiddenSet), nil
}

// SetHidden persistently hides or unhides a model and returns the updated Snapshot.
func (s *Service) SetHidden(ctx context.Context, providerID, modelID string, hidden bool) (Snapshot, error) {
	modelID = strings.TrimSpace(modelID)
	if modelID == "" {
		return Snapshot{}, fmt.Errorf("model ID cannot be empty")
	}
	if _, ok := s.registry.Get(providerID); !ok {
		return Snapshot{}, fmt.Errorf("unknown provider %q", providerID)
	}

	keys := []string{modelID}
	s.mu.RLock()
	if entry, ok := s.cache[providerID]; ok {
		for _, m := range entry.models {
			if m.ID == modelID || m.Slug == modelID {
				keys = []string{m.ID}
				if m.Slug != "" && m.Slug != m.ID {
					keys = append(keys, m.Slug)
				}
				break
			}
		}
	}
	s.mu.RUnlock()

	if err := s.hidden.SetHidden(providerID, keys, hidden); err != nil {
		return Snapshot{}, err
	}

	return s.GetCatalog(ctx, providerID, false, false)
}

func buildSnapshot(info provider.ProviderInfo, entry cacheEntry, hiddenSet map[string]struct{}) Snapshot {
	models := make([]provider.Model, len(entry.models))
	typeSet := make(map[string]struct{})
	tagSet := make(map[string]struct{})
	visibleCount := 0
	hiddenCount := 0

	for i, m := range entry.models {
		_, idHidden := hiddenSet[m.ID]
		_, slugHidden := hiddenSet[m.Slug]
		m.Hidden = idHidden || slugHidden
		if m.Hidden {
			hiddenCount++
		} else {
			visibleCount++
		}
		if m.Type != "" {
			typeSet[m.Type] = struct{}{}
		}
		for _, t := range m.Tags {
			if t != "" {
				tagSet[t] = struct{}{}
			}
		}
		models[i] = m
	}

	sort.Slice(models, func(i, j int) bool {
		return strings.ToLower(models[i].ID) < strings.ToLower(models[j].ID)
	})

	return Snapshot{
		Provider:     info,
		Source:       entry.source,
		FetchedAt:    entry.fetchedAt,
		Models:       models,
		Types:        sortedKeys(typeSet),
		Tags:         sortedKeys(tagSet),
		VisibleCount: visibleCount,
		HiddenCount:  hiddenCount,
	}
}

func sortedKeys(m map[string]struct{}) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
