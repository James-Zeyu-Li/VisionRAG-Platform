package redis

import (
	"VisionRAG/CoreServiceGo/config"
	"fmt"
)

func GenerateCaptcha(email string) string {
	return fmt.Sprintf(config.DefaultRedisKeyConfig.CaptchaPrefix, email)
}