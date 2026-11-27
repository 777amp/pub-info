package main

import (
	"embed"
	"log"
	"runtime/debug"

	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
)

//go:embed all:frontend/dist
var assets embed.FS

func main() {
	// Keep Go heap footprint compact for a low-RAM desktop utility.
	debug.SetMemoryLimit(64 << 20)

	app := NewApp()

	err := wails.Run(&options.App{
		Title:     "Model Check — Vercel AI Gateway",
		Width:     1180,
		Height:    760,
		MinWidth:  840,
		MinHeight: 540,
		AssetServer: &assetserver.Options{
			Assets: assets,
		},
		BackgroundColour: &options.RGBA{R: 13, G: 15, B: 20, A: 255},
		OnStartup:        app.startup,
		Bind: []interface{}{
			app,
		},
	})
	if err != nil {
		log.Fatal(err)
	}
}
