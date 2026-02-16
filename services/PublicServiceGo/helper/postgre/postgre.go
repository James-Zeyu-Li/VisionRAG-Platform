package postgre

import (
	"VisionRAG/PublicServiceGo/config"
	"VisionRAG/PublicServiceGo/model"
	"VisionRAG/shared/database"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

var DB *gorm.DB

func InitMysql() error {
	cfg := config.GetConfig().DBConfig

	db, err := database.InitDB(database.DBConfig{
		Host:     cfg.DBHost,
		Port:     cfg.DBPort,
		User:     cfg.DBUser,
		Password: cfg.DBPassword,
		DBName:   cfg.DBDatabaseName,
		SSLMode:  cfg.SSLMode,
		TimeZone: cfg.DBTimeZone,
	}, gin.Mode() == gin.DebugMode)

	if err != nil {
		return err
	}

	DB = db
	return migration()
}

func migration() error {
	return DB.AutoMigrate(new(model.User))
}

func InsertUser(user *model.User) (*model.User, error) {
	err := DB.Create(&user).Error
	return user, err
}

func GetUserByUsername(username string) (*model.User, error) {
	user := new(model.User)
	err := DB.Where("username = ?", username).First(user).Error
	return user, err
}
