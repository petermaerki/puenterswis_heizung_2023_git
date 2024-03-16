
## bochspi/puentpi

```
ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 -nNT -R 8852:localhost:22 www-data@www.maerki.com
```

## On PC

```
ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 -nNT -L 8851:localhost:8851 -L 8852:localhost:8852 -L 8853:localhost:8853 www-data@www.maerki.com

ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 zero@localhost -p 8852
```