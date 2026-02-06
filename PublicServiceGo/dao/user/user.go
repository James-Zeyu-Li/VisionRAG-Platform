package user

import (
	"VisionRAG/PublicServiceGo/helper/mysql"
	"VisionRAG/PublicServiceGo/helper/utils"
	"VisionRAG/PublicServiceGo/model"
	"context"

	"gorm.io/gorm"
)

const (
	CodeMsg     = "VisionRAG verification code: "
	UserNameMsg = "VisionRAG account ID: "
)

var ctx = context.Background()

func IsExistUser(username string) (bool, *model.User) {
	user, err := mysql.GetUserByUsername(username)
	if err == gorm.ErrRecordNotFound || user == nil {
		return false, nil
	}
	return true, user
}

func Register(username, email, password string) (*model.User, bool) {
	if user, err := mysql.InsertUser(&model.User{
		Email:    email,
		Name:     username,
		Username: username,
		Password: utils.MD5(password),
	}); err != nil {
		return nil, false
	} else {
		return user, true
	}
}