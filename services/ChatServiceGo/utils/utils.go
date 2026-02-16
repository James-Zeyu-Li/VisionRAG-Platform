package utils

import (
	"VisionRAG/ChatServiceGo/model"
	"crypto/md5"
	"fmt"
	"math/rand"
	"mime/multipart"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/cloudwego/eino/schema"
	"github.com/google/uuid"
)

// MD5 加密
func MD5(str string) string {
	data := []byte(str)
	has := md5.Sum(data)
	return fmt.Sprintf("%x", has)
}

// GetRandomNumbers 生成指定长度的数字字符串
func GetRandomNumbers(length int) string {
	rand.Seed(time.Now().UnixNano())
	result := ""
	for i := 0; i < length; i++ {
		result += fmt.Sprintf("%d", rand.Intn(10))
	}
	return result
}

func GenerateUUID() string {
	return uuid.New().String()
}

// 将 schema 消息转换为数据库可存储的格式
func ConvertToModelMessage(sessionID string, userName string, msg *schema.Message) *model.Message {
	return &model.Message{
		SessionID: sessionID,
		UserName:  userName,
		Content:   msg.Content,
	}
}

// 将数据库消息转换为 schema 消息（供 AI 使用）
func ConvertToSchemaMessages(msgs []*model.Message) []*schema.Message {
	schemaMsgs := make([]*schema.Message, 0, len(msgs))
	for _, m := range msgs {
		role := schema.Assistant
		if m.IsUser {
			role = schema.User
		}
		schemaMsgs = append(schemaMsgs, &schema.Message{
			Role:    role,
			Content: m.Content,
		})
	}
	return schemaMsgs
}

// RemoveAllFilesInDir 删除目录中的所有文件（不删除子目录）
func RemoveAllFilesInDir(dir string) error {
	entries, err := os.ReadDir(dir)
	if err != nil {
		if os.IsNotExist(err) {
			return nil // 目录不存在就算了
		}
		return err
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			filePath := filepath.Join(dir, entry.Name())
			if err := os.Remove(filePath); err != nil {
				return err
			}
		}
	}
	return nil
}

// ValidateFile 校验文件是否为允许的文本文件（.md 或 .txt）
func ValidateFile(file *multipart.FileHeader) error {
	// 校验文件扩展名
	ext := strings.ToLower(filepath.Ext(file.Filename))
	if ext != ".md" && ext != ".txt" {
		return fmt.Errorf("文件类型不正确，只允许 .md 或 .txt 文件，当前扩展名: %s", ext)
	}

	return nil
}
