package main

import (
	"VisionRAG/GatewayServiceGo/config"
	"VisionRAG/GatewayServiceGo/router"
	"fmt"
	"log"
)

func main() {
	if err := config.InitConfig(); err != nil {
		log.Fatalf("Failed to init config: %v", err)
	}

	conf := config.GetConfig()
	addr := fmt.Sprintf("%s:%d", conf.Host, conf.Port)

	r := router.InitRouter()

	log.Printf("Gateway Service starting on %s", addr)
	if err := r.Run(addr); err != nil {
		log.Fatalf("Failed to run server: %v", err)
	}
}
