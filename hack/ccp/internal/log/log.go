package log

import (
	"io"
	"os"

	"github.com/go-logr/logr"
	"github.com/go-logr/zapr"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

// Logger returns a new application logger based on the Zap logger.
func Logger(w io.Writer, appName string, level int, debug bool) (logr.Logger, error) {
	var encoder zapcore.Encoder
	{
		if debug {
			config := zap.NewDevelopmentEncoderConfig()
			config.EncodeLevel = zapcore.CapitalColorLevelEncoder
			encoder = zapcore.NewConsoleEncoder(config)
		} else {
			config := zap.NewProductionEncoderConfig()
			encoder = zapcore.NewJSONEncoder(config)
		}
	}

	var writer zapcore.WriteSyncer
	{
		writer = zapcore.Lock(zapcore.AddSync(os.Stdout))
	}

	var levelEnabler zapcore.LevelEnabler
	{
		levelEnabler = zap.NewAtomicLevelAt(zapcore.Level(-level))
	}

	zlogger := zap.New(zapcore.NewCore(encoder, writer, levelEnabler))
	zlogger = zlogger.Named(appName)

	return zapr.NewLogger(zlogger), nil
}

// Sync flushes buffered logs.
func Sync(logger logr.Logger) {
	if logger, ok := logger.GetSink().(zapr.Underlier); ok {
		_ = logger.GetUnderlying().Core().Sync()
	}
}
