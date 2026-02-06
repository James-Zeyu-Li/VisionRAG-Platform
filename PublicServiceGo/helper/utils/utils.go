package utils

import (
	"crypto/md5"
	"fmt"
	"math/rand"
	"time"
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
