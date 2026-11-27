package provider

import (
	"fmt"
	"sync"
)

// Registry holds all registered model providers in deterministic insertion order.
type Registry struct {
	mu        sync.RWMutex
	order     []string
	providers map[string]Provider
}

func NewRegistry() *Registry {
	return &Registry{
		providers: make(map[string]Provider),
	}
}

func (r *Registry) Register(p Provider) error {
	if p == nil {
		return fmt.Errorf("provider cannot be nil")
	}
	id := p.Info().ID
	if id == "" {
		return fmt.Errorf("provider ID cannot be empty")
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, exists := r.providers[id]; !exists {
		r.order = append(r.order, id)
	}
	r.providers[id] = p
	return nil
}

func (r *Registry) Get(id string) (Provider, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	p, ok := r.providers[id]
	return p, ok
}

func (r *Registry) List() []ProviderInfo {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := make([]ProviderInfo, 0, len(r.order))
	for _, id := range r.order {
		out = append(out, r.providers[id].Info())
	}
	return out
}
