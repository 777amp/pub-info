package provider

import (
	"context"
	"fmt"
	"math"
	"strconv"
	"strings"
)

// Pricing holds normalized per-1M-token and per-unit pricing for a model.
type Pricing struct {
	InputPerMillion      *float64 `json:"inputPerMillion,omitempty"`
	OutputPerMillion     *float64 `json:"outputPerMillion,omitempty"`
	CacheReadPerMillion  *float64 `json:"cacheReadPerMillion,omitempty"`
	CacheWritePerMillion *float64 `json:"cacheWritePerMillion,omitempty"`
	ImagePerUnit         *float64 `json:"imagePerUnit,omitempty"`
	InputDisplay         string   `json:"inputDisplay"`
	OutputDisplay        string   `json:"outputDisplay"`
	Display              string   `json:"display"`
	HasTiers             bool     `json:"hasTiers"`
	VariesByProvider     bool     `json:"variesByProvider"`
}

// Model is the provider-agnostic representation displayed by the desktop UI.
type Model struct {
	Provider      string   `json:"provider"`
	ID            string   `json:"id"`
	Slug          string   `json:"slug"`
	Name          string   `json:"name"`
	OwnedBy       string   `json:"ownedBy"`
	Type          string   `json:"type"`
	Description   string   `json:"description"`
	ContextWindow int      `json:"contextWindow"`
	MaxTokens     int      `json:"maxTokens"`
	Released      int64    `json:"released"`
	Knowledge     string   `json:"knowledge"`
	ZDR           string   `json:"zdr"`
	NoTraining    string   `json:"noTraining"`
	Tags          []string `json:"tags"`
	InputMods     []string `json:"inputMods"`
	OutputMods    []string `json:"outputMods"`
	Pricing       Pricing  `json:"pricing"`
	Hidden        bool     `json:"hidden"`
}

// ProviderInfo describes a registered provider for the UI selector.
type ProviderInfo struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	BrowseURL string `json:"browseUrl"`
}

// FetchResult holds the normalized models and metadata returned by a Provider.
type FetchResult struct {
	Models []Model
	Source string // "live" or "local"
}

// Provider is the extensibility contract: implement this interface and register
// it in Registry to add a new model catalog (e.g. OpenRouter, Anthropic, etc.).
type Provider interface {
	Info() ProviderInfo
	Fetch(ctx context.Context, localOnly bool) (FetchResult, error)
}

// ParseFloat parses a JSON string or number into a float64 pointer.
func ParseFloat(raw any) *float64 {
	if raw == nil {
		return nil
	}
	var v float64
	switch t := raw.(type) {
	case float64:
		v = t
	case int:
		v = float64(t)
	case string:
		s := strings.TrimSpace(t)
		if s == "" {
			return nil
		}
		parsed, err := strconv.ParseFloat(s, 64)
		if err != nil {
			return nil
		}
		v = parsed
	default:
		return nil
	}
	if math.IsNaN(v) || math.IsInf(v, 0) {
		return nil
	}
	return &v
}

// PerMillion multiplies a per-token price pointer by 1,000,000.
func PerMillion(perToken *float64) *float64 {
	if perToken == nil {
		return nil
	}
	v := *perToken * 1_000_000
	return &v
}

// FormatUSD formats a dollar value to match pub-info's shared/modelmd.py rules:
// negative -> "varies", zero -> "Free", positive -> "$X.XX" (up to 4 decimals).
func FormatUSD(val *float64) string {
	if val == nil {
		return "-"
	}
	v := *val
	if v < 0 {
		return "varies"
	}
	if v == 0 {
		return "Free"
	}
	s := strings.TrimRight(fmt.Sprintf("%.4f", v), "0")
	parts := strings.SplitN(s, ".", 2)
	whole := parts[0]
	frac := ""
	if len(parts) == 2 {
		frac = parts[1]
	}
	for len(frac) < 2 {
		frac += "0"
	}
	return "$" + whole + "." + frac
}
