package log

import (
	"fmt"
	"io"
	"math"
	"os"
	"strconv"
	"time"

	"github.com/go-logr/logr"
	"github.com/go-logr/zapr"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

// Logger returns a new application logger based on the Zap logger.
func Logger(w io.Writer, appName string, level int, debug bool) (logr.Logger, error) {
	var encoder zapcore.Encoder
	{
		var config zapcore.EncoderConfig
		if debug {
			config = zap.NewDevelopmentEncoderConfig()
		} else {
			config = zap.NewProductionEncoderConfig()
		}

		config.EncodeName = nameEncoder(debug)
		config.EncodeTime = timeEncoder(debug)
		config.EncodeLevel = levelEncoder(debug)

		if debug {
			encoder = zapcore.NewConsoleEncoder(config)
		} else {
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

type color uint8

const (
	Black color = iota + 30
	Red
	Green
	Yellow
	Blue
	Magenta
	Cyan
	White
)

func (c color) Add(s string) string {
	if c == 0 {
		return s
	}
	return fmt.Sprintf("\x1b[%dm%s\x1b[0m", uint8(c), s)
}

func nameEncoder(debug bool) func(loggerName string, enc zapcore.PrimitiveArrayEncoder) {
	return func(loggerName string, enc zapcore.PrimitiveArrayEncoder) {
		var c color
		if debug {
			c = Green
		}

		enc.AppendString(c.Add(loggerName))
	}
}

func timeEncoder(debug bool) func(t time.Time, enc zapcore.PrimitiveArrayEncoder) {
	return func(t time.Time, enc zapcore.PrimitiveArrayEncoder) {
		if !debug {
			zapcore.EpochTimeEncoder(t, enc)
			return
		}

		const layout = "2006-01-02T15:04:05.000Z0700" // ISO8601TimeEncoder.
		formatted := t.Format(layout)
		var c color
		if debug {
			c = Yellow
		}
		enc.AppendString(c.Add(formatted))
	}
}

func levelEncoder(debug bool) func(l zapcore.Level, enc zapcore.PrimitiveArrayEncoder) {
	return func(l zapcore.Level, enc zapcore.PrimitiveArrayEncoder) {
		vl := math.Abs(float64(l))
		level := strconv.FormatFloat(vl, 'f', 0, 64)

		if !debug {
			enc.AppendString(level)
			return
		}

		var c color
		switch {
		case vl == 2:
			c = Red
		case vl >= 0:
			c = Cyan
		default:
			c = White
		}

		enc.AppendString(
			c.Add(fmt.Sprintf("V(%s)", level)),
		)
	}
}
