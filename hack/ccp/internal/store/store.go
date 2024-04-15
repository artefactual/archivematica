package store

import (
	"context"
	"fmt"
	"strings"

	"github.com/go-logr/logr"
	"github.com/google/uuid"

	sqlc "github.com/artefactual/archivematica/hack/ccp/internal/store/sqlcmysql"
)

type Store interface {
	RemoveTransientData(context.Context) error
	CreateJob(context.Context, *sqlc.CreateJobParams) error
	UpdateJobStatus(context.Context, uuid.UUID, string) error

	Running() bool
	Close() error
}

func New(logger logr.Logger, driver, dsn string) (Store, error) {
	var store *mysqlStoreImpl

	switch strings.ToLower(driver) {
	case "mysql":
		{
			logger = logger.WithName("mysql")
			pool, err := connectToMySQL(logger, dsn)
			if err != nil {
				return nil, fmt.Errorf("connect to MySQL: %v", err)
			}
			store, err = newMySQLStore(logger, pool)
			if err != nil {
				return nil, fmt.Errorf("new MySQL store: %v", err)
			}
		}
	default:
		return nil, fmt.Errorf("unsupported db driver: %q", driver)
	}

	return store, nil
}
