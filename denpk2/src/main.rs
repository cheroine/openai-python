use std::{env, fs, path::PathBuf};

use pytools::{marshal, PytoolsError};
use pytools::marshal::PyObject;

fn main() -> Result<(), PytoolsError> {
    let args: Vec<String> = env::args().collect();

    if let Some(path) = args.get(1) {
        let path = PathBuf::from(path);
        let data = fs::read(&path).unwrap_or_default();
        let code = marshal::load_code_object(&data)?;
        println!(
            "Loaded code object '{}' from '{}' ({} bytes of bytecode)",
            code.name,
            path.display(),
            code.bytecode.len()
        );
    } else {
        let obj = PyObject::string("denpk2");
        let bytes = marshal::dumps(&obj);
        let roundtrip = marshal::loads(&bytes)?;
        println!(
            "Round‑tripped marshalled object with kind '{}' and size {} bytes",
            roundtrip.kind(),
            bytes.len()
        );
    }

    Ok(())
}
