package image

import "log"

type ImageRecognizer struct {
	ModelPath string
	LabelPath string
}

func NewImageRecognizer(modelPath, labelPath string, inputH, inputW int) (*ImageRecognizer, error) {
	log.Printf("Warning: Image recognition placeholder initialized. Remote Python service should handle this later.")
	return &ImageRecognizer{
		ModelPath: modelPath,
		LabelPath: labelPath,
	}, nil
}

func (r *ImageRecognizer) Close() error {
	return nil
}

func (r *ImageRecognizer) PredictFromBuffer(buf []byte) (string, error) {
	return "Image recognition is not implemented yet in Go. This will be handled by the Python Vision service.", nil
}
