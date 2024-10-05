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

## Simplified access. Works if ports 8851-8853 are exposed on www.maerki.com

`ssh -p 8852 zero@www.maerki.com`

## Work with VSCode

In VSCode: `>Remote-SSH: Connect to Host` -> `zero-puent_maerki.com`

This now should connect VSCode.
