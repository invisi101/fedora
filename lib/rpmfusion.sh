#!/usr/bin/env bash
# Enable RPM Fusion Free repository if not already present.
# Source this file; call enable_rpmfusion_free.

enable_rpmfusion_free() {
    if rpm -q rpmfusion-free-release &>/dev/null; then
        ok "RPM Fusion Free already enabled."
        return 0
    fi

    local ver
    ver=$(rpm -E %fedora)
    local url="https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-${ver}.noarch.rpm"

    info "Enabling RPM Fusion Free for Fedora ${ver}..."
    dnf install -y "$url" || err "Failed to enable RPM Fusion Free."
    ok "RPM Fusion Free enabled."
}
