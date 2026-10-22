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

### macOS (makes a universal Intel + Apple Silicon .dmg)

1. Run `xcode-select --install`, then install [Rust](https://rustup.rs) and [Node.js LTS](https://nodejs.org).
2. Run:

   ```bash
   rustup target add aarch64-apple-darwin x86_64-apple-darwin
   npm install
   npm run build:mac
   ```

3. The installer is written to `src-tauri/target/universal-apple-darwin/release/bundle/dmg/`.

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
