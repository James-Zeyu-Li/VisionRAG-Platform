package router

import (
	"VisionRAG/PublicServiceGo/gateway"
	"os"
	"github.com/gin-gonic/gin"
)

func InitRouter() *gin.Engine {

	r := gin.Default()
	
	// 注册用户相关本地路由
	enterRouter := r.Group("/api/v1")
	{
		RegisterUserRouter(enterRouter.Group("/user"))
	}

	// 注册网关转发路由，转发到 ChatServiceGo
	chatServiceAddr := os.Getenv("CHAT_SERVICE_ADDR")
	if chatServiceAddr == "" {
		chatServiceAddr = "http://localhost:9092"
	}
	gateway.RegisterGatewayRoutes(r, chatServiceAddr)

	return r
}