# CAVEATS

This document lists known failure modes, root causes, and buffer-size considerations for the Arctan Audio Driver (latest code). Keep tests targeted and reproduce problems before shipping.

## Known Failure Scenarios (concise)

- Device Cannot Start (Code 10 / STATUS_DEVICE_BUSY)
  - Cause: `CAdapterCommon::m_AdapterInstances` left non-zero because the previously loaded driver instance wasn't fully unloaded.
  - Symptom: Device shows `Error` in Device Manager; `setupapi.dev.log` shows `CM_PROB_FAILED_START`.
  - Impact: Driver refuses new instance; install appears to succeed but device is unusable.
  - Mitigation: Reboot to fully unload kernel module. Installer should detect Code 10 and request reboot instead of forcing service stop.

- Partial/Failed Initialization
  - Cause: Miniport or topology filters fail during `StartDevice` (resource allocation, missing registry settings, failed initialization of ring buffers).
  - Symptom: Device appears but in `Error` state or endpoints missing.
  - Mitigation: Collect `setupapi.dev.log`, `driver_install.log`, and Event Viewer; fix init failure path in driver to clean up and decrement `m_AdapterInstances` on failure.

- Duplicate Device Nodes
  - Cause: Installer run twice without duplicate detection; earlier devcon or driver-store state not cleaned.
  - Symptom: Multiple `ROOT\MEDIA\00xx` instances; one or more in Error state.
  - Mitigation: Installer uses detection to run `devcon update` if an OK device exists. Ensure `InstallDriver.ps1` uses `@(...)` wrappers and checks status accurately.

- Broken or Missing devcon.exe
  - Cause: Shipping wrong devcon (corrupt/truncated) or relying on WDK being present.
  - Symptom: Installer fails to create device node; no devcon logs.
  - Mitigation: Bundle a known-good WDK `devcon.exe` with installer and verify its signature before use.

- pnputil Edge Cases
  - Cause: `pnputil /add-driver` returns 259 (already up-to-date) or 3010 (reboot required).
  - Symptom: Installer logs non-zero exit codes but may continue; behavior varies across Windows versions.
  - Mitigation: Treat 259 and 3010 as benign; set `RebootNeeded` for 3010 and request reboot.

- Signature & Attestation Problems
  - Cause: Missing EV token, expired cert, or truncated catalog.
  - Symptom: `signtool` failures, SmartScreen warnings, or Driver Store rejects package.
  - Mitigation: Verify `signtool verify` locally; ensure attested `.cat` is WHQL-signed and `ArctanAudioDriver.sys` shows Microsoft signing if attested by MS.

- Uninstall Race Conditions
  - Cause: Trying to stop/unload driver while audio apps hold handles.
  - Symptom: `devcon remove` may report devices remaining; uninstall incomplete until processes close or system reboot.
  - Mitigation: Uninstaller should close apps (Inno Setup `CloseApplications`) and request reboot when needed; do not forcibly `sc stop` kernel driver while in use.

- Sleep/Resume / Fast Startup
  - Cause: Driver not resilient to power callbacks or global state not reinitialized on resume.
  - Symptom: Device missing after resume, or audio glitches.
  - Mitigation: Test suspend/resume and reinitialize ring buffers on power events; prefer idempotent start/stop paths.

## Actual Buffer Sizes (Current Code)

All values derived directly from source constants. Do not treat these as tunable — they are hardcoded.

### Ring Buffers (`RING_BUFFER_DURATION_SECONDS = 2`)

Formula: `SampleRate × (BitsPerSample ÷ 8) × Channels × 2`

| Endpoint | Sample Rate | Bit Depth | Channels | Ring Buffer Size |
|----------|-------------|-----------|----------|-----------------|
| Speaker (×2) | 48,000 Hz | 16-bit | 2 (stereo) | **768,000 bytes** (~750 KB) each |
| Microphone (×2) | 48,000 Hz | 32-bit | 2 (stereo) | **1,536,000 bytes** (~1.5 MB) each |

Total nonpaged pool consumed by ring buffers at steady state: **~4.6 MB**  
(2 speaker + 2 mic ring buffers, plus partial-frame scratch buffers per stream)

### DMA Buffer

`DMA_BUFFER_SIZE = 0x16000` = **90,112 bytes** (~88 KB)

### Supported Formats (hardcoded — no runtime negotiation)

