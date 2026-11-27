package vercel

import (
	"context"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

const samplePayload = `{
  "object": "list",
  "data": [
    {
      "id": "anthropic/claude-sonnet-5",
      "owned_by": "anthropic",
      "name": "Claude Sonnet 5",
      "description": "Fast reasoning model",
      "context_window": 1000000,
      "max_tokens": 64000,
      "released": 1750000000,
      "type": "language",
      "zdr": "all",
      "no_training": "all",
      "knowledge": "2026-03",
      "tags": ["reasoning", "tool-use", "vision"],
      "modalities": { "input": ["text", "image"], "output": ["text"] },
      "pricing": {
        "input": "0.000002",
        "output": "0.00001",
        "input_cache_read": "0.0000002"
      }
    },
    {
      "id": "openai/tiered-model",
      "owned_by": "openai",
      "name": "Tiered Model",
      "type": "language",
      "pricing": {
        "input_tiers": [{ "cost": "0.0000015" }],
        "output_tiers": [{ "cost": "0.000006" }]
      }
    },
    {
      "id": "bfl/flux-pro",
      "owned_by": "bfl",
      "name": "Flux Pro",
      "type": "image",
      "pricing": { "image": "0.04" }
    }
  ]
}`

func TestFetchLiveAndPricingNormalization(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(samplePayload))
	}))
	defer srv.Close()

	p := New(WithEndpoint(srv.URL), WithHTTPClient(srv.Client()))
	res, err := p.Fetch(context.Background(), false)
	if err != nil {
		t.Fatalf("Fetch() error: %v", err)
	}
	if res.Source != "live" {
		t.Fatalf("expected source=live, got %q", res.Source)
	}
	if len(res.Models) != 3 {
		t.Fatalf("expected 3 models, got %d", len(res.Models))
	}

	claude := res.Models[0]
	if claude.Pricing.Display != "$2.00 → $10.00" {
		t.Errorf("unexpected claude display price: %q", claude.Pricing.Display)
	}
	if claude.Pricing.CacheReadPerMillion == nil || *claude.Pricing.CacheReadPerMillion < 0.199999999 || *claude.Pricing.CacheReadPerMillion > 0.200000001 {
		t.Errorf("unexpected cache read price: %v", claude.Pricing.CacheReadPerMillion)
	}

	tiered := res.Models[1]
	if !tiered.Pricing.HasTiers || tiered.Pricing.Display != "$1.50 → $6.00" {
		t.Errorf("unexpected tiered pricing: %+v", tiered.Pricing)
	}

	img := res.Models[2]
	if img.Pricing.Display != "$0.04/img" {
		t.Errorf("unexpected image pricing: %q", img.Pricing.Display)
	}
}

func TestFetchFallsBackToLocalSnapshot(t *testing.T) {
	tmp := t.TempDir()
	snap := filepath.Join(tmp, "models.json")
	if err := os.WriteFile(snap, []byte(samplePayload), 0o644); err != nil {
		t.Fatal(err)
	}

	// Point endpoint at a closed server so live fetch fails immediately.
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {}))
	srv.Close()

	p := New(WithEndpoint(srv.URL), WithLocalSnapshot(snap))
	res, err := p.Fetch(context.Background(), false)
	if err != nil {
		t.Fatalf("expected fallback to succeed, got err: %v", err)
	}
	if res.Source != "local" {
		t.Fatalf("expected source=local, got %q", res.Source)
	}
	if len(res.Models) != 3 {
		t.Fatalf("expected 3 models, got %d", len(res.Models))
	}
}
