package session

import (
	"VisionRAG/CoreServiceGo/helper/code"
	"VisionRAG/CoreServiceGo/controller"
	"VisionRAG/CoreServiceGo/model"
	"VisionRAG/CoreServiceGo/service/session"
	"net/http"

	"github.com/gin-gonic/gin"
)

type (
	GetUserSessionsResponse struct {
		controller.Response
		Sessions []model.SessionInfo `json:"sessions,omitempty"`
	}

	CreateSessionRequest struct {
		Title string `json:"title" binding:"required"`
	}

	CreateSessionResponse struct {
		SessionID string `json:"sessionId,omitempty"`
		controller.Response
	}

	ChatHistoryRequest struct {
		SessionID string `json:"sessionId,omitempty" binding:"required"`
	}
	ChatHistoryResponse struct {
		History []model.History `json:"history"`
		controller.Response
	}
)

func GetUserSessionsByUserName(c *gin.Context) {
	res := new(GetUserSessionsResponse)
	// 因为去掉了JWT，暂时从Query或Header获取，或者硬编码
	userName := c.Query("username") 
	if userName == "" {
		userName = "testuser"
	}

	userSessions, err := session.GetUserSessionsByUserName(userName)
	if err != nil {
		c.JSON(http.StatusOK, res.CodeOf(code.CodeServerBusy))
		return
	}

	res.Success()
	res.Sessions = userSessions
	c.JSON(http.StatusOK, res)
}

func CreateSession(c *gin.Context) {
	req := new(CreateSessionRequest)
	res := new(CreateSessionResponse)
	userName := c.Query("username")
	if userName == "" {
		userName = "testuser"
	}
	if err := c.ShouldBindJSON(req); err != nil {
		c.JSON(http.StatusOK, res.CodeOf(code.CodeInvalidParams))
		return
	}

	sessionID, code_ := session.CreateSession(userName, req.Title)
	if code_ != code.CodeSuccess {
		c.JSON(http.StatusOK, res.CodeOf(code_))
		return
	}

	res.Success()
	res.SessionID = sessionID
	c.JSON(http.StatusOK, res)
}

func ChatHistory(c *gin.Context) {
	req := new(ChatHistoryRequest)
	res := new(ChatHistoryResponse)
	userName := c.Query("username")
	if userName == "" {
		userName = "testuser"
	}
	if err := c.ShouldBindJSON(req); err != nil {
		c.JSON(http.StatusOK, res.CodeOf(code.CodeInvalidParams))
		return
	}
	history, code_ := session.GetChatHistory(userName, req.SessionID)
	if code_ != code.CodeSuccess {
		c.JSON(http.StatusOK, res.CodeOf(code_))
		return
	}

	res.Success()
	res.History = history
	c.JSON(http.StatusOK, res)
}