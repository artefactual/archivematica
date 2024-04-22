package enums

// Models SIP and Transfer define a status property describing processing status
// with the following possible choices. It is possible that its value is left
// in an inconsistent state when processing ends abruptly. MCPServer marks all
// packages with unknown and processing status as failed at startup time in the
// lack of a better recovery mechanism.
//
// ENUM(
// Unknown,
// Processing,
// Done,
// CompletedSuccessfully,
// Failed
// ).
type PackageStatus int
