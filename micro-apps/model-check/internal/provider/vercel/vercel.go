package vercel

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"

	"github.com/777amp/pub-info/micro-apps/model-check/internal/provider"
)

const (
	ProviderID = "vercel"
	DefaultURL = "https://ai-gateway.vercel.sh/v1/models"
	BrowseURL  = "https://vercel.com/ai-gateway/models"
)

type Option func(*Provider)

// WithEndpoint overrides the Vercel AI Gateway API URL (useful for testing).
func WithEndpoint(url string) Option {
	return func(p *Provider) { p.endpoint = url }
}

// WithLocalSnapshot sets an optional local models.json fallback path.
func WithLocalSnapshot(path string) Option {
	return func(p *Provider) { p.localPath = path }
}

// WithHTTPClient overrides the HTTP client used for live requests.
func WithHTTPClient(c *http.Client) Option {
	return func(p *Provider) { p.client = c }
}

// Provider fetches and normalizes models from Vercel AI Gateway.
type Provider struct {
	endpoint  string
	localPath string
	client    *http.Client
}

func New(opts ...Option) *Provider {
	p := &Provider{
		endpoint: DefaultURL,
		client:   &http.Client{Timeout: 10 * time.Second},
	}
	for _, opt := range opts {
		opt(p)
	}
	return p
}

func (p *Provider) Info() provider.ProviderInfo {
	return provider.ProviderInfo{
		ID:        ProviderID,
		Name:      "Vercel AI Gateway",
		BrowseURL: BrowseURL,
	}
}

// Fetch retrieves models from the live Vercel AI Gateway endpoint and falls back
// to the local repo snapshot if offline or unreachable.
func (p *Provider) Fetch(ctx context.Context, localOnly bool) (provider.FetchResult, error) {
	if !localOnly && p.endpoint != "" {
		models, err := p.fetchLive(ctx)
		if err == nil {
			return provider.FetchResult{Models: models, Source: "live"}, nil
		}
		if p.localPath == "" {
			return provider.FetchResult{}, err
		}
		// Fall through to local snapshot when live fetch fails.
	}

	if p.localPath != "" {
		models, err := p.loadLocal()
		if err == nil {
			return provider.FetchResult{Models: models, Source: "local"}, nil
		}
		return provider.FetchResult{}, fmt.Errorf("vercel catalog unavailable (live and local failed): %w", err)
	}

	return provider.FetchResult{}, fmt.Errorf("vercel catalog unavailable: no endpoint or local snapshot configured")
}

func (p *Provider) fetchLive(ctx context.Context) ([]provider.Model, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, p.endpoint, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/json")

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status %d from %s", resp.StatusCode, p.endpoint)
	}
	return decodeCatalog(resp.Body)
}

func (p *Provider) loadLocal() ([]provider.Model, error) {
	f, err := os.Open(p.localPath)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return decodeCatalog(f)
}

// Compact decoding structs — only fields we actually use are retained in RAM.
type rawCatalog struct {
	Data []rawModel `json:"data"`
}

type rawModel struct {
	ID            string        `json:"id"`
	OwnedBy       string        `json:"owned_by"`
	Name          string        `json:"name"`
	Description   string        `json:"description"`
	ContextWindow int           `json:"context_window"`
	MaxTokens     int           `json:"max_tokens"`
	Released      int64         `json:"released"`
	Created       int64         `json:"created"`
	Type          string        `json:"type"`
	ZDR           string        `json:"zdr"`
	NoTraining    string        `json:"no_training"`
	Knowledge     string        `json:"knowledge"`
	Tags          []string      `json:"tags"`
	Modalities    rawModalities `json:"modalities"`
	Pricing       rawPricing    `json:"pricing"`
}

type rawModalities struct {
	Input  []string `json:"input"`
	Output []string `json:"output"`
}

type rawTier struct {
	Cost any `json:"cost"`
}

