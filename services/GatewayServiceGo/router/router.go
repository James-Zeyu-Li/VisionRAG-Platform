package router

import (
	"VisionRAG/GatewayServiceGo/config"
	"VisionRAG/GatewayServiceGo/middleware"
	"VisionRAG/GatewayServiceGo/proxy"
	"VisionRAG/shared/monitor"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func InitRouter() *gin.Engine {
	r := gin.New()        // Empty Gin Engine
	r.Use(gin.Recovery()) // capture panic

	r.GET("/metrics", gin.WrapH(promhttp.Handler()))

	// health check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "UP", "service": "Gateway"})
	})

	// Prometheus producer
	r.Use(monitor.PrometheusMiddleware())
	r.Use(gin.Logger())

	cfg := config.GetConfig()

	v1 := r.Group("/api/v1")
	{
		// 1.(Login/Register) -> PublicService
		publicGroup := v1.Group("/user")
		{
			publicGroup.Any("/*any", proxy.ProxyHandler(cfg.ServicesConfig.PublicServiceUrl))
		}

		// 2. Chat/Session/File -> ChatService
		authGroup := v1.Group("/")
		authGroup.Use(middleware.Auth())
		{
			authGroup.Any("/chat/*any", proxy.ProxyHandler(cfg.ServicesConfig.ChatServiceUrl))
			authGroup.Any("/session/*any", proxy.ProxyHandler(cfg.ServicesConfig.ChatServiceUrl))
			authGroup.Any("/AI/*any", proxy.ProxyHandler(cfg.ServicesConfig.ChatServiceUrl))
			authGroup.Any("/image/*any", proxy.ProxyHandler(cfg.ServicesConfig.ChatServiceUrl))
			authGroup.Any("/file/*any", proxy.ProxyHandler(cfg.ServicesConfig.ChatServiceUrl))
		}
	}

	return r
}
