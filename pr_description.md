## Summary

This PR adds comprehensive **dual-mode execution** support to BrowserSkill Pro, enabling seamless transition between the new `bsk invoke` passthrough command (bsk 0.2.0+) and legacy direct-command mode (bsk 0.1.x).

## Key Changes

### 🔄 Dual-Mode Auto-Detection
- **`invoke.sh`**: Runtime detection of `bsk invoke` availability with automatic fallback
- **`invoke.ps1`**: PowerShell equivalent with identical dual-mode logic
- **Zero-config**: No configuration needed - automatically selects best available mode

### 📚 Comprehensive Documentation
- **SKILL.md**: Added 8-section "Dual-mode execution" guide:
  - Mode comparison table (11 dimensions)
  - Auto-detection workflow (ASCII flowchart)
  - When each mode is used (examples + limitations)
  - Advanced forcing methods
  - Upgrade guide for agent developers

### 🔧 Upstream Sync from BrowserSkill
- **operations.md**: Restructured installation flow, added dev environment setup
- **Version pinning**: pnpm 10.17.0, Rust 1.85+/edition 2024, CLI 0.1.7, Extension 0.1.3
- **README.md**: Added extension build instructions link
- Updated examples and protocol references

### ✨ Features
- **Passthrough mode** (preferred): Complex nested args, Unicode, large payloads, production-ready
- **Legacy mode** (fallback): Simple flat args, older bsk versions, full backward compatibility
- **Cross-platform Python helper**: Windows (`py -3`), macOS/Linux (`python3`)
- **Session safety**: `--force` guard preserved on session-stopping actions

## Testing

- ✅ All 21 unit tests pass
- ✅ Bash syntax check passes on invoke.sh
- ✅ PowerShell syntax validation passes on invoke.ps1
- ✅ Legacy mode dry-run verified correct output
- ✅ Session stop force guard working correctly

## Migration Notes

No breaking changes - fully backward compatible with existing workflows.
New installations benefit immediately; existing setups upgrade seamlessly.

---

**Related**: Upstream BrowserSkill `bsk invoke` implementation on `chain` branch
