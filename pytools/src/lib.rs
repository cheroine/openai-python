//! Minimal pytools crate used by the denpk2 example project.
//!
//! The original project expects a `pytools::marshal` module that knows how to
//! parse Python bytecode.  Re‑implementing the full parser is out of scope for
//! this repository, so we provide small, well‑documented stubs that are easy to
//! extend whenever the binary needs a richer feature set.

pub mod marshal;

use std::{error::Error, fmt};

/// Common error type returned by the crate.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PytoolsError {
    /// Raised whenever data cannot be interpreted by the tiny marshal module.
    MarshalError(String),
}

impl PytoolsError {
    pub fn marshal<T: Into<String>>(msg: T) -> Self {
        PytoolsError::MarshalError(msg.into())
    }
}

impl fmt::Display for PytoolsError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            PytoolsError::MarshalError(message) => write!(f, "marshal error: {message}"),
        }
    }
}

impl Error for PytoolsError {}

/// Convenience alias used throughout the crate.
pub type Result<T> = std::result::Result<T, PytoolsError>;
