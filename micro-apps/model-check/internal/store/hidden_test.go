package store

import (
	"os"
	"path/filepath"
	"testing"
)

func TestHiddenStoreRoundTrip(t *testing.T) {
	tmp := t.TempDir()
	vercelFile := filepath.Join(tmp, "hidden_models.json")
	s := NewHiddenStore(map[string]string{"vercel": vercelFile}, tmp)

	// Empty initially.
	set, err := s.Load("vercel")
	if err != nil {
		t.Fatalf("Load() error: %v", err)
	}
	if len(set) != 0 {
		t.Fatalf("expected empty set, got %d", len(set))
	}

	// Hide two models in reverse alphabetical order and confirm sorted JSON output.
	if err := s.SetHidden("vercel", []string{"z/model", "a/model"}, true); err != nil {
		t.Fatalf("SetHidden(true) error: %v", err)
	}

	raw, err := os.ReadFile(vercelFile)
	if err != nil {
		t.Fatalf("ReadFile error: %v", err)
	}
	want := "[\n  \"a/model\",\n  \"z/model\"\n]\n"
	if string(raw) != want {
		t.Fatalf("unexpected file contents:\ngot:\n%s\nwant:\n%s", string(raw), want)
	}

	// Unhide one model.
	if err := s.SetHidden("vercel", []string{"a/model"}, false); err != nil {
		t.Fatalf("SetHidden(false) error: %v", err)
	}
	set, err = s.Load("vercel")
	if err != nil {
		t.Fatalf("Load() after unhide error: %v", err)
	}
	if _, ok := set["a/model"]; ok {
		t.Errorf("expected a/model to be removed")
	}
	if _, ok := set["z/model"]; !ok {
		t.Errorf("expected z/model to remain hidden")
	}
}
