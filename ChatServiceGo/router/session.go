package router

import (
	"VisionRAG/ChatServiceGo/controller/session"

	"github.com/gin-gonic/gin"
)

func RegisterSessionRouter(r *gin.RouterGroup) {
	{
		r.GET("/list", session.GetUserSessionsByUserName)
		r.POST("/create", session.CreateSession)
		r.POST("/history", session.ChatHistory)
	}
}