| Endpoint | Rate | Bit Depth | Channels | Mode |
|----------|------|-----------|----------|------|
| Speaker / Speaker 2 | 48,000 Hz only | 16-bit PCM | 2 (stereo) | Default |
| Mic / Mic 2 | 48,000 Hz only | 32-bit PCM | 2 (stereo) | Raw |

**No other sample rates or bit depths are supported.** Apps requesting 44.1 kHz, 96 kHz, 24-bit, or mono will be rejected by the driver's format validation.

### Stream Concurrency Limits

- `SPEAKER_MAX_INPUT_SYSTEM_STREAMS = 1` — only **one render stream** per speaker endpoint
- `MICARRAY_MAX_INPUT_STREAMS = 1` — only **one capture stream** per mic endpoint
- Total: 4 endpoints × 1 stream each = maximum **4 concurrent streams**

---

## Industry Comparison: Why 2 Seconds Is an Outlier

Production-grade virtual audio drivers use **far smaller** ring buffers. Arctan's 2-second buffer is inherited from the Microsoft sample code and is not representative of shipping audio products.

### What production drivers use

| Driver / Engine | Ring Buffer Duration | Buffer Size (48 kHz stereo 16-bit) | Strategy |
|-----------------|---------------------|-------------------------------------|----------|
| **VB-CABLE** (VB-Audio) | **~149 ms** (default 7168 samples) | ~28 KB | Configurable via control panel; DMA 4096 bytes |
| **Voicemeeter** (VB-Audio) | ~20–150 ms | Varies | Configurable 128–7168 samples |
| **ASIO4ALL** | ~12 ms (2× period, default 256 samples) | ~2 KB | Double-buffered, user-selectable 64–2048 |
| **RME ASIO** (pro hardware) | ~1.5–6 ms (32–256 samples) | <2 KB | Minimal, hardware-timed |
| **WASAPI Shared Mode** (Windows) | ~20–30 ms (2–3 × 10ms period) | ~8 KB | Audio engine manages buffering |
| **Arctan (current)** | **2,000 ms** | **768 KB** | Fixed, hardcoded |

**Key insight:** VB-CABLE defaults to ~150 ms (7168 samples @ 48 kHz) for maximum compatibility across diverse systems, but this is still **13× less** than Arctan's 2-second buffer. Pro/low-latency drivers (ASIO4ALL, RME) use much smaller buffers (2–12 ms). The ring buffer's job is to absorb scheduling jitter, not to store large amounts of audio.

### Why 2 seconds is problematic

1. **Latency ceiling on stall recovery.** The WASAPI engine period (typically 10 ms) determines steady-state latency, but the ring buffer determines **worst-case recovery time**. If the reader falls behind (DPC spike, CPU scheduling), up to 2 seconds of stale audio can accumulate. On resume, the listener hears a massive jump rather than a small click. A 20–40 ms buffer would cause at most a brief glitch.

2. **Excessive nonpaged pool usage.** 4.6 MB of kernel nonpaged pool for 4 streams. VB-CABLE achieves the same with ~16 KB total. On memory-constrained systems (VMs, embedded), this wastes scarce kernel resources.

3. **Bug masking.** A 2-second buffer hides real timing problems (slow DPCs, missed deadlines) that would surface immediately with a production-size buffer. Bugs ship silently and only appear under real workloads.

4. **Overrun delay.** On capture, if the reading app stalls, the ring buffer silently drops the oldest frames after 2 seconds. With a 40 ms buffer, the app gets immediate feedback that it's falling behind.

### Recommended change

Replace the fixed 2-second constant with a period-based calculation:

```c
// Before (current)
#define RING_BUFFER_DURATION_SECONDS 2

// After (recommended)
// Hold 4 engine periods worth of audio. At 10ms period / 48 kHz = 480 frames/period.
// 4 × 480 = 1920 frames × 4 bytes/frame = 7680 bytes (speaker)
// This matches production virtual audio drivers (VB-CABLE, Voicemeeter).
#define RING_BUFFER_NUM_PERIODS 4
#define RING_BUFFER_PERIOD_FRAMES 480  // 10ms at 48 kHz
// newBufferSize = RING_BUFFER_NUM_PERIODS * RING_BUFFER_PERIOD_FRAMES * frameSizeBytes
```

| With 4 periods | Speaker (16-bit stereo) | Mic (32-bit stereo) |
|----------------|-------------------------|---------------------|
| Buffer frames  | 1,920 | 1,920 |
| Buffer size    | 7,680 bytes (~7.5 KB) | 15,360 bytes (~15 KB) |
| Buffer duration | 40 ms | 40 ms |
| Total (4 streams) | ~45 KB | ~45 KB |

