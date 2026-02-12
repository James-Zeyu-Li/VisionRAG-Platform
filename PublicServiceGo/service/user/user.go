package user

import (
	"VisionRAG/PublicServiceGo/dao/user"
	"VisionRAG/PublicServiceGo/helper/code"
	"VisionRAG/PublicServiceGo/helper/email"
	"VisionRAG/PublicServiceGo/helper/rabbitmq"
	"VisionRAG/PublicServiceGo/helper/redis"
	"VisionRAG/PublicServiceGo/helper/utils"
	"VisionRAG/PublicServiceGo/helper/utils/jwt"
	"VisionRAG/PublicServiceGo/model"
	"log"
)

func Login(username, password string) (string, code.Code) {
	var userInformation *model.User
	var ok bool
	//1:判断用户是否存在
	if ok, userInformation = user.IsExistUser(username); !ok {
		return "", code.CodeUserNotExist
	}
	//2:判断用户是否密码账号正确
	if userInformation.Password != utils.MD5(password) {
		return "", code.CodeInvalidPassword
	}
	//3:返回一个Token
	token, err := jwt.GenerateToken(uint(userInformation.ID), userInformation.Username)
	if err != nil {
		return "", code.CodeServerBusy
	}

	// 4: 发送登录成功消息到 RabbitMQ (包含 JWT 以演示)
	log.Printf("[MQ] Sending USER_LOGIN event for user: %s", username)
	eventData := rabbitmq.GenerateUserLoginEvent(uint(userInformation.ID), userInformation.Username, token)
	_ = rabbitmq.RMQUserEvent.Publish(eventData)

	return token, code.CodeSuccess
}

func Register(email_, password, captcha string) (string, code.Code) {
	var ok bool
	var userInformation *model.User

	//1:先判断用户是否已经存在了
	if ok, _ := user.IsExistUser(email_); ok {
		return "", code.CodeUserExist
	}

	//2:从redis中验证验证码是否有效
	if ok, _ := redis.CheckCaptchaForEmail(email_, captcha); !ok {
		return "", code.CodeInvalidCaptcha
	}

	//3：生成11位的账号
	username := utils.GetRandomNumbers(11)

	//4：注册到数据库中
	if userInformation, ok = user.Register(username, email_, password); !ok {
		return "", code.CodeServerBusy
	}

	// 5：开发模式：在控制台打印账号 ID，跳过真实的邮件发送
	log.Printf("[DEV MODE] Registration Success. Email: %s, Assigned Account ID: %s", email_, username)
	/*
		if err := email.SendCaptcha(email_, username, "Your account ID"); err != nil {
			return "", code.CodeServerBusy
		}
	*/

	// 6:生成Token
	token, err := jwt.GenerateToken(uint(userInformation.ID), userInformation.Username)
	if err != nil {
		return "", code.CodeServerBusy
	}

	// 7: 发送注册成功消息到 RabbitMQ
	eventData := rabbitmq.GenerateUserRegisteredEvent(uint(userInformation.ID), userInformation.Username, userInformation.Email)
	_ = rabbitmq.RMQUserEvent.Publish(eventData)

	return token, code.CodeSuccess
}

// 往指定邮箱发送验证码
func SendCaptcha(email_ string) code.Code {
	send_code := utils.GetRandomNumbers(6)
	//1:先存放到redis
	if err := redis.SetCaptchaForEmail(email_, send_code); err != nil {
		return code.CodeServerBusy
	}

	// 2: 开发模式：控制台打印验证码，跳过邮件发送
	log.Printf("[DEV MODE] Verification Code for %s is: %s", email_, send_code)
	/*
		if err := email.SendCaptcha(email_, send_code, "Your verification code"); err != nil {
			return code.CodeServerBusy
		}
	*/

	return code.CodeSuccess
}