package queue

import (
	"fmt"
	amqp "github.com/rabbitmq/amqp091-go"
)

type RabbitMQ struct {
	conn      *amqp.Connection
	channel   *amqp.Channel
	QueueName string
	Exchange  string
	Key       string
}

type MQConfig struct {
	Host     string
	Port     int
	User     string
	Password string
	VHost    string
}

func NewConnection(cfg MQConfig) (*amqp.Connection, error) {
	url := fmt.Sprintf("amqp://%s:%s@%s:%d/%s", 
		cfg.User, cfg.Password, cfg.Host, cfg.Port, cfg.VHost)
	return amqp.Dial(url)
}

func NewRabbitMQ(conn *amqp.Connection, exchange, key, queue string) (*RabbitMQ, error) {
	ch, err := conn.Channel()
	if err != nil {
		return nil, err
	}
	return &RabbitMQ{
		conn:      conn,
		channel:   ch,
		Exchange:  exchange,
		Key:       key,
		QueueName: queue,
	}, nil
}

func (r *RabbitMQ) DeclareQueue() (amqp.Queue, error) {
	return r.channel.QueueDeclare(
		r.QueueName,
		true,  // durable
		false, // autoDelete
		false, // exclusive
		false, // noWait
		nil,   // args
	)
}

func (r *RabbitMQ) GetChannel() *amqp.Channel {
	return r.channel
}

func (r *RabbitMQ) Publish(message []byte) error {
	_, err := r.DeclareQueue()
	if err != nil {
		return err
	}
	return r.channel.Publish(
		r.Exchange,
		r.Key,
		false,
		false,
		amqp.Publishing{
			ContentType: "text/plain",
			Body:        message,
		},
	)
}

func (r *RabbitMQ) Destroy() {
	r.channel.Close()
}
