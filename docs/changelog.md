# Changelog

All notable changes to the NoteDx SDK will be documented in this file.

## [0.1.11] - 2025-06-06

### Added
- Improvement and bugfixes



## [0.1.10] - 2025-06-06

### Added
- `process_text` added as endpoint, where you can provide the transcripted text in order to generate a medical note.


## [0.1.9] - 2025-02-16

### Added
- `process_audio` accepts `webhook_env` parameter to specify the environment of the webhook. Either `prod` or `dev`, allowing the use of a live key in any environment.

### Changed
- Updated the documentation.

## [0.1.8] - 2025-02-13

### Added
- `process_audio` and `regenerate_note` methods accept a `custom_metadata` object for internal use and tracking.
- Added `interventionalRadiology` template.

### Changed
- Updated the documentation.


## [0.1.7] - 2025-02-10

### Changed
- Updated the documentation.
- Few bug fixes.

## [0.1.6] - 2025-02-07

### Changed
- Built a front end for the NoteDx admin methods. This will be the method to manage your NoteDx account.
- Removed the create_account method from the NoteDxClient class.

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
