package middleware

import (
	"VisionRAG/ChatServiceGo/controller"
	"VisionRAG/ChatServiceGo/helper/code"
	"VisionRAG/ChatServiceGo/helper/utils/jwt"
	"log"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

// Auth JWT 中间件
func Auth() gin.HandlerFunc {
	return func(c *gin.Context) {
		res := new(controller.Response)

		var token string
		authHeader := c.GetHeader("Authorization")
		if authHeader != "" && strings.HasPrefix(authHeader, "Bearer ") {
			token = strings.TrimPrefix(authHeader, "Bearer ")
		} else {
			// 兼容某些场景下 URL 参数传 token
			token = c.Query("token")
		}

		if token == "" {
			log.Println("[Auth Middleware] No token found in Request")
			c.JSON(http.StatusOK, res.CodeOf(code.CodeNotLogin))
			c.Abort()
			return
		}

		if len(token) > 10 {
			log.Printf("[Auth Middleware] Validating token: %s...", token[:10])
		} else {
			log.Printf("[Auth Middleware] Validating token: %s", token)
		}
		
		claims, err := jwt.ParseToken(token)
		if err != nil {
			log.Printf("[Auth Middleware] Token validation failed: %v", err)
			c.JSON(http.StatusOK, res.CodeOf(code.CodeInvalidToken))
			c.Abort()
			return
		}

		log.Printf("[Auth Middleware] Success! User: %s (ID: %d)", claims.Username, claims.UserID)

		// 将解析出来的用户信息存入上下文
		c.Set("userID", claims.UserID)
		c.Set("userName", claims.Username)
		
		c.Next()
	}
}
