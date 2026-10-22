//! Dot Clock — native shell.
//!
//! The UI lives in `../src` (plain HTML/JS). This file only does what the
//! webview can't do on its own:
//!   * persist settings to a JSON file and broadcast changes to both windows
//!   * show/hide the settings window
//!   * quit / recentre the widget

use std::{fs, path::PathBuf, sync::Mutex};

use tauri::{AppHandle, Emitter, Manager, State, WindowEvent};
use tauri_plugin_window_state::{AppHandleExt, StateFlags};

struct Store {
    path: PathBuf,
    json: Mutex<String>,
}

/// Returns the saved settings JSON, or `"null"` on first run.
#[tauri::command]
fn load_state(store: State<'_, Store>) -> String {
    store.json.lock().unwrap().clone()
}

/// Validates, saves (atomically) and broadcasts the settings JSON to every window.
#[tauri::command]
fn save_state(app: AppHandle, store: State<'_, Store>, json: String) -> Result<(), String> {
    serde_json::from_str::<serde_json::Value>(&json).map_err(|e| e.to_string())?;
    let tmp = store.path.with_extension("json.tmp");
    fs::write(&tmp, &json).map_err(|e| e.to_string())?;
    fs::rename(&tmp, &store.path).map_err(|e| e.to_string())?;
    *store.json.lock().unwrap() = json.clone();
    app.emit("state-changed", json).map_err(|e| e.to_string())
}

/// Shows the settings window, optionally jumping to a section (e.g. "map").
#[tauri::command]
fn open_settings(app: AppHandle, section: Option<String>) -> Result<(), String> {
    let win = app
        .get_webview_window("settings")
        .ok_or("settings window missing")?;
    win.show().map_err(|e| e.to_string())?;
    let _ = win.unminimize();
    let _ = win.set_focus();
    if let Some(section) = section {
        app.emit_to("settings", "open-section", section)
            .map_err(|e| e.to_string())?;
    }
    Ok(())
}

/// Moves the widget back to the middle of the screen (rescue if it's lost off-screen).
#[tauri::command]
fn recenter_widget(app: AppHandle) -> Result<(), String> {
    let win = app.get_webview_window("main").ok_or("main window missing")?;
    win.center().map_err(|e| e.to_string())?;
    win.show().map_err(|e| e.to_string())?;
    win.set_focus().map_err(|e| e.to_string())
}

#[tauri::command]
fn quit(app: AppHandle) {
    let _ = app.save_window_state(StateFlags::POSITION);
    app.exit(0);
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // Launching the app again just brings the existing widget forward
        // (must be the first plugin registered).
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(w) = app.get_webview_window("main") {
                let _ = w.show();
                let _ = w.set_focus();
            }
        }))
        .plugin(
            // Remember where the user left the widget.
            tauri_plugin_window_state::Builder::default()
                .with_state_flags(StateFlags::POSITION)
                .with_denylist(&["settings"])
                .build(),
        )
        .setup(|app| {
            let dir = app.path().app_config_dir()?;
            fs::create_dir_all(&dir)?;
            let path = dir.join("state.json");
            let json = fs::read_to_string(&path)
                .ok()
                .filter(|s| serde_json::from_str::<serde_json::Value>(s).is_ok())
                .unwrap_or_else(|| "null".to_string());
            app.manage(Store {
                path,
                json: Mutex::new(json),
            });
            // The widget starts hidden so it doesn't flash in the centre before the
            // window-state plugin moves it back to where the user left it.
            if let Some(w) = app.get_webview_window("main") {
                let _ = w.show();
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                match window.label() {
                    // Closing settings just hides it so it opens instantly next time.
                    "settings" => {
                        api.prevent_close();
                        let _ = window.hide();
                    }
                    // Closing the widget quits the app.
                    "main" => {
                        let app = window.app_handle();
                        let _ = app.save_window_state(StateFlags::POSITION);
                        app.exit(0);
                    }
                    _ => {}
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            load_state,
            save_state,
            open_settings,
            recenter_widget,
            quit
        ])
        .run(tauri::generate_context!())
        .expect("error while running Dot Clock");
}
