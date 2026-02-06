package router

import (
	"VisionRAG/ChatServiceGo/middleware"

	"github.com/gin-gonic/gin"
)

func InitRouter() *gin.Engine {

	r := gin.Default()
	enterRouter := r.Group("/api/v1")
	
	// 需要鉴权的路由组
	authGroup := enterRouter.Group("/")
	authGroup.Use(middleware.Auth())
	{
		RegisterSessionRouter(authGroup.Group("/session"))
		
		// 预留 AI, Image, File 接口位置
		// AIRouter(authGroup.Group("/AI"))
		// ImageRouter(authGroup.Group("/image"))
		// FileRouter(authGroup.Group("/file"))
	}

	return r
}