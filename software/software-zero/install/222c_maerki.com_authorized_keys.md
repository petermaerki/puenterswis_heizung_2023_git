# Authorized keys

To allow the rasperry PIs to login to www-insecure, the public keys have to be copied.

## On pc-linux

```bash
cd <repo>
cat software/software-zero/keys/*/id_rsa.pub
```

## On maerki.com

Copy output of above command and terminate with `ctrl-d`.
```bash
cat >> ~www-insecure/.ssh/authorized_keys
```

Make sure the file permissions are as follows

```bash
chown www-insecure:www-insecure ~www-insecure/.ssh/authorized_keys
chmod u=rw,g=,o= ~www-insecure/.ssh/authorized_keys
```
