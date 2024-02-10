
## bochspi/puentpi

```
ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 -nNT -R 8822:localhost:22 www-data@www.maerki.com
```

## On PC

```
ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 -nNT -L 8822:localhost:8822 www-data@www.maerki.com

ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 zero@localhost -p 8822
```