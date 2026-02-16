package file

import (
	"VisionRAG/ChatServiceGo/controller"
	"VisionRAG/ChatServiceGo/helper/code"
	"VisionRAG/ChatServiceGo/service/file"
	"VisionRAG/ChatServiceGo/utils"
	"net/http"

	"github.com/gin-gonic/gin"
)

type UploadResponse struct {
	controller.Response
	FilePath string `json:"file_path,omitempty"`
}

func UploadRagFile(c *gin.Context) {
	res := new(UploadResponse)
	
	// 从 header 或 query 获取用户名，配合 Auth 中间件
	username := c.GetString("username")
	if username == "" {
		username = c.Query("username")
	}
	if username == "" {
		username = "testuser"
	}

	fileHeader, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusOK, res.CodeOf(code.CodeInvalidParams))
		return
	}

	// 校验文件
	if err := utils.ValidateFile(fileHeader); err != nil {
		c.JSON(http.StatusOK, res.CodeOf(code.CodeInvalidParams))
		return
	}

	path, err := file.UploadRagFile(username, fileHeader)
	if err != nil {
		c.JSON(http.StatusOK, res.CodeOf(code.CodeServerBusy))
		return
	}

	res.Success()
	res.FilePath = path
	c.JSON(http.StatusOK, res)
}
