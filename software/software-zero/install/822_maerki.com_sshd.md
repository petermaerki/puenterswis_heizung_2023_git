# Gateway Ports for tunnel

The raspberry pi zeros create a tunnel which terminates port 8851,8852,8853 of www.maerki.com.

## reverse tunnel

A reverse tunnel as described in `./822_pc-linux-ssh-tunnel.md` works so far.

## GatewayPort

However, when the ports 8851,8852,8853 are exposed to the internet, one may connect using `ssh -p 8852 zero@www.maerki.com`.

### On www.maerki.com: GatewayPorts

In `/etc/ssh/sshd_config` set `GatewayPorts yes`.
Then `service sshd reload`,

### On www.maerki.com: Firewall

```
ufw allow 8851
ufw allow 8852
ufw allow 8853
```

This will update `/etc/ufs/user.rules`.
