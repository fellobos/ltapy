# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2018-02-14
### Added
- Add API for interacting with apodization files.
- Add logging to LightTools API function calls.
- Generate initial project documentation and publish it at
  [fellobos.github.io](https://fellobos.github.io/ltapy).
- Add README file.

### Changed
- Define public API interface to hide implementation details.
- Remove JumpStart macro function library from Session class. The
  JumpStart library is now accessible from the jslib module.
- Rename package from lighttools to ltapy to make it clearer that this
  is a 'Python' interface to the LightTools API.
- The lt attribute of the Session class holds now the reference to the
  LTAPI object.

### Fixed
- Fix bug in ArgSpec of DbKeyDump API method.

## [0.1.0] - 2016-11-09
First release.
