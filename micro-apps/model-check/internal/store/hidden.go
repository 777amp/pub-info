package store

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
)

// HiddenStore persists hidden model IDs per provider as sorted JSON arrays
// compatible with pub-info's <provider>/model-updates/hidden_models.json format.
type HiddenStore struct {
	mu      sync.RWMutex
	paths   map[string]string
	baseDir string
}

// NewHiddenStore creates a store with explicit provider->file overrides and a
// fallback directory (e.g. ~/.config/model-check) for providers without a repo file.
func NewHiddenStore(providerPaths map[string]string, fallbackDir string) *HiddenStore {
	copied := make(map[string]string, len(providerPaths))
	for k, v := range providerPaths {
		if v != "" {
			copied[k] = v
		}
	}
	return &HiddenStore{
		paths:   copied,
		baseDir: fallbackDir,
	}
}

func (s *HiddenStore) pathFor(providerID string) (string, error) {
	if p, ok := s.paths[providerID]; ok && p != "" {
		return p, nil
	}
	if s.baseDir == "" {
		return "", fmt.Errorf("no storage path configured for provider %q", providerID)
	}
	safe := strings.Map(func(r rune) rune {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == '-' || r == '_' {
			return r
		}
		return '_'
	}, strings.ToLower(providerID))
	return filepath.Join(s.baseDir, safe+"_hidden_models.json"), nil
}

// Load returns the set of hidden model IDs for a provider.
func (s *HiddenStore) Load(providerID string) (map[string]struct{}, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	p, err := s.pathFor(providerID)
	if err != nil {
		return nil, err
	}
	return readJSONSet(p)
}

// SetHidden adds or removes a model ID (and optional slug) from the provider's
// hidden_models.json atomically.
func (s *HiddenStore) SetHidden(providerID string, keys []string, hidden bool) error {
	if len(keys) == 0 {
		return fmt.Errorf("model ID is required")
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	p, err := s.pathFor(providerID)
	if err != nil {
		return err
	}

	set, err := readJSONSet(p)
	if err != nil {
		return err
	}

	for _, k := range keys {
		k = strings.TrimSpace(k)
		if k == "" {
			continue
		}
		if hidden {
			set[k] = struct{}{}
		} else {
			delete(set, k)
		}
	}

	return writeJSONSetAtomic(p, set)
}

func readJSONSet(path string) (map[string]struct{}, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return make(map[string]struct{}), nil
		}
		return nil, fmt.Errorf("read %s: %w", path, err)
	}

	var list []string
	if err := json.Unmarshal(data, &list); err != nil {
		return nil, fmt.Errorf("parse %s: %w", path, err)
	}

	set := make(map[string]struct{}, len(list))
	for _, id := range list {
		if id != "" {
			set[id] = struct{}{}
		}
	}
	return set, nil
}

func writeJSONSetAtomic(path string, set map[string]struct{}) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return fmt.Errorf("mkdir %s: %w", filepath.Dir(path), err)
	}

	sorted := make([]string, 0, len(set))
	for id := range set {
		sorted = append(sorted, id)
	}
	sort.Strings(sorted)

	encoded, err := json.MarshalIndent(sorted, "", "  ")
	if err != nil {
		return err
	}
	encoded = append(encoded, '\n')

	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, encoded, 0o644); err != nil {
		return fmt.Errorf("write temp file: %w", err)
	}
	if err := os.Rename(tmp, path); err != nil {
		_ = os.Remove(tmp)
		return fmt.Errorf("commit %s: %w", path, err)
	}
	return nil
}
