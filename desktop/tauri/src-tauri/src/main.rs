use once_cell::sync::Lazy;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::net::{SocketAddr, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::Duration;

const PROJECT_ROOT: &str = "/Users/dayin/Code/a-share-swing-system";
const BACKEND_URL: &str = "http://127.0.0.1:8000";
const BACKEND_HOST: &str = "127.0.0.1:8000";

static BACKEND_PROCESS: Lazy<Mutex<Option<Child>>> = Lazy::new(|| Mutex::new(None));

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            check_backend_status,
            start_backend,
            stop_backend,
            open_project_folder,
            open_logs_folder
        ])
        .setup(|app| {
            if !backend_is_running() {
                if let Err(err) = start_backend_process() {
                    log_desktop_warning(&format!("backend autostart warning: {err}"));
                }
                wait_for_backend(Duration::from_secs(10));
            }

            tauri::WebviewWindowBuilder::new(app, "main", tauri::WebviewUrl::External(BACKEND_URL.parse().unwrap()))
                .title("A 股 ETF 双周期模拟盘控制台")
                .inner_size(1440.0, 980.0)
                .min_inner_size(1100.0, 720.0)
                .build()?;
            Ok(())
        })
        .on_window_event(|_window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                if let Err(err) = stop_owned_backend() {
                    log_desktop_warning(&format!("backend shutdown warning: {err}"));
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running A-share ETF desktop shell");
}

#[tauri::command]
fn check_backend_status() -> bool {
    backend_is_running()
}

#[tauri::command]
fn start_backend() -> Result<String, String> {
    if backend_is_running() {
        return Ok("backend already running".to_string());
    }
    start_backend_process()?;
    if wait_for_backend(Duration::from_secs(12)) {
        Ok("backend started".to_string())
    } else {
        Err("backend process started but API port is not ready yet".to_string())
    }
}

#[tauri::command]
fn stop_backend() -> Result<String, String> {
    stop_owned_backend()?;
    Ok("owned backend stopped".to_string())
}

#[tauri::command]
fn open_project_folder() -> Result<(), String> {
    tauri_plugin_opener::open_path(PROJECT_ROOT, None::<&str>).map_err(|err| err.to_string())
}

#[tauri::command]
fn open_logs_folder() -> Result<(), String> {
    tauri_plugin_opener::open_path(format!("{PROJECT_ROOT}/logs"), None::<&str>).map_err(|err| err.to_string())
}

fn backend_is_running() -> bool {
    let addr: SocketAddr = match BACKEND_HOST.parse() {
        Ok(addr) => addr,
        Err(_) => return false,
    };
    TcpStream::connect_timeout(&addr, Duration::from_millis(450)).is_ok()
}

fn wait_for_backend(timeout: Duration) -> bool {
    let started = std::time::Instant::now();
    while started.elapsed() < timeout {
        if backend_is_running() {
            return true;
        }
        std::thread::sleep(Duration::from_millis(350));
    }
    false
}

fn start_backend_process() -> Result<(), String> {
    let mut guard = BACKEND_PROCESS.lock().map_err(|err| err.to_string())?;
    if guard.is_some() {
        return Ok(());
    }

    let project_root = PathBuf::from(PROJECT_ROOT);
    let python = project_root.join(".venv/bin/python");
    if !python.exists() {
        return Err(format!("python not found: {}", python.display()));
    }

    let log_dir = project_root.join("logs/desktop_app");
    fs::create_dir_all(&log_dir).map_err(|err| err.to_string())?;
    let stdout_path = log_dir.join("backend.out.log");
    let stderr_path = log_dir.join("backend.err.log");
    let stdout = open_append(&stdout_path)?;
    let stderr = open_append(&stderr_path)?;

    let child = Command::new(python)
        .current_dir(&project_root)
        .arg("-m")
        .arg("uvicorn")
        .arg("app.backend.main:app")
        .arg("--host")
        .arg("127.0.0.1")
        .arg("--port")
        .arg("8000")
        .env("REAL_TRADE_ENABLED", "0")
        .env("BROKER_API_ENABLED", "0")
        .stdout(Stdio::from(stdout))
        .stderr(Stdio::from(stderr))
        .spawn()
        .map_err(|err| err.to_string())?;

    *guard = Some(child);
    Ok(())
}

fn stop_owned_backend() -> Result<(), String> {
    let mut guard = BACKEND_PROCESS.lock().map_err(|err| err.to_string())?;
    if let Some(mut child) = guard.take() {
        child.kill().map_err(|err| err.to_string())?;
        let _ = child.wait();
    }
    Ok(())
}

fn open_append(path: &Path) -> Result<std::fs::File, String> {
    OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(|err| err.to_string())
}

fn log_desktop_warning(message: &str) {
    let path = PathBuf::from(PROJECT_ROOT).join("logs/desktop_app/desktop_warning.log");
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(path) {
        let _ = writeln!(file, "{message}");
    }
}
