package middleware

import (
	"VisionRAG/ChatServiceGo/controller"
	"VisionRAG/ChatServiceGo/helper/code"
	"errors"
	"log"
	"net/http"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
)

const (
	HeaderUserID    = "X-User-Id"
	HeaderUserName  = "X-User-Name"
	HeaderRequestID = "X-Request-Id"

	CtxUserID    = "userID"
	CtxUserName  = "userName"
	CtxRequestID = "requestID"
)

var(
	ErrMissingUserID    = errors.New("missing x-user-id")
	ErrInvalidUserID    = errors.New("invalid x-user-id")
	ErrMissingUserName  = errors.New("missing x-user-name")
	ErrMissingRequestID = errors.New("missing x-request-id")
)

func ReadUserIDFromHeader(c *gin.Context)(int64, error){
	raw := strings.TrimSpace(c.GetHeader(HeaderUserID))
	if raw == ""{
		return 0, ErrMissingUserID
	}

	id, err := strconv.ParseInt(raw, 10, 64)
	if err != nil || id <= 0{
		return 0, ErrInvalidUserID
	}
	return id, nil
}

func ReadUserNameFromHeader(c *gin.Context) (string, error) {
	name := strings.TrimSpace(c.GetHeader(HeaderUserName))
	if name == "" {
		return "", ErrMissingUserName
	}
	return name, nil
}

func ReadRequestIDFromHeader(c *gin.Context) (string, error) {
	rid := strings.TrimSpace(c.GetHeader(HeaderRequestID))
	if rid == "" {
		return "", ErrMissingRequestID
	}
	return rid, nil
}

func GetUserID(c *gin.Context) (int64, bool) {
	v, ok := c.Get(CtxUserID)
	if !ok {
		return 0, false
	}
	id, ok := v.(int64)
	return id, ok
}

func GetUserName(c *gin.Context) (string, bool) {
	v, ok := c.Get(CtxUserName)
	if !ok {
		return "", false
	}
	s, ok := v.(string)
	return s, ok
}

func GetRequestID(c *gin.Context) (string, bool) {
	v, ok := c.Get(CtxRequestID)
	if !ok {
		return "", false
	}
	s, ok := v.(string)
	return s, ok
}

func Auth() gin.HandlerFunc {
	return func(c *gin.Context) {
		res := new(controller.Response)

		fail := func(err error, detail string) {
			if detail != "" {
				log.Printf("[HeaderAuth] %v: %s", err, detail)
			} else {
				log.Printf("[HeaderAuth] %v", err)
			}
			// Keep your existing project convention: HTTP 200 + business code
			c.JSON(http.StatusOK, res.CodeOf(code.CodeNotLogin))
			c.Abort()
		}

		userID, err := ReadUserIDFromHeader(c)
		if err != nil {
			fail(err, "bad or missing user id")
			return
		}

		userName, err := ReadUserNameFromHeader(c)
		if err != nil {
			fail(err, "bad or missing user name")
			return
		}

		requestID, err := ReadRequestIDFromHeader(c)
		if err != nil {
			fail(err, "bad or missing request id")
			return
		}

		// 写入上下文，保持你原来的 controller/service 读取方式
		c.Set(CtxUserID, userID)
		c.Set(CtxUserName, userName)
		c.Set(CtxRequestID, requestID)

		// 可选：把 request-id 回传给客户端便于排障
		c.Header(HeaderRequestID, requestID)

		c.Next()
	
	}
}
