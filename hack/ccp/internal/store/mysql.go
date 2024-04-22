package store

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"time"

	"github.com/doug-martin/goqu/v9"
	"github.com/go-logr/logr"
	mysqldriver "github.com/go-sql-driver/mysql"
	"github.com/google/uuid"

	"github.com/artefactual/archivematica/hack/ccp/internal/store/enums"
	sqlc "github.com/artefactual/archivematica/hack/ccp/internal/store/sqlcmysql"
)

func connectToMySQL(logger logr.Logger, dsn string) (*sql.DB, error) {
	config, err := mysqldriver.ParseDSN(dsn)
	if err != nil {
		return nil, fmt.Errorf("error parsing dsn: %v (%s)", err, dsn)
	}
	config.Collation = "utf8mb4_unicode_ci"
	config.Loc = time.UTC
	config.ParseTime = true
	config.MultiStatements = true
	config.Params = map[string]string{
		"time_zone": "'+00:00'",
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

	var version string
	err = db.QueryRow("SELECT VERSION()").Scan(&version)
	if err != nil {
		return nil, err
	}

	logger.V(2).Info("Connected to MySQL.", "version", version)

	return db, nil
}

// mysqlstoreImpl implements the Store interface. While most queries are built
// using sqlc, there are some cases where more dynamism is required where we
// are using the goqu SQL builder, e.g. UpdateUnitStatus.
type mysqlStoreImpl struct {
	logger  logr.Logger
	pool    *sql.DB
	queries *sqlc.Queries
	goqu    *goqu.Database
}

var _ Store = (*mysqlStoreImpl)(nil)

func newMySQLStore(logger logr.Logger, pool *sql.DB) (*mysqlStoreImpl, error) {
	queries, err := sqlc.Prepare(context.Background(), pool)
	if err != nil {
		return nil, err
	}

	return &mysqlStoreImpl{
		logger:  logger,
		pool:    pool,
		queries: queries,
		goqu:    goqu.New("mysql", pool),
	}, nil
}

func (s *mysqlStoreImpl) RemoveTransientData(ctx context.Context) (err error) {
	defer wrap(&err, "RemoveTransientData")

	conn, _ := s.pool.Conn(ctx)
	defer conn.Close()

	q := sqlc.New(conn)

	// q.GetLock(ctx)
	// defer q.ReleaseLock(ctx)

	if err := q.CleanUpActiveTasks(ctx); err != nil {
		return err
	}

	if err := q.CleanUpActiveTransfers(ctx); err != nil {
		return err
	}

	if err := q.CleanUpTasksWithAwaitingJobs(ctx); err != nil {
		return err
	}

	if err := q.CleanUpAwaitingJobs(ctx); err != nil {
		return err
	}

	if err := q.CleanUpActiveSIPs(ctx); err != nil {
		return err
	}

	if err := q.CleanUpActiveJobs(ctx); err != nil {
		return err
	}

	return nil
}

func (s *mysqlStoreImpl) CreateJob(ctx context.Context, params *sqlc.CreateJobParams) (err error) {
	defer wrap(&err, "CreateJob")

	return s.queries.CreateJob(ctx, params)
}

func (s *mysqlStoreImpl) UpdateJobStatus(ctx context.Context, id uuid.UUID, status string) (err error) {
	defer wrap(&err, "UpdateJobStatus(%s, %s)", id, status)

	var step int32
	switch status {
	case "Unknown", "STATUS_UNKNOWN", "":
		step = 0
	case "Awaiting decision", "STATUS_AWAITING_DECISION":
		step = 1
	case "Completed successfully", "STATUS_COMPLETED_SUCCESSFULLY":
		step = 2
	case "Executing command(s)", "STATUS_EXECUTING_COMMANDS":
		step = 3
	case "Failed", "STATUS_FAILED":
		step = 4
	default:
		return fmt.Errorf("unknown status: %q", status)
	}

	return s.queries.UpdateJobStatus(ctx, &sqlc.UpdateJobStatusParams{
		ID:          id,
		Currentstep: step,
	})
}

func (s *mysqlStoreImpl) UpdatePackageStatus(ctx context.Context, id uuid.UUID, packageType enums.PackageType, status enums.PackageStatus) (err error) {
	defer wrap(&err, "UpdateUnitStatus(%s, %s, %s)", id, packageType, status)

	if !packageType.IsValid() {
		return fmt.Errorf("invalid type: %v", err)
	}
	if !status.IsValid() {
		return fmt.Errorf("invalid status: %v", err)
	}

	var (
		table     string
		idColumn  string
		statusVal int
	)

	switch packageType {
	case enums.PackageTypeTransfer:
		table = "Transfers"
		idColumn = "transferUUID"
	case enums.PackageTypeDIP, enums.PackageTypeSIP:
		table = "SIPs"
		idColumn = "sipUUID"
	default:
		return fmt.Errorf("unknown unit type: %q", packageType)
	}

	update := s.goqu.Update(table).
		Where(
			goqu.Ex{idColumn: id.String()},
		).
		Set(
			goqu.Record{"status": statusVal},
		).
		Executor()

	_, err = update.ExecContext(ctx)

	return err
}

func (s *mysqlStoreImpl) ReadTransferLocation(ctx context.Context, id uuid.UUID) (loc string, err error) {
	defer wrap(&err, "ReadTransferLocation(%s)", id)

	ret, err := s.queries.ReadTransferLocation(ctx, id)
	if err == sql.ErrNoRows {
		return "", ErrNotFound
	}
	if err != nil {
		return "", err
	}

	return ret.Currentlocation, nil
}

func (s *mysqlStoreImpl) UpsertTransfer(ctx context.Context, id uuid.UUID, path string) (_ bool, err error) {
	defer wrap(&err, "UpdateTransfer(%s, %s)", id, path)

	tx, err := s.pool.BeginTx(ctx, &sql.TxOptions{})
	if err != nil {
		return false, err
	}
	defer func() { _ = tx.Rollback() }()

	q := s.queries.WithTx(tx)

	r, err := q.ReadTransferLocation(ctx, id)

	// Return an error as we've failed to read the transfer.
	if err != nil && err != sql.ErrNoRows {
		return false, fmt.Errorf("read transfer: %v", err)
	}

	// Create the transfer as it has not been created yet.
	if err == sql.ErrNoRows {
		if err := q.CreateTransfer(ctx, &sqlc.CreateTransferParams{
			Transferuuid:    id,
			Currentlocation: path,
		}); err != nil {
			return false, fmt.Errorf("create transfer: %v", err)
		} else {
			return true, tx.Commit()
		}
	}

	// Update current location if needed.
	if r.Currentlocation == path {
		return false, nil
	}
	if err := q.UpdateTransferLocation(ctx, &sqlc.UpdateTransferLocationParams{
		Transferuuid:    id,
		Currentlocation: path,
	}); err != nil {
		return false, fmt.Errorf("update transfer: %v", err)
	}

	return false, tx.Commit()
}

func (s *mysqlStoreImpl) EnsureTransfer(ctx context.Context, path string) (_ uuid.UUID, _ bool, err error) {
	defer wrap(&err, "EnsureTransfer(%s)", path)

	tx, err := s.pool.BeginTx(ctx, &sql.TxOptions{})
	if err != nil {
		return uuid.Nil, false, err
	}
	defer func() { _ = tx.Rollback() }()

	q := s.queries.WithTx(tx)

	id, err := q.ReadTransferWithLocation(ctx, path)

	// Return an error as we've failed to read the transfer.
	if err != nil && err != sql.ErrNoRows {
		return uuid.Nil, false, fmt.Errorf("read transfer: %v", err)
	}

	commit := func(tx *sql.Tx) error {
		err := tx.Commit()
		if err != nil {
			return fmt.Errorf("commit: %v", nil)
		}

		return nil
	}

	// Create the transfer as it has not been created yet.
	if err == sql.ErrNoRows {
		id := uuid.New()
		if err := q.CreateTransfer(ctx, &sqlc.CreateTransferParams{
			Transferuuid:    id,
			Currentlocation: path,
		}); err != nil {
			return uuid.Nil, false, fmt.Errorf("create transfer: %v", err)
		} else {
			return id, true, commit(tx)
		}
	}

	return id, false, nil
}

func (s *mysqlStoreImpl) ReadUnitVars(ctx context.Context, id uuid.UUID, packageType enums.PackageType, name string) (vars []UnitVar, err error) {
	defer wrap(&err, "ReadUnitVars(%s, %s)", packageType, name)

	ret, err := s.queries.ReadUnitVars(ctx, &sqlc.ReadUnitVarsParams{
		UnitID: id,
		Name: sql.NullString{
			String: name,
			Valid:  true,
		},
	})
	if err == sql.ErrNoRows {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}

	for _, item := range ret {
		if packageType != "" && packageType.String() != item.Unittype.String {
			continue // Filter by package type if requested.
		}
		uv := UnitVar{}
		if item.Variablevalue.Valid {
			uv.Value = &item.Variablevalue.String
		}
		if item.LinkID.Valid {
			uv.LinkID = &item.LinkID.UUID
		}
		vars = append(vars, uv)
	}

	return vars, nil
}

func (s *mysqlStoreImpl) ReadUnitVar(ctx context.Context, id uuid.UUID, packageType enums.PackageType, name string) (_ string, err error) {
	defer wrap(&err, "ReadUnitVar(%s, %s, %s)", id, packageType, name)

	ret, err := s.queries.ReadUnitVar(ctx, &sqlc.ReadUnitVarParams{
		UnitID: id,
		UnitType: sql.NullString{
			String: packageType.String(),
			Valid:  true,
		},
		Name: sql.NullString{
			String: name,
			Valid:  true,
		},
	})
	if err == sql.ErrNoRows {
		return "", ErrNotFound
	}
	if err != nil {
		return "", err
	}

	return ret.Variablevalue.String, nil
}

func (s *mysqlStoreImpl) ReadUnitLinkID(ctx context.Context, id uuid.UUID, packageType enums.PackageType, name string) (_ uuid.UUID, err error) {
	defer wrap(&err, "ReadUnitVarLinkID(%s, %s, %s)", id, packageType, name)

	ret, err := s.queries.ReadUnitVar(ctx, &sqlc.ReadUnitVarParams{
		UnitID: id,
		UnitType: sql.NullString{
			String: packageType.String(),
			Valid:  true,
		},
		Name: sql.NullString{
			String: name,
			Valid:  true,
		},
	})
	if err == sql.ErrNoRows {
		return uuid.Nil, ErrNotFound
	}
	if err != nil {
		return uuid.Nil, err
	}

	return ret.LinkID.UUID, nil
}

func (s *mysqlStoreImpl) CreateUnitVar(ctx context.Context, id uuid.UUID, packageType enums.PackageType, name, value string, linkID uuid.UUID, updateExisting bool) (err error) {
	defer wrap(&err, "CreateUnitVar(%s, %s, %s, %s)", id, packageType, name, value)

	tx, err := s.pool.BeginTx(ctx, &sql.TxOptions{})
	if err != nil {
		return err
	}
	defer func() { _ = tx.Rollback() }()

	q := s.queries.WithTx(tx)

	exists := false
	uv, err := q.ReadUnitVar(ctx, &sqlc.ReadUnitVarParams{
		UnitID: id,
		UnitType: sql.NullString{
			String: packageType.String(),
			Valid:  true,
		},
		Name: sql.NullString{
			String: name,
			Valid:  true,
		},
	})
	switch {
	case err == sql.ErrNoRows:
	case err != nil:
		return err
	default:
		exists = true
	}

	var (
		wantValue  sql.NullString
		wantLinkID uuid.NullUUID
	)
	{
		switch {
		case value == "" && linkID == uuid.Nil:
			return errors.New("both value and linkID are zero")
		case value != "" && linkID != uuid.Nil:
			return errors.New("both value and linkID are non-zero")
		case value != "":
			// MCPServer sets "link_id" to NULL when a "value" is given, e.g.:
			// 	name="processingConfiguration", value="automated", link_id=NULL
			wantValue.String = value
			wantValue.Valid = true
			wantLinkID.Valid = false
		case linkID != uuid.Nil:
			// MCPServer sets "value" to empty string when a "link_id" is given, e.g.:
			//	name="reNormalize", value="", link_id="8ba83807-2832-4e41-843c-2e55ad10ea0b"/
			wantValue.Valid = true
			wantLinkID.UUID = linkID
			wantLinkID.Valid = true
		}
	}

	// It exists but it does not require further updates.
	if exists && wantValue == uv.Variablevalue && wantLinkID == uv.LinkID {
		return nil
	}

	// It exists and requires further updates but we rather raise an error.
	if !updateExisting {
		return errors.New("variable exists but with different propreties")
	}

	if exists {
		err := q.UpdateUnitVar(ctx, &sqlc.UpdateUnitVarParams{
			Value:  wantValue,
			LinkID: wantLinkID,
			// Where...
			UnitID:   id,
			UnitType: sql.NullString{String: packageType.String(), Valid: true},
			Name:     sql.NullString{String: name, Valid: true},
		})
		if err != nil {
			return fmt.Errorf("update: %v", err)
		} else {
			return tx.Commit()
		}
	} else {
		if err := s.queries.CreateUnitVar(ctx, &sqlc.CreateUnitVarParams{
			UnitID: id,
			UnitType: sql.NullString{
				String: packageType.String(),
				Valid:  true,
			},
			Name: sql.NullString{
				String: name,
				Valid:  true,
			},
			Value:  wantValue,
			LinkID: wantLinkID,
		}); err != nil {
			return fmt.Errorf("create: %v", err)
		} else {
			return tx.Commit()
		}
	}
}

func (s *mysqlStoreImpl) Running() bool {
	return s != nil
}

func (s *mysqlStoreImpl) Close() error {
	var err error

	if s.pool != nil {
		err = errors.Join(err, s.pool.Close())
	}

	if s.queries != nil {
		err = errors.Join(err, s.queries.Close())
	}

	return err
}

func wrap(errp *error, format string, args ...any) {
	if *errp == nil {
		return
	}
	var (
		errfmt  string
		message = fmt.Sprintf(format, args...)
	)
	if *errp == ErrNotFound {
		errfmt = "%s: %w"
	} else {
		errfmt = "%s: %v"
	}
	*errp = fmt.Errorf(errfmt, message, *errp)
}
