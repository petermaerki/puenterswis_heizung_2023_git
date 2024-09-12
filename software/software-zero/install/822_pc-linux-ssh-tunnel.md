# SSH Tunnel from Office into Heizung (Linux)

## Links

* https://www.sweetprocess.com/procedures/_AmM86Weq31FO0WDp5kRZFDBKRjB/ssh-tunnel-between-two-servers-behind-firewalls/
* https://toic.org/blog/2009/reverse-ssh-port-forwarding


## Remember

```python
DICT_SSH_TUNNEL_PORT = {
    "zero-virgin": 8851,
    "zero-bochs": 8852,
    "zero-puent": 8853,
}
```

## bochspi/puentpi

```bash
ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 -nNT -R 8852:localhost:22 www-insecure@www.maerki.com
```

## On PC

```bash
ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 -nNT -L 8851:localhost:8851 -L 8852:localhost:8852 -L 8853:localhost:8853 www-data@www.maerki.com
```

### Forward Flask HTTP port 8000

```bash
ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 zero@localhost -L 8000:127.0.0.1:8000 -p 8852
```


## Access Github from Zero

When developing on the zero, it is nice to be able to commit.

connect using `ssh -A`

Configure git

```bash
git config --global user.name "Hans Maerki"
git config --global user.email "buhtig.hans.maerki@ergoinfo.ch"
```
