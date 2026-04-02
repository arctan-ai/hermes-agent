# AGENTS.md

## Code Readability Principles

Write easy-to-consume code. Optimize for how quickly a reader can understand what the code does. Make code skimmable -- clear names, short functions, obvious flow. Avoid cleverness. Use early returns to reduce nesting and clarify preconditions. These principles apply to both Rust and TypeScript in this repo.

## Project Overview

Arctan (beatrice-client) is a real-time voice changer desktop app built with Tauri v2 (Rust backend + React/TypeScript frontend). The audio pipeline chains DeepFilterNet noise cancellation with a closed-source C/C++ Beatrice inference library (`beatrice.lib`) for neural voice conversion. **Windows-only** -- the native library is a pre-compiled MSVC static lib.

## Repository Structure

```
beatrice-client/             # Cargo workspace root (resolver 3, edition 2024)
├── beatrice_lib/            # Rust FFI wrapper around beatrice.lib
├── beatrice-client/         # Tauri application (package name: "arctan")
│   ├── src/                 # React frontend (Vite, Tailwind v4, Jotai, shadcn/ui)
│   ├── src-tauri/src/       # Tauri Rust backend (~21 modules)
│   └── package.json         # JS dependencies (yarn)
├── models/                  # Voice models + gender classifier ONNX model
├── dependencies/            # onnxruntime.dll
└── scripts/                 # Build/release scripts (PowerShell)
```

## Build / Dev / Test Commands

### Frontend (from `beatrice-client/` directory)
```sh
yarn install                   # Install JS dependencies
yarn dev                       # Vite dev server on localhost:1420
yarn build                     # tsc + Vite production build
npx tsc --noEmit               # Type check only (no build output)
```

### Tauri App (from `beatrice-client/` directory)
```sh
yarn tauri dev                 # Dev mode (hot-reload frontend + debug Rust backend)
yarn tauri build               # Production build -- use for audio testing (release Rust)
```
**Important:** Always use `yarn tauri build` for audio pipeline testing. Dev mode compiles Rust unoptimized and DeepFilterNet will miss real-time deadlines.

### Rust (from workspace root)
```sh
cargo check                    # Type check all crates
cargo build                    # Build all crates (Windows only -- needs beatrice.lib)
cargo clippy                   # Lint
cargo test                     # Run all tests
cargo test -p beatrice_lib     # Run tests for a single crate
cargo test test_name           # Run a single test by name
cargo test -- --ignored        # Run ignored tests (require model files on disk)
```

### CI
GitHub Actions (`build.yml`) on `windows-latest`, target `x86_64-pc-windows-msvc`. Triggers: PR to `main`, push on tags `v*`, `workflow_dispatch`.

## Audio Pipeline Architecture

```
Mic -> rb_in -> Worker thread -> rb_out -> Speaker
Worker: resample 48kHz -> DeepFilterNet -> speech gating -> gain -> Beatrice VC -> output gain
```
Ring buffers (~150ms at 48kHz), MMCSS "Pro Audio" scheduling, Event-based wake. Beatrice has three model versions (`beta_0`, `beta_1`, `rc_0`) dispatched via TOML metadata. WASAPI for input enumeration, default cpal host for output.

## Rust Code Style

### Imports
Three groups separated by blank lines: (1) `std`, (2) external crates, (3) `crate`-internal. Merge multi-item imports with curly braces. Use `as _` for trait imports used only for methods:
```rust
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait as _};
```
Wildcard imports (`*`) only for FFI bindings: `use crate::bindings::*`.

### Naming
- Functions, variables, modules: `snake_case`
- Types, structs, enums, traits: `PascalCase` prefixed with `Beatrice` in library crate (e.g., `BeatriceRC0`, `BeatriceResampler`)
- Tauri command functions: domain-prefixed (`cpal_get_inputs`, `beatrice_set_pitch`)
- Constants: `SCREAMING_SNAKE_CASE`

### Error Handling
- **Library crate**: `thiserror` enum (`BeatriceError`) with `#[from]` for auto-conversion. FFI error codes via `TryFrom<Beatrice_ErrorCode>`.
- **App crate**: `anyhow::Result` for internal logic; Tauri commands return `Result<T, String>` with `.map_err(|e| e.to_string())`.
- `unwrap()` acceptable on `Mutex::lock()`. `panic!` for invariant violations.

