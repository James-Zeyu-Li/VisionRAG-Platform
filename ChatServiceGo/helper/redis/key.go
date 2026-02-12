package redis

import (
	"VisionRAG/ChatServiceGo/config"
	"fmt"
)

func GenerateCaptcha(email string) string {
	return fmt.Sprintf(config.DefaultRedisKeyConfig.CaptchaPrefix, email)
}

func GenerateIndexName(filename string) string {
	return fmt.Sprintf(config.DefaultRedisKeyConfig.IndexName, filename)
}

func GenerateIndexNamePrefix(filename string) string {
	return fmt.Sprintf(config.DefaultRedisKeyConfig.IndexNamePrefix, filename)
}