# SSH Tunnel from Office into Heizung (Windows)

## Access to www.maerki.com

Copy ssh-id to allow login without password:
```bash
ssh-copy-id www-data@www.maerki.com
```

Test without password:
```bash
ssh www-data@www.maerki.com
```
Important: A password is not required anymore!

## Prepare keys

Make sure your public and privat key is present:
```
C:\Users\maerki\.ssh\id_rsa.pub
C:\Users\maerki\.ssh\id_rsa.ppk
```

Make sure your public key is known to the zero:

`C:\Users\maerki\.ssh\id_rsa.pub`
must be one line in
`<repo>/keys/authorized_keys`

## Prepare `C:\Users\maerki\.ssh\config`

Copy lines from the template [822_pc-template-ssh-config.txt](822_pc-template-ssh-config.txt).

## Start ssh tunnels

Start a bash (git-bash or terminal-bash in VSCdoe) and type:
```bash
ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 -nNT -L 8851:localhost:8851 -L 8852:localhost:8852 -L 8853:localhost:8853 www-data@www.maerki.com
```
Important: The command *hangs* and does not produce any output.

## Work with VSCode

In VSCode: `>Remote-SSH: Connect to Host` -> `zero-puent_maerki.com`

This now should connect VSCode.
