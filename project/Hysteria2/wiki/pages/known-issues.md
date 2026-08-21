# Known Issues

## Hysteria Port Confusion

README and generated configs historically referenced Hysteria on `443`, while production config listens on `8443`.

Status 2026-08-11:

- `hist.yupiterpro.ru:8443` works for Hysteria client.
- `hist.yupiterpro.ru:443` serves nginx HTTPS and times out as a Hysteria endpoint.
- Manager and CLI generator were updated to emit `8443`.

## Cascade SSH Intermittence

SSH to `193.164.155.153` sometimes timed out during banner exchange, then succeeded later with both available keys.

Observed 2026-08-11:

- First attempts to port 22 timed out.
- Later SSH succeeded and showed cascade services/ports.

## Xray Unit State

On cascade server, `systemctl is-active xray` reported `inactive`, but `xray-linux-amd6` processes were listening on `:443` and `:18443`.

This may mean Xray is managed by `x-ui` rather than a plain `xray` unit.

## WireProxy Memory Leak

README records a WireProxy v1.0.9 memory leak and daily restart workaround at 04:00. Keep an eye on RSS and OOM signs when checking cascade health.

## x-ui Fork Confusion

The cascade server panel command is `x-ui`, and the installed panel tracks `alireza0/x-ui`, not the `MHSanaei/3x-ui` v3.x release line.

On 2026-08-11, an attempted `MHSanaei/3x-ui v3.6.0` install was stopped after it removed `/usr/local/x-ui`; service was restored from `/root/backup-3xui-20260811-125329.tar.gz`, preserving `/etc/x-ui/x-ui.db`. Then the panel was safely updated within the existing fork to `alireza0/x-ui v1.11.4`.
