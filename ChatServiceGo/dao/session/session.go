package session

import (
	"VisionRAG/ChatServiceGo/helper/postgre"
	"VisionRAG/ChatServiceGo/model"
)

func GetSessionsByUserName(userName string) ([]model.Session, error) {
	var sessions []model.Session
	err := postgre.DB.Where("user_name = ?", userName).Find(&sessions).Error
	return sessions, err
}

func CreateSession(session *model.Session) (*model.Session, error) {
	err := postgre.DB.Create(session).Error
	return session, err
}

func GetSessionByID(sessionID string) (*model.Session, error) {
	var session model.Session
	err := postgre.DB.Where("id = ?", sessionID).First(&session).Error
	return &session, err
}