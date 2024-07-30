# SSH Tunnel from Office into Heizung


## Sometimes the tunnel could not be enabled

### suspicion `remote port forwarding failed`

How to reproduce

Call below command twice on the Pi in two different terminals. The second will display the warning and hang.

```bash
ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 -nNT -R 8851:localhost:22 www-insecure@www.maerki.com
Warning: remote port forwarding failed for listen port 8851
```

However, this option `-o ExitOnForwardFailure=yes` will force ssh to exit. This is the wanted behaviour.

* Links
  * https://stackoverflow.com/questions/42357406/why-doesnt-ssh-exit-upon-remote-forward-failure
  * https://man.openbsd.org/ssh
