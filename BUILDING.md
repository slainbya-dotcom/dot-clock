# Building Dot Clock

The `.msi` has to be built on Windows and the `.dmg` on macOS. You can build them either way:

## build locally

### Windows (makes the .msi)

1. Install the tools once, from Terminal:

   ```powershell
   winget install OpenJS.NodeJS.LTS
   winget install Rustlang.Rustup
   winget install Microsoft.VisualStudio.2022.BuildTools --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
   ```

2. Close Terminal and open a new one, so the new tools are recognised.
3. Open a terminal in the project folder. In File Explorer, type `powershell` in the address bar of the folder that contains `package.json`.
4. Run:

   ```powershell
   npm install
   npm run build:win
   ```

5. The installer is written to `src-tauri\target\release\bundle\msi\Dot Clock_1.1.0_x64_en-US.msi`.

If you see "running scripts is disabled on this system", run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then try again.

### macOS (makes a universal .dmg)
 
1. Install the tools once, from Terminal. Skip any you already have.
 
   Xcode command line tools:
   ```
   xcode-select --install
   ```

   Rust. If you previously installed Rust through Homebrew, remove it first, because its older Cargo can't build this project and it conflicts with rustup:
   ```
   brew uninstall rust
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```
   Choose the standard installation, then load Rust into your current shell (or just open a new Terminal window):
   ```
   . "$HOME/.cargo/env"
   ```
 
   Node.js (with [Homebrew](https://brew.sh)):
   ```
   brew install node
   ```
   Or download the LTS installer from https://nodejs.org and open a new Terminal window afterwards.
 
   Check everything is in place. Each command should print a version, and `cargo` should be 1.85 or newer:
   ```
   node -v
   npm -v
   cargo --version
   rustup --version
   ```
 
2. Open Terminal in the project folder, the one that contains `package.json`. Type `cd ` (with a trailing space), drag the folder from Finder into the Terminal window and press Enter. For example:
   ```
   cd /Users/yourname/Downloads/dot-[widghetname]-main
   ```
 
3. Add the two Mac build targets and install the dependencies:
   ```
   rustup target add aarch64-apple-darwin x86_64-apple-darwin
   npm install
   ```
 
4. Build. The first run compiles a lot of Rust and can take several minutes:
   ```
   CI=true npm run build:mac
   ```
   `CI=true` skips the step where the DMG script uses AppleScript to arrange the window in Finder. That step can hang or fail depending on Automation permissions. The only effect is that the DMG window has no custom icon layout.
 
5. Open the output folder:
   ```
   open src-tauri/target/universal-apple-darwin/release/bundle/dmg/
   ```
   The installer is `Dot WIDGETNAME_X.X.X_universal.dmg`. If you only see `bundle_dmg.sh` and `icon.icns`, the build didn't finish; see Troubleshooting below.
 
### Troubleshooting (macOS)
 
- **`rustup: command not found`**: run `. "$HOME/.cargo/env"` or open a new Terminal window.
- **`npm: command not found`**: Node.js isn't installed; see step 1.
- **`feature edition2024 is required` / Cargo 1.84**: an old Homebrew Rust is being used instead of rustup's. Run `brew uninstall rust`, open a new Terminal window and check that `cargo --version` is 1.85 or newer.
- **No `.dmg` in the folder, and a "Dot WIDGET" disk is mounted**: a previous build was interrupted. Eject it with `hdiutil detach "/Volumes/Dot WIDGET"` (add `-force` if it's busy), then rebuild with `CI=true npm run build:mac`.

For development, `npm run dev` runs the app with live reload. `npm test` runs the logic tests in Node.

## Project layout

```
src/                 UI (no build step)
  index.html         the widget window
  settings.html      the settings window
  js/time.js         offsets, DST, abbreviations, 12/24h formatting
  js/solar.js        sun altitude → day/night
  js/geo.js          offline city search, nearest city/zone, geolocation
  js/dotmatrix.js    5×7 font, icons, canvas renderer
  js/store.js        settings model + bridge to the native shell
  js/data.js         generated city list (603 cities, every tz zone)
src-tauri/           native shell (Rust), config, icons, capabilities
tools/               data/icon generators, preview builder
tests/               Node tests for the pure logic
```

To regenerate the city list after editing `tools/cities_curated.txt`, run `python3 tools/build_data.py`. It needs a system tzdata at `/usr/share/zoneinfo` (Linux or macOS).
