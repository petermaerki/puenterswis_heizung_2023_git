# Important commands for the maintenance of the rasperry pi

## Ssh

```bash
ssh zero@zero-virgin.local
```

## Available services

```bash
systemctl | grep heizung
  heizung-app.service
  heizung-ssh-tunnel_zero-virgin.service
```

### service status

```bash
systemctl status heizung-app.service
```

### service journal

```bash
journalctl --no-tail --follow --unit heizung-app.service
```

### service journal

## Change from `zero-virgin` to `zero-puent`

Run `625_zero-root_bootstrap.py`. See instructions on top of the file.
