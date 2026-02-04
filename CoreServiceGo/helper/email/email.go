package email

import (
	"VisionRAG/CoreServiceGo/config"
	"fmt"

	"gopkg.in/gomail.v2"
)

func SendCaptcha(email, code, msg string) error {
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