This reduces nonpaged pool from ~4.6 MB to ~45 KB (100× reduction) while still providing enough headroom for scheduling jitter.

**Action required:** This is a driver source change → requires rebuild, re-sign, and re-attestation. Do not change this in a hotfix unless you're prepared for a full submission cycle.

---

## Buffer Size — Practical Effects & Failure Scenarios

### Latency (fixed by format, 48 kHz)

Actual perceived latency is determined by the WASAPI engine period, not the ring buffer size. The ring buffer only affects **worst-case recovery** after a stall.

| Render period | Steady-state latency | Worst-case stall recovery (current 2s buffer) | Worst-case (recommended 40ms buffer) |
|---------------|---------------------|-----------------------------------------------|--------------------------------------|
| 128 frames | ≈ 2.67 ms | 2,000 ms | 40 ms |
| 256 frames | ≈ 5.33 ms | 2,000 ms | 40 ms |
| 480 frames | ≈ 10 ms | 2,000 ms | 40 ms |
| 1024 frames | ≈ 21.3 ms | 2,000 ms | 40 ms |

### Underruns (render)
- Occur when the audio engine doesn't fill the ring buffer before the driver reads past the write pointer.
- With `m_WriteFrameId + 1 == m_NumFrames` the driver auto-advances `m_ReadFrameId` (drops oldest frame) — this produces an audible glitch, not a crash.
- With a 2-second buffer, underruns are nearly invisible during testing but **will** happen in the field under DPC pressure. A smaller buffer surfaces them early.
- Test with LatencyMon or DPCLat while streaming.

### Overruns (capture)
- The ring buffer overwrites oldest frames when full.
- With 2-second buffer: overrun only when app stalls >2 seconds — hides real problems.
- With 40 ms buffer: overrun surfaces quickly, giving immediate signal that the app is falling behind.

### Nonpaged Pool Exhaustion
- If the system is under memory pressure and `ExAllocatePool2` for ring buffers returns `NULL`, `InitializeInput` / `InitializeOutput` fail silently (return `FALSE`) — the stream starts but produces silence or garbage, not a clean error.
- Current 4.6 MB allocation increases this risk. Recommended 45 KB allocation is negligible.

### Sample Rate / Format Mismatch
- The driver only accepts 48,000 Hz. If Windows audio engine or an app negotiates a different rate, `IsFormatSupported` returns `STATUS_NOT_SUPPORTED` and the endpoint may appear unavailable.
- This is the most common failure on systems where the default audio format has been manually changed to 44.1 kHz or 96 kHz in Sound Settings.
- **Test:** change system default format to 44.1 kHz 24-bit and verify endpoints remain usable.

### Single-Stream Limit
- A second app trying to open an exclusive stream on the same endpoint gets `AUDCLNT_E_DEVICE_IN_USE`.
- Shared-mode (normal) is fine — the audio engine multiplexes; the driver sees one stream from the engine.
- Exclusive mode with two simultaneous apps on the same endpoint will fail for the second app by design.

## Logging & Diagnostics (what to capture)

- `C:\ProgramData\ArctanAudioDriver\logs\driver_install.log` (installer actions)
- `C:\Windows\inf\setupapi.dev.log` (driver install details)
- Event Viewer → System and Application
- `Get-PnpDevice -Class Media | Format-List *` (device instances / status)
- Reproducer steps, sample rate, buffer size, and CPU load profile

## Shipping/Operational Caveats

- Do not attempt to force-stop the kernel driver while it is in use — it can crash the system.
- If installer sees Code 10, prefer requesting a reboot instead of forcibly unloading the driver.
- Always bundle a verified WDK `devcon.exe`; do not trust system PATH for devcon.
- Keep attested `.cat` and `.sys` matching — mismatched catalogs will lead to store rejects.

## Quick Mitigations for Field Support

- Ask user to reboot and retry install.
- If reboot not possible, collect logs and ask for `pnputil /enum-devices` and `driver_install.log`.
- If underruns reported: suggest increasing buffer size in client apps or system settings; provide guidance for default buffer values.

---

Keep `CAVEATS.md` with releases and update when driver behavior or architecture changes (e.g., additional streaming threads, multi-instance support, or different ring buffer implementation).