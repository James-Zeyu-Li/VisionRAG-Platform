package session

import (
	"VisionRAG/ChatServiceGo/dao/message"
	"VisionRAG/ChatServiceGo/dao/session"
	"VisionRAG/ChatServiceGo/helper/code"
	"VisionRAG/ChatServiceGo/model"
	"log"

	"github.com/google/uuid"
)

func GetUserSessionsByUserName(userName string) ([]model.SessionInfo, error) {
	sessions, err := session.GetSessionsByUserName(userName)
	if err != nil {
		return nil, err
	}

	var sessionInfos []model.SessionInfo
	for _, s := range sessions {
		sessionInfos = append(sessionInfos, model.SessionInfo{
			SessionID: s.ID,
			Title:     s.Title,
		})
	}
	return sessionInfos, nil
}

func CreateSession(userName string, title string) (string, code.Code) {
	newSession := &model.Session{
		ID:       uuid.New().String(),
		UserName: userName,
		Title:    title,
	}
	_, err := session.CreateSession(newSession)
	if err != nil {
		log.Println("CreateSession error:", err)
		return "", code.CodeServerBusy
	}
	return newSession.ID, code.CodeSuccess
}

func GetChatHistory(userName string, sessionID string) ([]model.History, code.Code) {
	msgs, err := message.GetMessagesBySessionID(sessionID)
	if err != nil {
		log.Println("GetChatHistory error:", err)
		return nil, code.CodeServerBusy
	}

	history := make([]model.History, 0, len(msgs))
	for _, m := range msgs {
		history = append(history, model.History{
			IsUser:  m.IsUser,
			Content: m.Content,
		})
	}
	return history, code.CodeSuccess
}