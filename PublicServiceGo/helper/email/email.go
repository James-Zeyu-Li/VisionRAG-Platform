package email

import (
	"VisionRAG/PublicServiceGo/config"
	"fmt"

	"gopkg.in/gomail.v2"
)

const (
	CodeMsg     = "VisionRAG验证码如下(验证码仅限于2分钟有效): "
	UserNameMsg = "VisionRAG的账号如下，请保留好，后续可以用账号/邮箱登录 "
)

func SendCaptcha(email, code, msg string) error {

	fmt.Printf("\n[DEVELOPMENT] ================================\n")
	fmt.Printf("[DEVELOPMENT] 正在发送验证码到: %s\n", email)
	fmt.Printf("[DEVELOPMENT] 验证码是: %s\n", code)
	fmt.Printf("[DEVELOPMENT] 消息内容: %s\n", msg)
	fmt.Printf("[DEVELOPMENT] ================================\n\n")
	return nil

	m := gomail.NewMessage()

	m.SetHeader("From", config.GetConfig().EmailConfig.Email)
	m.SetHeader("To", email)
	m.SetHeader("Subject", "VisionRAG Notification")
	m.SetBody("text/plain", msg+" "+code)

	d := gomail.NewDialer("smtp.qq.com", 587, config.GetConfig().EmailConfig.Email, config.GetConfig().EmailConfig.Authcode)

	if err := d.DialAndSend(m); err != nil {
		fmt.Printf("DialAndSend err %v:\n", err)
		return err
	}
	fmt.Printf("send mail success\n")
	return nil
}