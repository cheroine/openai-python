//! Very small stand‑in for the original marshal module.
//!
//! Only the handful of types and functions that the `denpk2` binary uses are
//! implemented.  Everything intentionally returns predictable, easily mocked
//! values instead of trying to interpret the Python bytecode format.

use crate::Result;
use std::fmt;

/// Minimal representation of a marshalled Python object.
#[derive(Debug, Clone, PartialEq)]
pub enum PyObject {
    Integer(i64),
    Float(f64),
    String(String),
    Bytes(Vec<u8>),
    Code(Box<CodeObject>),
    None,
}

impl PyObject {
    /// Convenience constructor used by the CLI.
    pub fn string<S: Into<String>>(value: S) -> Self {
        PyObject::String(value.into())
    }

    /// Returns a static description of the contained variant.
    pub fn kind(&self) -> &'static str {
        match self {
            PyObject::Integer(_) => "int",
            PyObject::Float(_) => "float",
            PyObject::String(_) => "str",
            PyObject::Bytes(_) => "bytes",
            PyObject::Code(_) => "code",
            PyObject::None => "none",
        }
    }
}

impl fmt::Display for PyObject {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            PyObject::Integer(value) => write!(f, "{value}"),
            PyObject::Float(value) => write!(f, "{value}"),
            PyObject::String(value) => write!(f, "{value}"),
            PyObject::Bytes(_) => write!(f, "<bytes>"),
            PyObject::Code(code) => write!(f, "<code {}>", code.name),
            PyObject::None => write!(f, "None"),
        }
    }
}

/// Cut‑down representation of a CPython code object.
#[derive(Debug, Clone, PartialEq)]
pub struct CodeObject {
    pub filename: String,
    pub name: String,
    pub arg_count: usize,
    pub constants: Vec<PyObject>,
    pub bytecode: Vec<u8>,
}

impl CodeObject {
    /// Creates a dummy object that still carries some provenance data.
    pub fn placeholder() -> Self {
        CodeObject {
            filename: "<unknown>".to_string(),
            name: "<module>".to_string(),
            arg_count: 0,
            constants: vec![],
            bytecode: vec![],
        }
    }
}

/// Returns a deterministic [`CodeObject`] built from opaque bytes.
pub fn load_code_object(data: &[u8]) -> Result<CodeObject> {
    let mut code = CodeObject::placeholder();
    if !data.is_empty() {
        code.bytecode = data.to_vec();
        code.name = format!("code_object_{}", data.len());
        code.filename = "<memory>".into();
    }
    Ok(code)
}

/// Converts a slice of bytes into a [`PyObject`].
pub fn loads(data: &[u8]) -> Result<PyObject> {
    Ok(PyObject::Bytes(data.to_vec()))
}

/// Serialises a [`PyObject`] into a Vec<u8> using a predictable strategy.
pub fn dumps(obj: &PyObject) -> Vec<u8> {
    match obj {
        PyObject::Integer(value) => value.to_le_bytes().to_vec(),
        PyObject::Float(value) => value.to_le_bytes().to_vec(),
        PyObject::String(value) => value.as_bytes().to_vec(),
        PyObject::Bytes(value) => value.clone(),
        PyObject::Code(code) => code.bytecode.clone(),
        PyObject::None => Vec::new(),
    }
}