### Function Signatures
- Constructors named `new`, return concrete type. Factory functions return `Box<dyn Beatrice>`.
- Path args: `impl AsRef<Path>`. Multi-param functions: one param per line, trailing comma.
- Tauri commands: `pub async fn`, `#[tauri::command]`. Use `macro_rules!` for repetitive setter commands.

### Module Organization
- Flat structure, one concept per file. Private `mod` declarations in `lib.rs` with selective `pub use` re-exports.
- No `pub(crate)` -- use module privacy + re-exports instead.
- Version-specific implementations in separate files sharing a common trait.

### Global State
- Simple values: `pub static NAME: Mutex<T> = Mutex::new(default);`
- Atomic f32: `AtomicU32` with `atomic_store_f32` / `atomic_load_f32` helpers. `AtomicBool` for flags.
- Complex types: `pub static NAME: LazyLock<Mutex<Option<T>>> = LazyLock::new(|| Mutex::new(None));`
- Non-Send/Sync types: `UnsafeCell` wrapper with manual `unsafe impl Sync`.
- Lock access: `{ *NAME.lock().unwrap() }` in a block to limit scope.

### FFI
Raw pointers in private structs. `unsafe` blocks wrap only the FFI call. `Drop` impl for cleanup. Manual `unsafe impl Send` for pointer-containing types.

### Logging
Custom macros `log_info!`, `log_error!`, `log_warn!`, `log_debug!` defined in `logger.rs`. Use these instead of `log::info!` etc.

### Comments
- Library crate (`beatrice_lib`): inline `//` comments only, no rustdoc.
- App crate: `///` rustdoc and `//!` module docs. Japanese comments for domain-specific notes. English comments as section markers.

## TypeScript / React Code Style

### Imports
Use `@/` path alias for non-relative imports. Namespace imports for Tauri packages:
```ts
import * as tauriStore from "@tauri-apps/plugin-store";
```
Named imports for React, Jotai, and components.

### Naming
- Components: `PascalCase` (`SelectModel`, `VoiceSettings`)
- Component files: `PascalCase` (`SettingsDrawer.tsx`); cross-cutting files: `camelCase` (`rustInvoke.ts`, `jotaiAtoms.ts`)
- Variables, functions: `camelCase`
- Interfaces: `PascalCase` with `Info`/`Setting`/`Interface` suffixes
- Tauri command strings: `snake_case` matching Rust (`"cpal_get_inputs"`)
- Jotai atoms: `camelCase` in a single namespace object (`jotaiAtoms.outputSetting`)

### TypeScript Patterns
- Use `interface` for object shapes (not `type`). Nullable types: `T | null`.
- Inline prop types at function params (no separate prop interfaces).
- Strict mode enabled (`noUnusedLocals`, `noUnusedParameters`).
- Explicit generics on `invoke<T>()` and `atom<T>()`.

### React Patterns
- Components as `function` declarations (not arrow functions, not `React.FC`).
- Headless effect components returning `<></>` for side-effect logic (`SyncBeatrice`, `LoadTauriStore`, etc.).
- Jotai `useAtom` for global state. React Context for auth (`useAuth()`) and pipeline (`usePipeline()`).
- Functional updater for partial state: `setPrev((p) => ({ ...p, field: v }))`.
- Async in `useEffect`: wrap in `const promise = async () => { ... }; promise();`.
- Routing via `react-router-dom` v7 with `HashRouter`, `ProtectedRoute`, `PublicRoute`.

### Tauri IPC
All invoke calls centralized in `rustInvoke.ts`, organized into namespaces (`cpal`, `beatrice`, `audioDevices`, `sse`, `credentials`, `logger`, `micSignaling`, `tray`, `recording`, `appUpdate`). Interfaces for Rust data use `snake_case` field names matching serde serialization.

### Styling
Tailwind CSS v4 utility classes inline. `cn()` helper from `lib/utils.ts` for shadcn components. Dark theme with `neutral-*` palette, `indigo-300` accent.

### File Organization
- Flat root files for cross-cutting concerns (`jotaiAtoms.ts`, `rustInvoke.ts`, `tauriStore.ts`)
- `components/ui/` -- shadcn primitives (auto-generated, named exports)
- `components/<feature>/` -- feature components (multiple internal components per file, only top-level exported)
- `contexts/` -- React context providers (`AuthContext.tsx`, `PipelineContext.tsx`)
- `routes/` -- route config and guards
- No barrel files, types colocated with their modules
