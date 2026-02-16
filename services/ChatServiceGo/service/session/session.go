package session

import (
	"VisionRAG/ChatServiceGo/dao/message"
	"VisionRAG/ChatServiceGo/dao/session"
	"VisionRAG/ChatServiceGo/helper/aihelper"
	"VisionRAG/ChatServiceGo/helper/code"
	"VisionRAG/ChatServiceGo/model"
	"context"
	"log"
	"net/http"

	"github.com/google/uuid"
)

var ctx = context.Background()

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
	// 1. 尝试从 AIHelper 内存获取
	manager := aihelper.GetGlobalManager()
	helper, exists := manager.GetAIHelper(userName, sessionID)
	if exists {
		messages := helper.GetMessages()
		history := make([]model.History, 0, len(messages))
		for _, m := range messages {
			history = append(history, model.History{
				IsUser:  m.IsUser,
				Content: m.Content,
			})
		}
		return history, code.CodeSuccess
	}

	// 2. 如果内存没有，从数据库获取
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

func CreateSessionAndSendMessage(userName string, userQuestion string, modelType string) (string, string, code.Code) {
	newSession := &model.Session{
		ID:       uuid.New().String(),
		UserName: userName,
		Title:    userQuestion,
	}
	createdSession, err := session.CreateSession(newSession)
	if err != nil {
		log.Println("CreateSessionAndSendMessage CreateSession error:", err)
		return "", "", code.CodeServerBusy
	}

	manager := aihelper.GetGlobalManager()
	config := map[string]interface{}{
		"username": userName,
	}
	helper, err := manager.GetOrCreateAIHelper(userName, createdSession.ID, modelType, config)
	if err != nil {
		log.Println("CreateSessionAndSendMessage GetOrCreateAIHelper error:", err)
		return "", "", code.AIModelFail
	}

	aiResponse, err_ := helper.GenerateResponse(userName, ctx, userQuestion)
	if err_ != nil {
		log.Println("CreateSessionAndSendMessage GenerateResponse error:", err_)
		return "", "", code.AIModelFail
	}

	return createdSession.ID, aiResponse.Content, code.CodeSuccess
}

func CreateStreamSessionOnly(userName string, userQuestion string) (string, code.Code) {
	newSession := &model.Session{
		ID:       uuid.New().String(),
		UserName: userName,
		Title:    userQuestion,
	}
	createdSession, err := session.CreateSession(newSession)
	if err != nil {
		log.Println("CreateStreamSessionOnly CreateSession error:", err)
		return "", code.CodeServerBusy
	}
	return createdSession.ID, code.CodeSuccess
}

func StreamMessageToExistingSession(userName string, sessionID string, userQuestion string, modelType string, writer http.ResponseWriter) code.Code {
	flusher, ok := writer.(http.Flusher)
	if !ok {
		log.Println("StreamMessageToExistingSession: streaming unsupported")
		return code.CodeServerBusy
	}

	manager := aihelper.GetGlobalManager()
	config := map[string]interface{}{
		"username": userName,
	}
	helper, err := manager.GetOrCreateAIHelper(userName, sessionID, modelType, config)
	if err != nil {
		log.Println("StreamMessageToExistingSession GetOrCreateAIHelper error:", err)
		return code.AIModelFail
	}

	cb := func(msg string) {
		log.Printf("[SSE] Sending chunk: %s (len=%d)\n", msg, len(msg))
		_, err := writer.Write([]byte("data: " + msg + "\n\n"))
		if err != nil {
			log.Println("[SSE] Write error:", err)
			return
		}
		flusher.Flush()
	}

	_, err_ := helper.StreamResponse(userName, ctx, cb, userQuestion)
	if err_ != nil {
		log.Println("StreamMessageToExistingSession StreamResponse error:", err_)
		return code.AIModelFail
	}

	_, err = writer.Write([]byte("data: [DONE]\n\n"))
	if err != nil {
		log.Println("StreamMessageToExistingSession write DONE error:", err)
		return code.AIModelFail
	}
	flusher.Flush()

	return code.CodeSuccess
}

func ChatSend(userName string, sessionID string, userQuestion string, modelType string) (string, code.Code) {
	manager := aihelper.GetGlobalManager()
	config := map[string]interface{}{
		"username": userName,
	}
	helper, err := manager.GetOrCreateAIHelper(userName, sessionID, modelType, config)
	if err != nil {
		log.Println("ChatSend GetOrCreateAIHelper error:", err)
		return "", code.AIModelFail
	}

	aiResponse, err_ := helper.GenerateResponse(userName, ctx, userQuestion)
	if err_ != nil {
		log.Println("ChatSend GenerateResponse error:", err_)
		return "", code.AIModelFail
	}

	return aiResponse.Content, code.CodeSuccess
}

func ChatStreamSend(userName string, sessionID string, userQuestion string, modelType string, writer http.ResponseWriter) code.Code {
	return StreamMessageToExistingSession(userName, sessionID, userQuestion, modelType, writer)
}
