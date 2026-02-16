package router

import (
	"VisionRAG/GatewayServiceGo/config"
	"VisionRAG/GatewayServiceGo/middleware"
	"VisionRAG/GatewayServiceGo/proxy"

	"github.com/gin-gonic/gin"
)

func InitRouter() *gin.Engine {
	r := gin.Default()
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

	// health check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "UP", "service": "Gateway"})
	})

	return r
}
