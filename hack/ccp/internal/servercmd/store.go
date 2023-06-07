package servercmd

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strings"
	"time"

	sqlc "github.com/artefactual/archivematica/hack/ccp/sqlc/mysql"
	"github.com/go-logr/logr"
	mysqldriver "github.com/go-sql-driver/mysql"
)

type store interface {
	sqlc.Querier
	Close() error
}

type storeImpl struct {
	logger  logr.Logger
	pool    *sql.DB
	querier sqlc.Querier
}

var _ store = (*storeImpl)(nil)

func newStore(logger logr.Logger, pool *sql.DB, querier sqlc.Querier) *storeImpl {
	return &storeImpl{
		logger:  logger,
		pool:    pool,
		querier: querier,
	}
}

func (s *storeImpl) CleanUpActiveJobs(ctx context.Context) error {
	s.logger.V(2).Info("Running query.", "method", "CleanUpActiveJobs")
	return s.querier.CleanUpActiveJobs(ctx)
}

func (s *storeImpl) CleanUpActiveSIPs(ctx context.Context) error {
	s.logger.V(2).Info("Running query.", "method", "CleanUpActiveSIPs")
	return s.querier.CleanUpActiveSIPs(ctx)
}

func (s *storeImpl) CleanUpActiveTasks(ctx context.Context) error {
	s.logger.V(2).Info("Running query.", "method", "CleanUpActiveTasks")
	return s.querier.CleanUpActiveTasks(ctx)
}

func (s *storeImpl) CleanUpActiveTransfers(ctx context.Context) error {
	s.logger.V(2).Info("Running query.", "method", "CleanUpActiveTransfers")
	return s.querier.CleanUpActiveTransfers(ctx)
}

func (s *storeImpl) CleanUpAwaitingJobs(ctx context.Context) error {
	s.logger.V(2).Info("Running query.", "method", "CleanUpAwaitingJobs")
	return s.querier.CleanUpActiveJobs(ctx)
}

func (s *storeImpl) CreateJob(ctx context.Context, arg *sqlc.CreateJobParams) error {
	s.logger.V(2).Info("Running query.", "method", "CreateJob")
	return s.querier.CreateJob(ctx, arg)
}

func (s *storeImpl) CreateWorkflowUnitVariable(ctx context.Context, arg *sqlc.CreateWorkflowUnitVariableParams) error {
	s.logger.V(2).Info("Running query.", "method", "CreateWorkflowUnitVariable")
	return s.querier.CreateWorkflowUnitVariable(ctx, arg)
}

func (s *storeImpl) ReadWorkflowUnitVariable(ctx context.Context, arg *sqlc.ReadWorkflowUnitVariableParams) (sql.NullString, error) {
	s.logger.V(2).Info("Running query.", "method", "ReadWorkflowUnitVariable")
	return s.querier.ReadWorkflowUnitVariable(ctx, arg)
}

func (s *storeImpl) Close() error {
	var err error

	if s.pool != nil {
		err = errors.Join(err, s.pool.Close())
	}

	return err
}

func createStore(logger logr.Logger, driver, dsn string) (*storeImpl, error) {
	var store *storeImpl

	switch strings.ToLower(driver) {
	case "mysql":
		{
			logger = logger.WithName("mysql")

			pool, err := connectMySQL(dsn)
			if err != nil {
				return nil, err
			}

			var version string
			err = pool.QueryRow("SELECT VERSION()").Scan(&version)
			if err != nil {
				return nil, err
			}

			logger.V(2).Info("Connected to MySQL.", "version", version)

			var querier sqlc.Querier
			querier, err = sqlc.Prepare(context.Background(), pool)
			if err != nil {
				return nil, err
			}

			store = newStore(logger, pool, querier)
		}
	default:
		return nil, fmt.Errorf("unsupported db driver: %q", driver)
	}

	return store, nil
}

func connectMySQL(dsn string) (*sql.DB, error) {
	config, err := mysqldriver.ParseDSN(dsn)
	if err != nil {
		return nil, fmt.Errorf("error parsing dsn: %v (%s)", err, dsn)
	}
	config.Collation = "utf8mb4_unicode_ci"
	config.Loc = time.UTC
	config.ParseTime = true
	config.MultiStatements = true
	config.Params = map[string]string{
		"time_zone": "UTC",
	}

	conn, err := mysqldriver.NewConnector(config)
	if err != nil {
		return nil, fmt.Errorf("error creating connector: %w", err)
	}

	db := sql.OpenDB(conn)

	// Set reasonable sizes on the built-in pool.
	db.SetMaxOpenConns(30)
	db.SetMaxIdleConns(30)
	db.SetConnMaxLifetime(time.Minute)

	return db, nil
}
