# Important commands for the maintenance of the rasperry pi

## Peter Automation: Update software

windows:
```bash
ssh zero@zero-bochs.local '(cd puenterswis_heizung_2023_git; git pull; sudo systemctl restart heizung-app.service)'
```

## Ssh

pc-linux:
```bash
ssh zero@zero-virgin.local
```

zero:
```bash
ssh www-insecure@www.maerki.com
```


## Available services

zero:
```bash
systemctl | grep heizung
  heizung-app.service
  heizung-ssh-tunnel.service
```

### service status

zero:
```bash
systemctl status heizung-app.service
systemctl status heizung-ssh-tunnel.service
```

### service journal

zero:
```bash
journalctl --no-tail --follow --unit heizung-app.service
```

### service journal

## Change from `zero-virgin` to `zero-puent`

Run `625_zero-root_bootstrap.py`. See instructions on top of the file.
