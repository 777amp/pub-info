package catalog

import (
	"context"
	"path/filepath"
	"testing"

	"github.com/777amp/pub-info/micro-apps/model-check/internal/provider"
	"github.com/777amp/pub-info/micro-apps/model-check/internal/store"
)

type stubProvider struct {
	info   provider.ProviderInfo
	models []provider.Model
}

func (s *stubProvider) Info() provider.ProviderInfo { return s.info }
func (s *stubProvider) Fetch(_ context.Context, _ bool) (provider.FetchResult, error) {
	return provider.FetchResult{Models: s.models, Source: "local"}, nil
}

func TestCatalogServiceHideAndUnhide(t *testing.T) {
	reg := provider.NewRegistry()
	_ = reg.Register(&stubProvider{
		info: provider.ProviderInfo{ID: "vercel", Name: "Vercel AI Gateway"},
		models: []provider.Model{
			{Provider: "vercel", ID: "b/model", Slug: "b/model", Type: "language", Tags: []string{"reasoning"}},
			{Provider: "vercel", ID: "a/model", Slug: "a/model", Type: "image", Tags: []string{"vision"}},
		},
	})

	tmp := t.TempDir()
	st := store.NewHiddenStore(map[string]string{"vercel": filepath.Join(tmp, "hidden.json")}, tmp)
	svc := NewService(reg, st)

	snap, err := svc.GetCatalog(context.Background(), "vercel", false, true)
	if err != nil {
		t.Fatalf("GetCatalog() error: %v", err)
	}
	if snap.VisibleCount != 2 || snap.HiddenCount != 0 {
		t.Fatalf("unexpected initial counts: visible=%d hidden=%d", snap.VisibleCount, snap.HiddenCount)
	}
	if snap.Models[0].ID != "a/model" {
		t.Fatalf("expected alphabetical sort, got %q first", snap.Models[0].ID)
	}

	snap, err = svc.SetHidden(context.Background(), "vercel", "a/model", true)
	if err != nil {
		t.Fatalf("SetHidden(true) error: %v", err)
	}
	if snap.VisibleCount != 1 || snap.HiddenCount != 1 {
		t.Fatalf("unexpected counts after hide: visible=%d hidden=%d", snap.VisibleCount, snap.HiddenCount)
	}

	snap, err = svc.SetHidden(context.Background(), "vercel", "a/model", false)
	if err != nil {
		t.Fatalf("SetHidden(false) error: %v", err)
	}
	if snap.VisibleCount != 2 || snap.HiddenCount != 0 {
		t.Fatalf("unexpected counts after unhide: visible=%d hidden=%d", snap.VisibleCount, snap.HiddenCount)
	}
}
