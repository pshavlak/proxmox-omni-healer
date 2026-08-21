# Architecture

## Current Flow

```text
Client
  -> hist.yupiterpro.ru:8443 (Hysteria 2, UDP)
  -> main server 62.113.105.38
  -> ACL
     -> Russian/private destinations: direct
     -> Other destinations: SOCKS5 cascade 193.164.155.153:18443
  -> Xray SOCKS on cascade
  -> WireProxy 127.0.0.1:40000
  -> Cloudflare WARP
  -> Internet
```

## Ports

- `443/tcp` on main server: nginx website and hidden manager proxy.
- `8443/udp` on main server: Hysteria server.
- `8081/tcp` on main server localhost: Flask manager and Hysteria HTTP auth.
- `18443/tcp` on cascade: SOCKS5 endpoint exposed by Xray process.
- `443/tcp` on cascade: Xray/VLESS/REALITY endpoint.
- `40000/tcp` on cascade localhost: WireProxy SOCKS endpoint.

## Public Web Surface

- `https://hist.yupiterpro.ru` is a decoy/static placeholder used to hide the VPN service.
- `https://hist.yupiterpro.ru/44169d2dba4d0fd5/` is the hidden admin panel path proxied by nginx to Flask manager on `127.0.0.1:8081`.

## Important Port Note

Older docs and generated configs referenced `hist.yupiterpro.ru:443` for Hysteria clients. Live verification on 2026-08-11 showed that Hysteria client works on `8443`, while `443` times out for Hysteria. New generated configs should use `8443`.
