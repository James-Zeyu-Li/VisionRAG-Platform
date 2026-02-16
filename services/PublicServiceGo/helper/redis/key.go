package redis

import (
	"VisionRAG/PublicServiceGo/config"
	"fmt"
)

func GenerateCaptcha(email string) string {
	return fmt.Sprintf(config.DefaultRedisKeyConfig.CaptchaPrefix, email)
}