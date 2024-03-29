
## bochspi/puentpi

```bash
ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 -nNT -R 8852:localhost:22 www-insecure@www.maerki.com
```

## On PC

```bash
ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 -nNT -L 8851:localhost:8851 -L 8852:localhost:8852 -L 8853:localhost:8853 www-insecure@www.maerki.com

ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 zero@localhost -p 8852
```

### Forward Flask HTTP port 8000

```bash
ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 zero@localhost -L 8000:127.0.0.1:8000 -p 8852
```