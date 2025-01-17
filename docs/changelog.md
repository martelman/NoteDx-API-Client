# Changelog

All notable changes to the NoteDx SDK will be documented in this file.

## [0.1.5] - 2025-01-17

### Added
- Self-service account creation via `NoteDxClient.create_account()`
- Automatic API key setup during account creation
- Support for combined authentication (email/password + API key)

### Changed
- Simplified authentication flow
- Improved error handling for authentication
- Updated documentation to reflect self-service account creation
- Removed beta access request requirement

### Fixed
- Authentication retry logic for expired tokens
- Token refresh handling during method changes
- API key validation in request headers

## [0.1.4] - 2025-01-14

### Added

#### Documentation style

Introduction of the `documentation_style` parameter to allow for more flexibility in the note generation process. You can now choose between `soap` and `problemBased` documentation styles. Which structures the note based on these 2 very popular formats. When left empty, the default documentation style of the template is used, which is a structures classical style.

#### Pharmacy support

Introduction of the `pharmacy` template! This is a perfectly tailored template for pharmacists to generate notes for their patients after a consultation. It was codeveloped with pharmacists.


- Updated documentation
- Updated README


## [0.1.3] - 2025-01-13

### Added
- Bug fix for the `NoteManager` class


## [0.1.2] - 2025-01-11

### Added
- Initial release
