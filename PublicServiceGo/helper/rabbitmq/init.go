package rabbitmq

var (
	RMQUserEvent *RabbitMQ
)

func InitRabbitMQ() {
	// PublicService 只负责发送注册事件
	RMQUserEvent = NewWorkRabbitMQ("UserEvent")
}

// DestroyRabbitMQ 销毁RabbitMQ
func DestroyRabbitMQ() {
	if RMQUserEvent != nil {
		RMQUserEvent.Destroy()
	}
}
