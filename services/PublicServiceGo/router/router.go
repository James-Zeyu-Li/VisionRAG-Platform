package router

import (
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
	{
		RegisterUserRouter(enterRouter.Group("/user"))
	}

	return r
}
