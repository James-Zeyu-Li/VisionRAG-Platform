package redis

import (
	"VisionRAG/ChatServiceGo/config"
	"fmt"
)

func GenerateCaptcha(email string) string {
	return fmt.Sprintf(config.DefaultRedisKeyConfig.CaptchaPrefix, email)
}