type rawPricing struct {
	Input            any       `json:"input"`
	Output           any       `json:"output"`
	InputTiers       []rawTier `json:"input_tiers"`
	OutputTiers      []rawTier `json:"output_tiers"`
	InputCacheRead   any       `json:"input_cache_read"`
	InputCacheWrite  any       `json:"input_cache_write"`
	Image            any       `json:"image"`
	VariesByProvider any       `json:"varies_by_provider"`
}

func decodeCatalog(r io.Reader) ([]provider.Model, error) {
	var raw rawCatalog
	if err := json.NewDecoder(r).Decode(&raw); err != nil {
		return nil, fmt.Errorf("decode vercel catalog: %w", err)
	}

	models := make([]provider.Model, 0, len(raw.Data))
	for _, m := range raw.Data {
		if m.ID == "" {
			continue
		}
		models = append(models, normalize(m))
	}
	return models, nil
}

func normalize(m rawModel) provider.Model {
	name := m.Name
	if name == "" {
		name = m.ID
	}
	released := m.Released
	if released == 0 {
		released = m.Created
	}

	tags := m.Tags
	if tags == nil {
		tags = []string{}
	}
	inMods := m.Modalities.Input
	if inMods == nil {
		inMods = []string{}
	}
	outMods := m.Modalities.Output
	if outMods == nil {
		outMods = []string{}
	}

	return provider.Model{
		Provider:      ProviderID,
		ID:            m.ID,
		Slug:          m.ID,
		Name:          name,
		OwnedBy:       m.OwnedBy,
		Type:          m.Type,
		Description:   m.Description,
		ContextWindow: m.ContextWindow,
		MaxTokens:     m.MaxTokens,
		Released:      released,
		Knowledge:     m.Knowledge,
		ZDR:           m.ZDR,
		NoTraining:    m.NoTraining,
		Tags:          tags,
		InputMods:     inMods,
		OutputMods:    outMods,
		Pricing:       normalizePricing(m.Pricing),
	}
}

func normalizePricing(rp rawPricing) provider.Pricing {
	rawIn := rp.Input
	hasTiers := len(rp.InputTiers) > 0 || len(rp.OutputTiers) > 0
	if rawIn == nil && len(rp.InputTiers) > 0 {
		rawIn = rp.InputTiers[0].Cost
	}
	rawOut := rp.Output
	if rawOut == nil && len(rp.OutputTiers) > 0 {
		rawOut = rp.OutputTiers[0].Cost
	}

	inPerM := provider.PerMillion(provider.ParseFloat(rawIn))
	outPerM := provider.PerMillion(provider.ParseFloat(rawOut))
	cacheRead := provider.PerMillion(provider.ParseFloat(rp.InputCacheRead))
	cacheWrite := provider.PerMillion(provider.ParseFloat(rp.InputCacheWrite))
	imgUnit := provider.ParseFloat(rp.Image)

	inDisp := provider.FormatUSD(inPerM)
	outDisp := provider.FormatUSD(outPerM)
	display := "-"

	if inPerM != nil || outPerM != nil {
		if inDisp == "Free" && outDisp == "Free" {
			display = "Free"
		} else {
			display = inDisp + " → " + outDisp
		}
	} else if imgUnit != nil {
		imgDisp := provider.FormatUSD(imgUnit)
		inDisp = imgDisp + "/img"
		display = inDisp
	}

	varies := false
	if b, ok := rp.VariesByProvider.(bool); ok && b {
		varies = true
	}

	return provider.Pricing{
		InputPerMillion:      inPerM,
		OutputPerMillion:     outPerM,
		CacheReadPerMillion:  cacheRead,
		CacheWritePerMillion: cacheWrite,
		ImagePerUnit:         imgUnit,
		InputDisplay:         inDisp,
		OutputDisplay:        outDisp,
		Display:              display,
		HasTiers:             hasTiers,
		VariesByProvider:     varies,
	}
}
