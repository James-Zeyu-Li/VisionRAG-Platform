package router

import (
	"VisionRAG/ChatServiceGo/controller/file"

	"github.com/gin-gonic/gin"
)

func FileRouter(r *gin.RouterGroup) {
	r.POST("/upload", file.UploadRagFile)
}
