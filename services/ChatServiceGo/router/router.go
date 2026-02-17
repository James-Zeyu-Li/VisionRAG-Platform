package router

import (
	"VisionRAG/ChatServiceGo/middleware"
	"VisionRAG/shared/monitor"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func InitRouter() *gin.Engine {

	r := gin.New()
	r.Use(gin.Recovery())

	// Metrics endpoint
	r.GET("/metrics", gin.WrapH(promhttp.Handler()))

	// Monitoring and logging middleware
	r.Use(monitor.PrometheusMiddleware())
	r.Use(gin.Logger())

	enterRouter := r.Group("/api/v1")

	// 需要鉴权的路由组
	authGroup := enterRouter.Group("/")
	authGroup.Use(middleware.Auth())
	{
		RegisterSessionRouter(authGroup.Group("/session"))

		AIRouter(authGroup.Group("/AI"))
		ImageRouter(authGroup.Group("/image"))
		FileRouter(authGroup.Group("/file"))
	}

	return r
}
